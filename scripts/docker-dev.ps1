# Helper script for Docker Compose commands
# Usage: .\scripts\docker-dev.ps1 [command]
# Commands: logs, setup-categories, setup-demo, shell, restart, migrate, test

param(
    [string]$Command = "help"
)

function Show-Help {
    Write-Host @"
Docker Compose Helper Commands

Usage: .\scripts\docker-dev.ps1 [command]

Commands:
  logs [service]           Show logs (default: backend). Services: backend, celery_worker, celery_beat, gateway, redis, db
  setup-categories         Setup default expense/income categories
  setup-demo              Setup demo financial data
  shell                   Open Django shell in backend container
  restart [service]       Restart service (default: backend)
  migrate                 Run Django migrations
  test                    Run tests
  rebuild [service]       Rebuild and restart (default: backend)
  exec <cmd>              Execute command in backend (e.g. 'manage.py help')
  status                  Show container status

Examples:
  .\scripts\docker-dev.ps1 logs
  .\scripts\docker-dev.ps1 logs celery_worker
  .\scripts\docker-dev.ps1 setup-categories
  .\scripts\docker-dev.ps1 exec manage.py createsuperuser
"@
}

$ProjectRoot = $PSScriptRoot | Split-Path -Parent
Set-Location $ProjectRoot

switch ($Command.ToLower()) {
    "logs" {
        $Service = if ($args[0]) { $args[0] } else { "backend" }
        Write-Host "Showing logs for $Service..." -ForegroundColor Cyan
        docker compose logs $Service -f
    }
    
    "setup-categories" {
        Write-Host "Setting up default categories..." -ForegroundColor Cyan
        docker compose exec backend python manage.py setup_categories
        Write-Host "Done." -ForegroundColor Green
    }
    
    "setup-demo" {
        Write-Host "Setting up demo data..." -ForegroundColor Cyan
        docker compose exec backend python manage.py setup_demo_data
        Write-Host "Done." -ForegroundColor Green
    }
    
    "shell" {
        Write-Host "Opening Django shell..." -ForegroundColor Cyan
        docker compose exec backend python manage.py shell
    }
    
    "restart" {
        $Service = if ($args[0]) { $args[0] } else { "backend" }
        Write-Host "Restarting $Service..." -ForegroundColor Cyan
        docker compose restart $Service
        Write-Host "Done." -ForegroundColor Green
    }
    
    "migrate" {
        Write-Host "Running migrations..." -ForegroundColor Cyan
        docker compose exec backend python manage.py migrate
        Write-Host "Done." -ForegroundColor Green
    }
    
    "test" {
        Write-Host "Running tests..." -ForegroundColor Cyan
        docker compose exec backend python manage.py test
    }
    
    "rebuild" {
        $Service = if ($args[0]) { $args[0] } else { "backend" }
        Write-Host "Rebuilding $Service..." -ForegroundColor Cyan
        docker compose up --build -d $Service
        Write-Host "Done." -ForegroundColor Green
    }
    
    "exec" {
        $Cmd = $args -join " "
        Write-Host "Executing: $Cmd" -ForegroundColor Cyan
        docker compose exec backend python $Cmd
    }
    
    "status" {
        Write-Host "Container status:" -ForegroundColor Cyan
        docker compose ps --format "table {{.Names}}\t{{.Status}}"
    }
    
    default {
        Show-Help
    }
}
