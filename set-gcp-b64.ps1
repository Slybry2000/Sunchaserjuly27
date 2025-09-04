$json = Get-Content -Raw -Encoding UTF8 .\sa-key-new.json
$bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
$b64 = [Convert]::ToBase64String($bytes)
gh secret set GCP_SA_KEY_B64 --body $b64
Remove-Item .\sa-key-new.json -Force
Write-Output "GCP_SA_KEY_B64 set."
