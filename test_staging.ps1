# Test staging deployment accessibility
# The staging URL pattern for Google Cloud Run is typically:
# https://SERVICE-PROJECT-REGION-HASH.a.run.app

$stagingUrls = @(
    "https://sun-chaser-staging-sun-chaser-081623-uw.a.run.app",
    "https://sun-chaser-staging-081623-uw.a.run.app", 
    "https://sun-chaser-staging-sun-chaser-uw.a.run.app"
)

Write-Host "Testing possible staging URLs..."

foreach ($url in $stagingUrls) {
    Write-Host "`nTesting: $url"
    try {
        $response = Invoke-WebRequest -Uri "$url/health" -TimeoutSec 10
        Write-Host "✅ SUCCESS: Status $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Response: $($response.Content)"
        
        # If health works, test the recommend endpoint
        try {
            $recResponse = Invoke-WebRequest -Uri "$url/recommend?lat=47.6&lon=-122.3&radius=25" -TimeoutSec 10
            Write-Host "✅ /recommend also works: Status $($recResponse.StatusCode)" -ForegroundColor Green
        } catch {
            Write-Host "⚠️  /recommend failed: $($_.Exception.Message)" -ForegroundColor Yellow
        }
        
        # Found working URL, save it
        $url | Out-File -FilePath "staging_url.txt" -Encoding UTF8
        Write-Host "✅ Saved working URL to staging_url.txt" -ForegroundColor Green
        break
        
    } catch {
        Write-Host "❌ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`nIf no URLs worked, the staging deployment may need to be triggered."
Write-Host "You can deploy to staging by pushing to the master branch."
