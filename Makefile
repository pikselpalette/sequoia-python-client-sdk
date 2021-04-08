SHELL=/bin/bash
CWD=$(shell pwd)

default: clean test

clean:
	rm -rf build dist *.egg-info .cache .coverage .pytest_cache .tox
	find . -type f -name "*.pyc" -exec rm {} \;

test:
	coverage erase
	pytest --numprocesses auto --cov=sequoia --cov-config=setup.cfg -m "not integration_test"

test-all:
	tox

lint:
	prospector

.PHONY: clean test test-all lint default
