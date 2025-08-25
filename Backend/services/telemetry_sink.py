
import os
import json
import asyncio
import logging
from typing import Any, Dict, List, Optional
import httpx
import random
from Backend.services.metrics import incr

logger = logging.getLogger('sunshine_backend.telemetry.sink')


async def sink_event_jsonl(payload: Dict[str, Any]) -> None:
    """Append telemetry payload as a JSON-line to TELEMETRY_SINK_PATH when set.

    This uses asyncio.to_thread to avoid blocking the event loop during file I/O.
    """
    path = os.getenv('TELEMETRY_SINK_PATH', '').strip()
    if not path:
        return

    line = json.dumps(payload, ensure_ascii=False)

    def _write():
        try:
            # Ensure parent dir exists
            dirpath = os.path.dirname(path)
            if dirpath and not os.path.exists(dirpath):
                os.makedirs(dirpath, exist_ok=True)
            with open(path, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        except Exception:
            logger.exception('Failed to write telemetry to %s', path)

    await asyncio.to_thread(_write)


async def sink_event_forward_http(payload: Dict[str, Any]) -> None:
    """Optional forwarder: POST telemetry to TELEMETRY_SINK_URL if set.

    This is fire-and-forget and times out quickly to avoid blocking pipeline.
    """
    url = os.getenv('TELEMETRY_SINK_URL', '').strip()
    if not url:
        return

    # Retry/backoff configuration
    try:
        max_retries = int(os.getenv('TELEMETRY_FORWARD_RETRIES', '3'))
    except Exception:
        max_retries = 3
    try:
        base_delay = float(os.getenv('TELEMETRY_FORWARD_BASE_DELAY_SEC', '0.5'))
    except Exception:
        base_delay = 0.5
    try:
        max_delay = float(os.getenv('TELEMETRY_FORWARD_MAX_DELAY_SEC', '5.0'))
    except Exception:
        max_delay = 5.0

    attempt = 0
    while attempt < max_retries:
        attempt += 1
        incr('telemetry_forward_attempts')
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(url, json=payload)
            incr('telemetry_forward_success')
            return
        except Exception:
            incr('telemetry_forward_failures')
            logger.warning('Telemetry forward attempt %d/%d failed to %s', attempt, max_retries, url)
            logger.info('payload=%s', payload)
            if attempt >= max_retries:
                incr('telemetry_forward_final_failures')
                logger.exception('Failed to forward telemetry to %s after %d attempts', url, attempt)
                return
            # exponential backoff with jitter
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = random.uniform(0, base_delay)
            await asyncio.sleep(delay + jitter)


# --- Batching support -------------------------------------------------
# A simple in-process batcher: collects events into an asyncio.Queue and
# flushes periodically or when the batch size threshold is reached.


class TelemetryBatcher:
    def __init__(self, *, batch_size: int = 25, interval_sec: float = 2.0):
        self.queue: asyncio.Queue = asyncio.Queue()
        self.batch_size = max(1, int(batch_size))
        self.interval_sec = float(interval_sec)
        self._task: Optional[asyncio.Task] = None
        self._stopping = False

    async def start(self) -> None:
        if self._task is None:
            self._stopping = False
            self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        self._stopping = True
        # wakeup worker
        if self._task:
            # put a sentinel to unblock wait_for
            try:
                self.queue.put_nowait(None)
            except Exception:
                pass
            await self._task
            self._task = None

    async def enqueue(self, payload: Dict[str, Any]) -> None:
        await self.queue.put(payload)

    async def _worker(self) -> None:
        while not self._stopping:
            items: List[Dict[str, Any]] = []
            try:
                # wait for the first item with timeout
                first = await asyncio.wait_for(self.queue.get(), timeout=self.interval_sec)
                # sentinel used to wake up on stop
                if first is None:
                    break
                items.append(first)
            except asyncio.TimeoutError:
                # timeout without items -> continue loop
                pass

            # drain up to batch_size-1 additional items
            while len(items) < self.batch_size:
                try:
                    item = self.queue.get_nowait()
                    if item is None:
                        break
                    items.append(item)
                except asyncio.QueueEmpty:
                    break

            if items:
                await self._flush(items)

        # flush remaining items after stop requested
        leftover: List[Dict[str, Any]] = []
        while True:
            try:
                item = self.queue.get_nowait()
                if item is None:
                    continue
                leftover.append(item)
            except asyncio.QueueEmpty:
                break
        if leftover:
            await self._flush(leftover)

    async def _flush(self, items: List[Dict[str, Any]]) -> None:
        # Write JSONL for each item in a thread to avoid blocking
        path = os.getenv('TELEMETRY_SINK_PATH', '').strip()
        if path:
            lines = [json.dumps(p, ensure_ascii=False) + '\n' for p in items]

            def _write_lines():
                try:
                    dirpath = os.path.dirname(path)
                    if dirpath and not os.path.exists(dirpath):
                        os.makedirs(dirpath, exist_ok=True)
                    with open(path, 'a', encoding='utf-8') as f:
                        f.writelines(lines)
                except Exception:
                    logger.exception('Failed to write telemetry batch to %s', path)

            await asyncio.to_thread(_write_lines)

        # Forward each event asynchronously (do not await here to avoid blocking)
        for payload in items:
            try:
                asyncio.create_task(sink_event_forward_http(payload))
            except Exception:
                logger.exception('Failed to schedule forward for telemetry payload')


# Global batcher instance managed by start/stop helpers
_BATCHER: Optional[TelemetryBatcher] = None


async def start_telemetry_batcher() -> None:
    global _BATCHER
    if _BATCHER is not None:
        return
    try:
        batch_size = int(os.getenv('TELEMETRY_BATCH_SIZE', '25'))
    except Exception:
        batch_size = 25
    try:
        interval = float(os.getenv('TELEMETRY_BATCH_INTERVAL_SEC', '2.0'))
    except Exception:
        interval = 2.0
    _BATCHER = TelemetryBatcher(batch_size=batch_size, interval_sec=interval)
    await _BATCHER.start()


async def stop_telemetry_batcher() -> None:
    global _BATCHER
    if _BATCHER is None:
        return
    await _BATCHER.stop()
    _BATCHER = None


async def enqueue_event(payload: Dict[str, Any]) -> None:
    """Enqueue an event for batching if the batcher is running; otherwise write immediately."""
    if _BATCHER is not None:
        await _BATCHER.enqueue(payload)
        return

    # fallback: write immediately
    await sink_event_jsonl(payload)
    # schedule forwarder without awaiting
    try:
        asyncio.create_task(sink_event_forward_http(payload))
    except Exception:
        logger.exception('Failed to schedule forward for telemetry payload')

