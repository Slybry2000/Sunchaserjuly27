Param()
$ErrorActionPreference = 'Stop'

$uvicornLog = $env:UVICORN_LOG; if (-not $uvicornLog) { $uvicornLog = 'uvicorn.log' }
$uvicornPidFile = $env:UVICORN_PID_FILE; if (-not $uvicornPidFile) { $uvicornPidFile = 'uvicorn.pid' }

Write-Host "Starting uvicorn, logs -> $uvicornLog"
$startInfo = @('-m','uvicorn','main:app','--host','127.0.0.1','--port','8001','--log-level','warning')
$outTmp = [System.IO.Path]::GetTempFileName()
$errTmp = [System.IO.Path]::GetTempFileName()
$proc = Start-Process -FilePath python -ArgumentList $startInfo -NoNewWindow -RedirectStandardOutput $outTmp -RedirectStandardError $errTmp -PassThru
$proc.Id | Out-File -FilePath $uvicornPidFile -Encoding ascii

# Combine temp files into the uvicorn log in the background
$job = Start-Job -ScriptBlock {
    param($outTmpPath, $errTmpPath, $finalLog)
    while ($true) {
        Get-Content $outTmpPath -ErrorAction SilentlyContinue | Out-File -FilePath $finalLog -Append -Encoding utf8
        Get-Content $errTmpPath -ErrorAction SilentlyContinue | Out-File -FilePath $finalLog -Append -Encoding utf8
        Start-Sleep -Milliseconds 200
    }
} -ArgumentList $outTmp, $errTmp, $uvicornLog

$started = $false
for ($i = 0; $i -lt 10; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8001/metrics' -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -eq 200) { $started = $true; break }
    } catch {
        # swallow and retry
    }
    Start-Sleep -Milliseconds 500
}

if (-not $started) {
    Write-Host "ERROR: metrics endpoint not reachable after wait; dumping $uvicornLog"
    Get-Content $uvicornLog -ErrorAction SilentlyContinue
    Write-Host "Killing uvicorn pid: $(Get-Content $uvicornPidFile)"
    try { Stop-Process -Id (Get-Content $uvicornPidFile) -ErrorAction SilentlyContinue } catch {}
    # Cleanup background job and temp files
    try { Stop-Job -Job $job -Force -ErrorAction SilentlyContinue } catch {}
    try { Remove-Job -Job $job -Force -ErrorAction SilentlyContinue } catch {}
    try { Remove-Item -Path $outTmp -ErrorAction SilentlyContinue } catch {}
    try { Remove-Item -Path $errTmp -ErrorAction SilentlyContinue } catch {}
    exit 1
}

Write-Host "metrics endpoint reachable; stopping uvicorn"
try { Stop-Process -Id (Get-Content $uvicornPidFile) -ErrorAction SilentlyContinue } catch {}
try { Stop-Job -Job $job -Force -ErrorAction SilentlyContinue } catch {}
try { Remove-Job -Job $job -Force -ErrorAction SilentlyContinue } catch {}
try { Remove-Item -Path $outTmp -ErrorAction SilentlyContinue } catch {}
try { Remove-Item -Path $errTmp -ErrorAction SilentlyContinue } catch {}
exit 0
