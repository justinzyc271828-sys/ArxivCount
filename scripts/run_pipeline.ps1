# ArxivCount end-to-end pipeline (PowerShell)
# Usage:
#   .\scripts\run_pipeline.ps1
#   .\scripts\run_pipeline.ps1 -MaxPerQuery 100
#   .\scripts\run_pipeline.ps1 -SkipCollect

param(
    [int]$MaxPerQuery = 0,
    [switch]$SkipCollect,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "== ArxivCount pipeline ==" -ForegroundColor Cyan

if (-not $SkipCollect) {
    if ($DryRun) {
        python -m src.collect --dry-run
    }
    elseif ($MaxPerQuery -gt 0) {
        python -m src.collect --max-per-query $MaxPerQuery
    }
    else {
        python -m src.collect
    }
}

if ($env:DEEPSEEK_API_KEY) {
    Write-Host "Running DeepSeek refine..." -ForegroundColor Cyan
    python -m src.refine
} else {
    Write-Host "DEEPSEEK_API_KEY not set; keyword curate only" -ForegroundColor Yellow
    python -m src.curate --min-level L1
}

python -m src.aggregate

Write-Host "Done. Launch dashboard with:" -ForegroundColor Green
Write-Host "  streamlit run app.py"
