<#
.SYNOPSIS
  Samanvay-AI Local Shutdown Utility.
  Stops the background Docker database containers cleanly.

.EXAMPLE
  .\stop_local.ps1
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`nStopping Samanvay-AI local database containers..." -ForegroundColor Yellow
docker compose stop postgres qdrant neo4j

Write-Host "[+] Containers stopped successfully. To stop terminal windows, close the PowerShell windows.`n" -ForegroundColor Green
