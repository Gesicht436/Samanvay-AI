<#
.SYNOPSIS
    Starts a Cloudflare Quick Tunnel to expose the Samanvay-AI application to the global internet.
.DESCRIPTION
    Runs an official Cloudflare Tunnel container attached to the Samanvay Docker network.
    Generates a secure https://*.trycloudflare.com URL accessible anywhere in the world.
    No account, domain registration, or router port-forwarding required.
#>

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Samanvay-AI: Cloudflare Global Public Tunnel" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker is running
$dockerCheck = docker ps 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check frontend container is running
$frontendCheck = docker ps --filter "name=samanvay-ai-frontend" --format "{{.Status}}"
if (-not $frontendCheck) {
    Write-Host "[WARN] samanvay-ai-frontend is not running." -ForegroundColor Yellow
    Write-Host "Starting the stack with docker compose..." -ForegroundColor Yellow
    docker compose -f docker/docker-compose.yml --env-file docker/.env.docker up -d
}

Write-Host "[+] Launching Cloudflare Tunnel for frontend (port 3000)..." -ForegroundColor Cyan
Write-Host "[+] All API requests are automatically reverse-proxied to FastAPI (port 8000)." -ForegroundColor Cyan
Write-Host "[+] Press Ctrl+C at any time to terminate the global tunnel." -ForegroundColor Yellow
Write-Host ""

# Run the tunnel interactively so the user sees the generated https://*.trycloudflare.com link live
docker run --rm -it --name samanvay-public-tunnel --network samanvay-ai-network cloudflare/cloudflared:latest tunnel --url http://samanvay-ai-frontend:3000
