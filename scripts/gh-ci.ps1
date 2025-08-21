<#
CI helpers for GitHub Actions runs (Windows PowerShell 5.1 compatible)

Usage (from repo root):
  . .\scripts\gh-ci.ps1      # dot-source to load functions
  Show-NewestRunLogs -Workflow 'Python Tests'
  Open-NewestFailedRun -Workflow 'Python Tests'
  Open-NewestRun -Workflow 'Python Tests'
  Open-NewestRunForBranch -Workflow 'Python Tests' -Branch 'feat/etag-tighten-tests'
#>

function Show-NewestRunLogs {
  [CmdletBinding()]
  param(
    [string]$Workflow = 'Python Tests'
  )
  $items = gh run list --workflow $Workflow -L 50 --json databaseId,createdAt,status,conclusion | ConvertFrom-Json
  if (-not $items) { Write-Host 'No recent run found.'; return }
  $run = ($items | Sort-Object createdAt -Descending)[0]
  Write-Host ("Workflow: {0}  ID: {1}  Status: {2}  Conclusion: {3}  Created: {4}" -f `
    $Workflow, $run.databaseId, $run.status, $run.conclusion, $run.createdAt)
  gh run view $($run.databaseId) --log | `
    Select-String -Pattern "pip install|pytest|FAILED|ERROR|ResolutionImpossible|ModuleNotFoundError"
}

function Open-NewestFailedRun {
  [CmdletBinding()]
  param(
    [string]$Workflow = 'Python Tests'
  )
  $items = gh run list --workflow $Workflow -L 50 --json databaseId,conclusion,createdAt | ConvertFrom-Json
  if (-not $items) { Write-Host 'No failed runs in last 50'; return }
  $failed = $items | Where-Object conclusion -ne 'success' | Sort-Object createdAt -Descending | Select-Object -First 1
  if ($failed) { gh run view $failed.databaseId --web } else { Write-Host 'No failed runs in last 50' }
}

function Open-NewestRun {
  [CmdletBinding()]
  param(
    [string]$Workflow = 'Python Tests'
  )
  $items = gh run list --workflow $Workflow -L 50 --json databaseId,createdAt | ConvertFrom-Json
  if (-not $items) { Write-Host 'No recent runs'; return }
  $r = $items | Sort-Object createdAt -Descending | Select-Object -First 1
  if ($r) { gh run view $r.databaseId --web } else { Write-Host 'No recent runs' }
}

function Open-NewestRunForBranch {
  [CmdletBinding()]
  param(
    [string]$Workflow = 'Python Tests',
    [Parameter(Mandatory=$true)][string]$Branch
  )
  $items = gh run list --workflow $Workflow --branch $Branch -L 50 --json databaseId,createdAt | ConvertFrom-Json
  if (-not $items) { Write-Host "No recent runs for $Branch"; return }
  $r = $items | Sort-Object createdAt -Descending | Select-Object -First 1
  if ($r) { gh run view $r.databaseId --web } else { Write-Host "No recent runs for $Branch" }
}
