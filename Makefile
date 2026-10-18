.PHONY: help build up down test lint k8s-render k8s-up k8s-down k8s-status k8s-logs k8s-rollback

SHELL := /bin/bash
IMAGE_TAG ?= v1.0.0

help:
	@echo "=========================================================="
	@echo " Knowledge Base — DevOps Automation Commands"
	@echo "=========================================================="
	@echo "  make build         - Build Docker images (backend & frontend)"
	@echo "  make up            - Launch 4-tier stack in Docker Compose"
	@echo "  make down          - Stop and clean up Docker Compose containers"
	@echo "  make test          - Run backend Pytest and frontend Vitest"
	@echo "  make lint          - Lint backend code and frontend code"
	@echo "  make k8s-render    - Render Kubernetes manifests with Kustomize"
	@echo "  make k8s-up        - Apply Kubernetes manifests to cluster"
	@echo "  make k8s-down      - Tear down Kubernetes resources"
	@echo "  make k8s-status    - Inspect pod, service, and rollout status"
	@echo "  make k8s-logs      - Stream logs from backend pods"
	@echo "  make k8s-rollback  - Roll back backend Deployment to prior revision"
	@echo "=========================================================="

build:
	@echo "Building Backend container image (kb-backend:$(IMAGE_TAG))..."
	docker build -f docker/Dockerfile.backend -t kb-backend:$(IMAGE_TAG) .
	@echo "Building Frontend container image (kb-frontend:$(IMAGE_TAG))..."
	docker build -f docker/Dockerfile.frontend -t kb-frontend:$(IMAGE_TAG) .

up:
	docker compose up -d

down:
	docker compose down -v

test:
	@echo "Running Backend Unit Tests..."
	python -m pytest KB-main/tests/ -m "not integration" -v
	@echo "Running Frontend Vitest Suite..."
	cd KB-main/frontend && npm run test

lint:
	@echo "Linting backend Python code..."
	flake8 KB-main/backend --count --max-line-length=120 --statistics || true
	@echo "Linting frontend JavaScript..."
	cd KB-main/frontend && npm run lint --if-present || true

k8s-render:
	kubectl kustomize k8s/

k8s-up:
	kubectl apply -k k8s/
	kubectl rollout status deployment/postgres -n knowledge-base --timeout=120s
	kubectl rollout status deployment/qdrant -n knowledge-base --timeout=120s
	kubectl rollout status deployment/backend -n knowledge-base --timeout=180s
	kubectl rollout status deployment/frontend -n knowledge-base --timeout=120s

k8s-down:
	kubectl delete -k k8s/

k8s-status:
	kubectl get pods,services,pvc,configmap,secret -n knowledge-base

k8s-logs:
	kubectl logs -l app=backend -n knowledge-base -f --tail=100

k8s-rollback:
	@echo "Rolling back backend deployment..."
	kubectl rollout undo deployment/backend -n knowledge-base
	kubectl rollout status deployment/backend -n knowledge-base

