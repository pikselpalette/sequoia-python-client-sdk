SHELL=/bin/bash
CWD=$(shell pwd)

ifndef GO_PIPELINE_LABEL
	SEQUOIA_CLIENT_SDK_PYTHON_HASH=
else
	SEQUOIA_CLIENT_SDK_PYTHON_HASH=$(shell echo $${GO_DEPENDENCY_LABEL_UPSTREAM} | head -c 8)
endif

default: noop

noop:
	@echo "i think your're searching ./make command instead make"

release:
	git reset $(SEQUOIA_CLIENT_SDK_PYTHON_HASH)
	./make package --release
	./make deploy --local

.PHONY: default release
