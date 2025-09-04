Param(
  [string]$JsonPath = "sa-key-attach.json",
  [string]$Repo = "Slybry2000/Sunchaserjuly27"
)

Write-Output "Running set_gcp_b64.ps1..."
if (-not (Test-Path $JsonPath)) {
  Write-Error "Service account JSON not found at path: $JsonPath"
  exit 1
}

try {
  $json = Get-Content -Raw -Encoding UTF8 $JsonPath
} catch {
  Write-Error "Failed to read JSON file: $_"
  exit 1
}

$b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))
Write-Output "Encoding complete (length $($b64.Length) chars). Setting secret..."

$ghArgs = @('secret','set','GCP_SA_KEY_B64','-b',$b64,'--repo',$Repo)
$proc = Start-Process gh -ArgumentList $ghArgs -NoNewWindow -Wait -PassThru
if ($proc.ExitCode -ne 0) {
  Write-Error "gh secret set failed with exit code $($proc.ExitCode)"
  exit $proc.ExitCode
}
Write-Output "GCP_SA_KEY_B64 set in repo $Repo"

# Create empty commit to retrigger workflow
git commit --allow-empty -m "ci: trigger deploy after setting GCP_SA_KEY_B64"
if ($LASTEXITCODE -ne 0) { Write-Output "No commit created (maybe no changes)" } else { Write-Output "Empty commit created" }

Write-Output "Pushing to origin/master..."
git push origin HEAD:master
if ($LASTEXITCODE -ne 0) { Write-Error "git push failed with exit code $LASTEXITCODE"; exit $LASTEXITCODE }

Write-Output "Done."
