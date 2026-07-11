param(
    [switch]$Install,
    [switch]$NoServer,
    [switch]$DemoMode,
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv"
$python = Join-Path $venv "Scripts\python.exe"
$envFile = Join-Path $root ".env"

Write-Host "智能问数（Intelligent Data Query）Demo 启动检查" -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "未找到 Python，请安装 Python 3.12+ 后重试。"
}

if (-not (Test-Path $python)) {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    python -m venv $venv
}

if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root ".env.example") $envFile
    Write-Host "已根据 .env.example 创建 .env。" -ForegroundColor Yellow
}

if ($DemoMode) {
    $envText = Get-Content -LiteralPath $envFile -Raw
    if ($envText -match '(?m)^DEMO_MODE=') {
        $envText = [regex]::Replace($envText, '(?m)^DEMO_MODE=.*$', 'DEMO_MODE=true')
    } else {
        $envText += "`r`nDEMO_MODE=true`r`n"
    }
    Set-Content -LiteralPath $envFile -Value $envText -Encoding utf8
}

if ($Install) {
    Write-Host "安装项目依赖..." -ForegroundColor Yellow
    & $python -m pip install -e $root
}

$envText = Get-Content -LiteralPath $envFile -Raw
$dbHost = if ($envText -match '(?m)^DB_HOST=(.+)$') { $Matches[1].Trim() } else { "127.0.0.1" }
$dbPort = if ($envText -match '(?m)^DB_PORT=(\d+)$') { [int]$Matches[1] } else { 3306 }
$port = if ($envText -match '(?m)^PORT=(\d+)$') { [int]$Matches[1] } else { 8000 }

if (-not (Test-NetConnection -ComputerName $dbHost -Port $dbPort -InformationLevel Quiet)) {
    throw "无法连接 MySQL $dbHost`:$dbPort，请启动数据库后重试。"
}

Write-Host "MySQL $dbHost`:$dbPort 可连接。" -ForegroundColor Green
Write-Host "访问地址：http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "健康检查：http://127.0.0.1:8000/health" -ForegroundColor Green

if (-not $NoServer) {
    $job = Start-Job -ScriptBlock {
        param($projectRoot, $pythonPath, $useDemoMode)
        Set-Location $projectRoot
        if ($useDemoMode) { $env:DEMO_MODE = "true" }
        & $pythonPath (Join-Path $projectRoot "run.py") --server
    } -ArgumentList $root, $python, [bool]$DemoMode

    try {
        $ready = $false
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep -Seconds 1
            try {
                $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 2
                $ready = $true
                break
            } catch { }
        }
        if (-not $ready) {
            Receive-Job $job -Keep
            throw "服务未能在 30 秒内通过健康检查。"
        }
        Write-Host "服务已就绪：健康检查通过。" -ForegroundColor Green
        if ($OpenBrowser) { Start-Process "http://127.0.0.1:$port" }
        Receive-Job $job -Wait
    } finally {
        Stop-Job $job -ErrorAction SilentlyContinue
        Remove-Job $job -Force -ErrorAction SilentlyContinue
    }
}
