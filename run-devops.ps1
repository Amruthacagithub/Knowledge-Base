<#
.SYNOPSIS
    Knowledge Base — DevOps Automation PowerShell Script
.DESCRIPTION
    Provides cross-platform automation commands for building, testing, deploying,
    and monitoring the Knowledge Base application stack.
.EXAMPLE
    .\run-devops.ps1 -Target test
    .\run-devops.ps1 -Target build
    .\run-devops.ps1 -Target k8s-render
    .\run-devops.ps1 -Target up
#>

param (
    [Parameter(Mandatory=$false, Position=0)]
    [ValidateSet("help", "test", "lint", "build", "up", "down", "k8s-render", "k8s-up", "k8s-down", "k8s-status", "k8s-logs", "k8s-rollback")]
    [string]$Target = "help",

    [Parameter(Mandatory=$false)]
    [string]$ImageTag = "v1.0.0"
)

$ErrorActionPreference = "Continue"

function Show-Help {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host " Knowledge Base — DevOps Automation (PowerShell)" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "  .\run-devops.ps1 -Target test          Run backend and frontend test suites"
    Write-Host "  .\run-devops.ps1 -Target lint          Run code linting"
    Write-Host "  .\run-devops.ps1 -Target build         Build backend & frontend Docker images"
    Write-Host "  .\run-devops.ps1 -Target up            Start 4-tier stack in Docker Compose"
    Write-Host "  .\run-devops.ps1 -Target down          Stop and clean up Docker Compose"
    Write-Host "  .\run-devops.ps1 -Target k8s-render    Render Kubernetes manifests with Kustomize"
    Write-Host "  .\run-devops.ps1 -Target k8s-up        Deploy application stack to Kubernetes"
    Write-Host "  .\run-devops.ps1 -Target k8s-down      Delete Kubernetes resources"
    Write-Host "  .\run-devops.ps1 -Target k8s-status    Inspect Kubernetes pods, services, and PVCs"
    Write-Host "  .\run-devops.ps1 -Target k8s-logs      Tail backend logs in Kubernetes"
    Write-Host "  .\run-devops.ps1 -Target k8s-rollback  Roll back backend Deployment to prior revision"
    Write-Host "==========================================================" -ForegroundColor Cyan
}

switch ($Target) {
    "test" {
        Write-Host "--> Running Backend Pytest Suite..." -ForegroundColor Green
        .\venv\Scripts\python.exe -m pytest KB-main/tests/ -m "not integration" -v
        Write-Host "--> Running Frontend Vitest Suite..." -ForegroundColor Green
        Push-Location KB-main/frontend
        npm run test
        Pop-Location
    }
    "lint" {
        Write-Host "--> Linting Python backend..." -ForegroundColor Green
        .\venv\Scripts\python.exe -m flake8 KB-main/backend --count --max-line-length=120 --statistics
        Write-Host "--> Linting Frontend..." -ForegroundColor Green
        Push-Location KB-main/frontend
        npm run lint
        Pop-Location
    }
    "build" {
        Write-Host "--> Building Backend container: kb-backend:$ImageTag..." -ForegroundColor Green
        docker build -f docker/Dockerfile.backend -t "kb-backend:$ImageTag" .
        Write-Host "--> Building Frontend container: kb-frontend:$ImageTag..." -ForegroundColor Green
        docker build -f docker/Dockerfile.frontend -t "kb-frontend:$ImageTag" .
    }
    "up" {
        Write-Host "--> Starting Docker Compose services..." -ForegroundColor Green
        docker compose up -d
    }
    "down" {
        Write-Host "--> Stopping Docker Compose services..." -ForegroundColor Yellow
        docker compose down -v
    }
    "k8s-render" {
        Write-Host "--> Rendering Kustomize manifests..." -ForegroundColor Green
        kubectl kustomize k8s/
    }
    "k8s-up" {
        Write-Host "--> Deploying to Kubernetes namespace 'knowledge-base'..." -ForegroundColor Green
        kubectl apply -k k8s/
        kubectl rollout status deployment/postgres -n knowledge-base --timeout=120s
        kubectl rollout status deployment/qdrant -n knowledge-base --timeout=120s
        kubectl rollout status deployment/backend -n knowledge-base --timeout=180s
        kubectl rollout status deployment/frontend -n knowledge-base --timeout=120s
    }
    "k8s-down" {
        Write-Host "--> Tearing down Kubernetes resources..." -ForegroundColor Yellow
        kubectl delete -k k8s/
    }
    "k8s-status" {
        Write-Host "--> Kubernetes Pods and Services:" -ForegroundColor Green
        kubectl get pods,services,pvc,configmap,secret -n knowledge-base
    }
    "k8s-logs" {
        Write-Host "--> Streaming backend logs:" -ForegroundColor Green
        kubectl logs -l app=backend -n knowledge-base -f --tail=100
    }
    "k8s-rollback" {
        Write-Host "--> Undoing rollout for deployment/backend..." -ForegroundColor Yellow
        kubectl rollout undo deployment/backend -n knowledge-base
        kubectl rollout status deployment/backend -n knowledge-base
    }
    Default {
        Show-Help
    }
}
