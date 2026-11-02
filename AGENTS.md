# pyRMA Project Instructions

## Overview
**pyRMA** is a remote access control system for server and network equipment via SSH and TELNET, built with Python (Flask, SQLAlchemy, Alembic) and Ansible for deployment.

## Environment & Development Tools
- **Python Environment (uv):** Virtual environment `.venv/` managed via `uv` (`/snap/bin/uv`)
- **Testing Command:** `make test` (or `uv run pytest -v`)
- **Linting Command:** `make lint` (or `uv run ruff check .`)
- **Dependency Management:** `uv` with `pyproject.toml`
- **Database:** PostgreSQL (with SQLAlchemy ORM and Alembic migrations)
- **Deployment:** Ansible playbooks (`deploy.yml`, `ansible/`)

## Key Guidelines
- Always use the `uv` managed `.venv` environment binary path (`.venv/bin/python`, `pytest`, `ruff`) when running commands, tests, or linters.
- **All comments and explanations** in configuration files, documentation, and code must be in **Russian** (as requested by project policy).
- Adhere to existing code style, architectural patterns, and type/testing conventions.
- Never commit credentials or sensitive configuration.
