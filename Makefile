.PHONY: test lint

VERSION = $(shell python -m lib.pyrmalib.info)

# Запуск тестов проекта
test:
	@test -z $(shell git tag -l '$(VERSION)') && echo 'Version $(VERSION): success' || (echo 'Version $(VERSION): bad'; exit 1)
	@python -m pytest -v

# Запуск линтера ruff для проверки кода
lint:
	@ruff check .

