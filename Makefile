
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
TEST_RESULTS?=$(BUILDROOT).develop/tests/xunit
COVERAGE_RESULTS?=$(BUILDROOT).develop/coverage/xunit

## Flags
TEST_FLAGS ?= --verbose \
							--with-coverage \
							--cover-package=canteen \
							--cover-package=canteen_tests \
							--cover-branches \
							--cover-html \
							--cover-xml \
							--with-xunit \
							--cover-html-dir=.develop/coverage/html \
							--cover-xml-file=.develop/coverage/clover.xml \
							--xunit-file=.develop/tests/xunit.xml

all: develop

ifeq ($(TESTS),1)
test:
	@mkdir -p $(TEST_RESULTS) $(COVERAGE_RESULTS)
	@-$(BINPATH)nosetests $(TEST_FLAGS) canteen_tests
else
test:
	@echo "Skipping tests."
endif

build: .Python dependencies
	@$(BINPATH)python setup.py build

package: develop test
	@$(BINPATH)python setup.py $(DISTRIBUTIONS)

release: build test package
	@$(BINPATH)python setup.py $(DISTRIBUTIONS) upload

ifeq ($(DEPS),1)
develop: build
	@echo "Installing development tools..."
	@$(BINPATH)pip install --upgrade -r dev_requirements.txt

	@echo "Building..."
	@$(BINPATH)python setup.py develop
else
develop: build package
	@echo "Building..."
	@$(BINPATH)python setup.py develop
endif

ifeq ($(DEPS),1)
dependencies:
	# install pip dependencies
	@$(BINPATH)python -c "import colorlog" > /dev/null || $(BINPATH)pip install colorlog
	@$(BINPATH)pip install --upgrade -r requirements.txt
else
dependencies:
	@echo "Skipping dependencies..."
endif

clean:
	@echo "Cleaning buildspace..."
	@rm -fr build/

	@echo "Cleaning egginfo..."
	@rm -fr canteen.egg-info

	@echo "Cleaning object files..."
	@find $(BUILDROOT) -name "*.pyc" -delete
	@find $(BUILDROOT) -name "*.pyo" -delete

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
	@which pip > /dev/null || sudo easy_install pip
	@which virtualenv > /dev/null || pip install virtualenv

	@echo "Making virtualenv..."
	@virtualenv $(BUILDROOT) > /dev/null
else
.Python:
	@echo "Skipping env..."
endif
