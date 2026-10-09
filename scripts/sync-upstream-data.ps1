param(
    [string]$RepositoryUrl = "https://github.com/Gesicht436/Samanvay-AI.git",
    [string]$CheckoutPath = ".upstream-samanvay"
)

$ErrorActionPreference = "Stop"

$source = $null
if (Get-Command git -ErrorAction SilentlyContinue) {
    if (-not (Test-Path $CheckoutPath)) {
        git clone --depth 1 $RepositoryUrl $CheckoutPath
    }
    elseif (-not (Test-Path (Join-Path $CheckoutPath "data"))) {
        throw "The existing checkout does not contain a data directory: $CheckoutPath"
    }
    $source = Join-Path $CheckoutPath "data"
}
else {
    $archive = Join-Path $env:TEMP "samanvay-ai-main.zip"
    $extract = Join-Path $env:TEMP "samanvay-ai-main"
    Invoke-WebRequest -Uri "https://github.com/Gesicht436/Samanvay-AI/archive/refs/heads/main.zip" -OutFile $archive
    if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
    Expand-Archive -Path $archive -DestinationPath $extract -Force
    $source = Join-Path $extract "Samanvay-AI-main\data"
}

if (-not (Test-Path $source)) {
    throw "Upstream data directory was not found: $source"
}

Get-ChildItem -Path $source -Force | Copy-Item -Destination ".\data" -Recurse -Force
Write-Host "Upstream data synced into .\data"