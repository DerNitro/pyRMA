# pyRMA Project Instructions

## Overview
**pyRMA** is a remote access control system for server and network equipment via SSH and TELNET, built with Python (Flask, SQLAlchemy, Alembic) and Ansible for deployment.

## Environment & Development Tools
- **Python Environment (pyenv):** `pyrma` (`/home/sutkin/.pyenv/versions/pyrma/`)
- **Testing Command:** `/home/sutkin/.pyenv/versions/pyrma/bin/pytest -v`
- **Linting Command:** `/home/sutkin/.pyenv/versions/pyrma/bin/ruff check .` (or via `make lint`)
- **Dependency Management:** `pip` with `requirements.txt`
- **Database:** PostgreSQL (with SQLAlchemy ORM and Alembic migrations)
- **Deployment:** Ansible playbooks (`deploy.yml`, `ansible/`)

## Key Guidelines
- Always use the `pyrma` pyenv environment binary path (`/home/sutkin/.pyenv/versions/pyrma/bin/python`, `pytest`, `ruff`) when running commands, tests, or linters.
- **All comments and explanations** in configuration files, documentation, and code must be in **Russian** (as requested by project policy).
- Adhere to existing code style, architectural patterns, and type/testing conventions.
- Never commit credentials or sensitive configuration.
