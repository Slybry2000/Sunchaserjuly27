# Makefile for common dev tasks
.PHONY: seed-forecasts test lint

# On Windows, use PowerShell to run the helper script
seed-forecasts:
	@echo "Run the PowerShell helper: .\\scripts\\seed_forecasts.ps1"

test:
	pytest -q

lint:
	ruff check . || true
