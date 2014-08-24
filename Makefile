
#
#    canteen: makefile
#
#   :author: Sam Gammon <sam@keen.io>
#   :copyright: (c) Sam Gammon, 2014
#   :license: This software makes use of the MIT Open Source License.
#             A copy of this library is included as ``LICENSE.md`` in
#             the root of the project.
#


SHELL := /bin/bash

## Vars
DEPS?=1
TESTS?=1
SHELL?=bash
VIRTUALENV?=1
DISTRIBUTIONS ?= bdist_egg sdist bdist_dumb
BUILDROOT?=./
TEST_FLAGS?=
BINPATH?=$(BUILDROOT)bin/
TEST_RESULTS?=$(BUILDROOT).develop/tests/xunit
COVERAGE_RESULTS?=$(BUILDROOT).develop/coverage/xunit


## Colors + Texts
STOP=\x1b[;0m
RED=\x1b[31;01m
GREEN=\x1b[32;01m
CYAN=\x1b[36;01m
YELLOW=\x1b[33;01m
MAGENTA=\x1b[35;01m

OK=$(GREEN)[OK]$(STOP)
ERROR=$(RED)[ERROR]$(STOP)
WARN=$(YELLOW)[WARN]$(STOP)


## Functions
define say
	@printf "$(CYAN)"
	@echo $1
	@printf "$(STOP)"
endef

define okay
	@printf "$(GREEN)"
	@echo $1 $2
	@printf "$(STOP)"
endef

define warn
	@printf "$(YELLOW)"
	@echo $1 $2
	@printf "$(STOP)"
endef

define error
	@printf "$(RED)"
	@echo $1 $2
	@printf "$(STOP)"
endef


all: .Python develop test package ready

ready:
	@echo
	$(call okay,"~~ canteen ready ~~")
	@echo


ifeq ($(TESTS),1)
test:
	$(call say,"Running testsuite...")
	@mkdir -p $(TEST_RESULTS) $(COVERAGE_RESULTS)
	@-$(BINPATH)nosetests --with-coverage \
							--cover-package=canteen \
							--cover-package=canteen_tests \
							--cover-html \
							--cover-xml \
							--with-xunit \
							--cover-html-dir=.develop/coverage/html \
							--cover-xml-file=.develop/coverage/clover.xml \
							--xunit-file=.develop/tests/xunit.xml $(TEST_FLAGS) canteen_tests
	$(call okay,"All tests passed!")
else
test:
	$(call warn,"Skipping tests.")
endif

build: .Python dependencies
	$(call say,"Building framework...")
	@$(BINPATH)python setup.py build
	$(call okay,"Framework built successfully.")

package: test
	$(call say,"Building release packages...")
	@$(BINPATH)python setup.py $(DISTRIBUTIONS)
	$(call okay,"Framework release packages built.")

ifeq ($(DEPS),1)
develop: build
	$(call say,"Installing dev dependencies...")
	@$(BINPATH)pip install -q --upgrade -r dev_requirements.txt

	$(call say,"Building framework for development...")
	-@$(BINPATH)python setup.py develop
else
develop: build
	$(call say,"Building framework for development...")
	-@$(BINPATH)python setup.py develop
endif

ifeq ($(DEPS),1)
dependencies:
	$(call say,"Installing runtime dependencies (this may take a moment)...")
	@$(BINPATH)python -c "import colorlog" > /dev/null 2> /dev/null || $(BINPATH)pip -q install colorlog
	@$(BINPATH)pip install -q --upgrade -r requirements.txt
	$(call okay,"Runtime dependencies ready.")
else
dependencies:
	$(call warn,"Skipping dependencies...")
endif

clean:
	$(call say,"Cleaning buildspace...")
	@rm -fr build/

	$(call say,"Cleaning egginfo...")
	@rm -fr canteen.egg-info

	$(call say,"Cleaning object files...")
	@find $(BUILDROOT) -name "*.pyc" -delete
	@find $(BUILDROOT) -name "*.pyo" -delete

distclean: clean
	$(call say,"Cleaning environment...")
	@rm -fr .Python lib include

	$(call say,"Resetting codebase...")
	@git reset --hard

	$(call say,"Cleaning codebase...")
	@git clean -xdf

	$(call okay,"~~ codebase cleaned. ~~")

ifeq ($(VIRTUALENV),1)
.Python:
	@which pip > /dev/null || sudo easy_install pip
	@which virtualenv > /dev/null || pip install virtualenv

	$(call say,"Preparing virtual environment...")
	@virtualenv $(BUILDROOT) > /dev/null
	$(call okay,"Virtual environment ready.")
else
.Python:
	$(call warn,"Skipping virtual environment...")
endif
