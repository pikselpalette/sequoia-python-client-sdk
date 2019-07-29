SHELL=/bin/bash
CWD=$(shell pwd)

SNAPSHOT_VERSION = 0.0.0.dev${GO_PIPELINE_COUNTER}+$(shell echo ${GO_PIPELINE_LABEL} | head -c8).post${GO_STAGE_COUNTER}

default: clean test

clean:
	rm -rf build dist *.egg-info .cache .coverage .pytest_cache .tox

test:
	coverage erase
	pytest -n4 --cov=sequoia --cov-config=setup.cfg -m "not integration_test"

test-all:
	tox

bump_snapshot_version:
	bumpversion --new-version $(SNAPSHOT_VERSION) --parse "(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(\.(?P<snapshot>.*))*" --serialize {major}.{minor}.{patch}.{snapshot} snapshot setup.py setup.cfg sequoia/__init__.py --allow-dirty

lint:
	prospector

.PHONY: clean test test-all lint default
