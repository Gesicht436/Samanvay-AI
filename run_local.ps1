<#
.SYNOPSIS
  Samanvay-AI Local Orchestrator.
  Starts PostgreSQL, Qdrant, Neo4j in Docker, verifies healthchecks,
  initializes schemas & seeds, and launches FastAPI and Next.js with hot-reload.

.EXAMPLE
  .\run_local.ps1
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host "`n===========================================================================" -ForegroundColor Cyan
Write-Host "  SAMANVAY-AI LOCAL ORCHESTRATOR (BharatCodex #81)" -ForegroundColor Cyan
Write-Host "  Starting local development environment with full database & AI models..." -ForegroundColor Cyan
Write-Host "===========================================================================`n" -ForegroundColor Cyan

# 1. Check Docker daemon
Write-Host "[1/5] Checking Docker daemon status..." -ForegroundColor Yellow
try {
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
    if (-not $dockerVersion) {
        throw "Docker is not running. Please start Docker Desktop and retry."
    }
    Write-Host "  [+] Docker daemon is active (v$dockerVersion)" -ForegroundColor Green
} catch {
    Write-Host "  [-] Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# 2. Start Supporting Containers
Write-Host "`n[2/5] Starting supporting database containers (PostgreSQL, Qdrant, Neo4j)..." -ForegroundColor Yellow
docker compose up -d postgres qdrant neo4j

Write-Host "  [+] Waiting for database healthchecks..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$allHealthy = $false

while ($attempt -lt $maxAttempts -and -not $allHealthy) {
    Start-Sleep -Seconds 2
    $attempt++
    
    $pgStatus = (docker inspect --format='{{.State.Health.Status}}' samanvay-postgres 2>$null)
    $qdStatus = (docker inspect --format='{{.State.Health.Status}}' samanvay-qdrant 2>$null)
    $neoStatus = (docker inspect --format='{{.State.Health.Status}}' samanvay-neo4j 2>$null)

    if ($pgStatus -eq "healthy" -and $qdStatus -eq "healthy" -and $neoStatus -eq "healthy") {
        $allHealthy = $true
        Write-Host "  [+] PostgreSQL (5432) : HEALTHY" -ForegroundColor Green
        Write-Host "  [+] Qdrant Vector (6333): HEALTHY" -ForegroundColor Green
        Write-Host "  [+] Neo4j Graph (7687)  : HEALTHY" -ForegroundColor Green
    } else {
        Write-Host "  ... Waiting for containers (attempt $attempt of $maxAttempts - PG=$pgStatus, Qdrant=$qdStatus, Neo4j=$neoStatus)" -ForegroundColor Gray
    }
}

if (-not $allHealthy) {
    Write-Host "  [!] Warning: Containers started but not all reported healthy yet. Proceeding with launch..." -ForegroundColor Yellow
}

# 3. Database Initialization & Seeding
Write-Host "`n[3/5] Verifying database tables and catalog seeding..." -ForegroundColor Yellow
uv run python -c "
from backend.app.ingestion.storage import init_db
init_db()
print('  [+] Relational tables verified in PostgreSQL.')
"

uv run python -c "
from backend.app.ml.vector_search import get_qdrant_client, seed_canonical_catalog
c = get_qdrant_client()
if not c.collection_exists('canonical_materials'):
    print('  [+] Seeding 2,200 canonical items into Qdrant collection...')
    seed_canonical_catalog()
else:
    count = c.count('canonical_materials').count
    print(f'  [+] Qdrant catalog ready with {count} canonical vector points.')
"

uv run python -c "
from backend.app.graph.client import get_neo4j_driver
driver = get_neo4j_driver()
if driver:
    with driver.session() as s:
        res = s.run('MATCH (c:CanonicalMaterial) RETURN count(c) AS cnt')
        cnt = res.single()['cnt']
        if cnt == 0:
            print('  [+] Seeding Neo4j knowledge graph...')
            from backend.app.graph.seed_graph import seed_database
            seed_database()
        else:
            print(f'  [+] Neo4j knowledge graph ready with {cnt} canonical materials.')
"

# 4. Launch FastAPI Backend in a separate window with hot-reload
Write-Host "`n[4/5] Launching FastAPI Backend (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '=== SAMANVAY-AI FASTAPI BACKEND ===' -ForegroundColor Green; cd '$PSScriptRoot'; uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
Write-Host "  [+] Backend process launched at http://localhost:8000" -ForegroundColor Green

# 5. Launch Next.js Frontend in a separate window
Write-Host "`n[5/5] Launching Next.js 15 Web Portal (port 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '=== SAMANVAY-AI NEXT.JS FRONTEND ===' -ForegroundColor Green; cd '$PSScriptRoot\frontend'; npm run dev"
Write-Host "  [+] Frontend process launched at http://localhost:3000" -ForegroundColor Green

Write-Host "`n===========================================================================" -ForegroundColor Cyan
Write-Host "  SAMANVAY-AI LOCAL ENVIRONMENT IS FULLY OPERATIONAL" -ForegroundColor Cyan
Write-Host "===========================================================================" -ForegroundColor Cyan
Write-Host "  Frontend Web Portal   : http://localhost:3000" -ForegroundColor White
Write-Host "  Interactive API Docs  : http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Direct Backend API    : http://localhost:8000/api/v1" -ForegroundColor White
Write-Host "  Qdrant Web Dashboard  : http://localhost:6333/dashboard" -ForegroundColor White
Write-Host "  Neo4j Graph Browser   : http://localhost:7474 (user: neo4j, pass: password)" -ForegroundColor White
Write-Host "  PostgreSQL Database   : localhost:5432/samanvay_db (user: postgres, pass: password)" -ForegroundColor White
Write-Host "`n  To stop the environment later, run: .\stop_local.ps1`n" -ForegroundColor Gray
