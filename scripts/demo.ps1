param(
    [switch]$Install,
    [switch]$NoServer
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
    Write-Host "已创建 .env，请确认数据库配置后重试。" -ForegroundColor Yellow
    exit 1
}

if ($Install) {
    Write-Host "安装项目依赖..." -ForegroundColor Yellow
    & $python -m pip install -e $root
}

$envText = Get-Content -LiteralPath $envFile -Raw
$dbHost = if ($envText -match '(?m)^DB_HOST=(.+)$') { $Matches[1].Trim() } else { "127.0.0.1" }
$dbPort = if ($envText -match '(?m)^DB_PORT=(\d+)$') { [int]$Matches[1] } else { 3306 }

if (-not (Test-NetConnection -ComputerName $dbHost -Port $dbPort -InformationLevel Quiet)) {
    throw "无法连接 MySQL $dbHost`:$dbPort，请启动数据库后重试。"
}

Write-Host "MySQL $dbHost`:$dbPort 可连接。" -ForegroundColor Green
Write-Host "访问地址：http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "健康检查：http://127.0.0.1:8000/health" -ForegroundColor Green

if (-not $NoServer) {
    & $python (Join-Path $root "run.py") --server
}
