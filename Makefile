.PHONY: test

VERSION = $(shell python -m lib.pyrmalib.info)

test:
	@test -z $(shell git tag -l '$(VERSION)') && echo 'Version $(VERSION): success' || (echo 'Version $(VERSION): bad'; exit 1)
	@python -m pytest -v
