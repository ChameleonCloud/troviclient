.PHONY: docs
docs:
	@tox -e docs

.PHONY: build
build:
	poetry build

.PHONY: publish
publish: build
	poetry publish
