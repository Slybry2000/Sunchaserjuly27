<#
run_with_timeout.ps1
Utility to run a command and enforce a timeout (Windows PowerShell).
Usage examples:
  .\tools\run_with_timeout.ps1 -Timeout 120 -Script "flutter test test/capture_screenshots_test.dart -r expanded"
  .\tools\run_with_timeout.ps1 -Timeout 10 -Script "Write-Output 'hi'; Start-Sleep -Seconds 2; Write-Output 'done'"

Exits with:
  0   - command finished before timeout
  124 - timed out (killed)
  2   - usage / bad args
  1   - command failed
#>
param(
    [int]
    $Timeout = 120,
    [string]
    $Script
)

if (-not $Script) {
    Write-Host "Usage: .\tools\run_with_timeout.ps1 -Timeout <seconds> -Script <command-string>"
    exit 2
}

Write-Host "Running with timeout ${Timeout}s: $Script"

# Start the command as a background job so we can Wait-Job with timeout.
$job = Start-Job -ScriptBlock { param($s) Invoke-Expression $s } -ArgumentList $Script

$finished = Wait-Job -Job $job -Timeout $Timeout
if (-not $finished) {
    Write-Host "Timeout ($Timeout s) reached. Attempting to stop job..."
    try {
        # Best-effort stop; Stop-Job may not kill native child processes, but stops the job host.
        Stop-Job -Job $job -Force -ErrorAction SilentlyContinue
        # Try to find any child processes with the same ProcessName as 'flutter' and stop them if found (best-effort)
        Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match 'flutter|dart|gradlew|adb' } | ForEach-Object { try { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {} }
    } catch {
        # ignore
    }
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    Write-Host "Command terminated due to timeout."
    exit 124
} else {
    # Output collected stdout/stderr
    Receive-Job -Job $job -ErrorAction SilentlyContinue | ForEach-Object { Write-Output $_ }
    $state = (Get-Job -Id $job.Id -ErrorAction SilentlyContinue).State
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    if ($state -eq 'Completed') { exit 0 } else { exit 1 }
}
