
#
#    canteen: makefile
#
#   :author: Sam Gammon <sam@keen.io>
#   :copyright: (c) Keen IO, 2013
#   :license: This software makes use of the MIT Open Source License.
#             A copy of this library is included as ``LICENSE.md`` in
#             the root of the project.
#


## Vars
DISTRIBUTIONS ?= bdist_egg sdist bdist_dumb

## Flags
TEST_FLAGS ?= --verbose --with-coverage --cover-package=canteen --cover-package=canteen_tests


all: develop

test: build
	@nosetests $(TEST_FLAGS) canteen_tests

clean:
	@echo "Cleaning buildspace..."
	@rm -fr build/

	@echo "Cleaning egginfo..."
	@rm -fr canteen.egg-info

	@echo "Cleaning object files..."
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete

build: .Python dependencies
	@python setup.py build

develop: build
	@python setup.py develop

package:
	@python setup.py $(DISTRIBUTIONS)

release: build test package
	@python setup.py $(DISTRIBUTIONS) upload

dependencies:
	# install pip dependencies
	@bin/pip install colorlog
	@bin/pip install -r requirements.txt

distclean: clean
	@echo "Cleaning env..."
	@rm -fr .Python lib include

	@echo "Resetting codebase..."
	@git reset --hard

	@echo "Cleaning codebase..."
	@git clean -xdf

.Python:
	# install pip/virtualenv if we have to
	@which pip || sudo easy_install pip
	@which virtualenv || pip install virtualenv

	@virtualenv .
