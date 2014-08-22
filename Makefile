
#
#    canteen: makefile
#
#   :author: Sam Gammon <sam@keen.io>
#   :copyright: (c) Sam Gammon, 2014
#   :license: This software makes use of the MIT Open Source License.
#             A copy of this library is included as ``LICENSE.md`` in
#             the root of the project.
#


## Vars
DEPS?=1
TESTS?=1
VIRTUALENV?=1
DISTRIBUTIONS ?= bdist_egg sdist bdist_dumb
BUILDROOT?=./
BINPATH?=

## Flags
TEST_FLAGS ?= --verbose \
							--with-coverage \
							--cover-package=canteen \
							--cover-package=canteen_tests \
							--cover-html \
							--cover-xml \
							--with-xunit \
							--cover-html-dir=.develop/coverage/html \
							--cover-xml-file=.develop/coverage/clover.xml \
							--xunit-file=.develop/tests/xunit.xml

all: develop

ifeq ($(TESTS),1)
test: develop
	@mkdir -p $(BUILDROOT).develop/tests/xunit $(BUILDROOT).develop/coverage/xunit
	@-$(BINPATH)nosetests $(TEST_FLAGS) canteen_tests
else
test:
	@echo "Skipping tests."
endif

clean:
	@echo "Cleaning buildspace..."
	@rm -fr build/

	@echo "Cleaning egginfo..."
	@rm -fr canteen.egg-info

	@echo "Cleaning object files..."
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete

build: .Python dependencies
	@$(BINPATH)python setup.py build

ifeq ($(DEPS),1)
develop: build
	@echo "Installing development tools..."
	@$(BINPATH)pip install -r dev_requirements.txt

	@echo "Building..."
	@$(BINPATH)python setup.py develop
else
develop: build package
	@echo "Building..."
	@$(BINPATH)python setup.py develop
endif

package: test
	@$(BINPATH)python setup.py $(DISTRIBUTIONS)

release: build test package
	@$(BINPATH)python setup.py $(DISTRIBUTIONS) upload

ifeq ($(DEPS),1)
dependencies:
	# install pip dependencies
	@$(BINPATH)pip install colorlog
	@$(BINPATH)pip install -r requirements.txt
else
dependencies:
	@echo "Skipping dependencies..."
endif

distclean: clean
	@echo "Cleaning env..."
	@rm -fr .Python lib include

	@echo "Resetting codebase..."
	@git reset --hard

	@echo "Cleaning codebase..."
	@git clean -xdf

ifeq ($(VIRTUALENV),1)
.Python:
	# install pip/virtualenv if we have to
	@which pip || sudo easy_install pip
	@which virtualenv || pip install virtualenv

	@virtualenv $(BUILDROOT)
else
.Python:
	@echo "Skipping env..."
endif
