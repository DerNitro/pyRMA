.PHONY: test lint

VERSION = $(shell python -m src.pyrmalib.info)

# Запуск тестов проекта
test:
	@test -z $(shell git tag -l '$(VERSION)') && echo 'Version $(VERSION): success' || (echo 'Version $(VERSION): bad'; exit 1)
	@uv run pytest -v

# Запуск линтера ruff для проверки кода
lint:
	@uv run ruff check .
