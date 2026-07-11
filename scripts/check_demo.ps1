param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
$health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method Get
$health | ConvertTo-Json -Depth 5

if ($health.status -eq "error") {
    exit 1
}

Write-Host "Demo 服务已响应。" -ForegroundColor Green
