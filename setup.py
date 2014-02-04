# -*- coding: utf-8 -*-

'''

  canteen setup
  ~~~~~~~~~~~~~

  :author: Sam Gammon <sam@keen.io>
  :copyright: (c) Keen IO, 2013
  :license: This software makes use of the MIT Open Source License.
            A copy of this license is included as ``LICENSE.md`` in
            the root of the project.

'''

# setuptools
from setuptools import setup


setup(name="canteen",
      version="0.1-alpha",
      description="Minimally complicated, maximally blasphemous approach to app development",
      author="Sam Gammon",
      author_email="sam@keen.io",
      url="https://github.com/sgammon/canteen",
      packages=(
        "canteen",
        "canteen.base",
        "canteen.core",
        "canteen.core.api",
        "canteen.logic",
        "canteen.logic.http",
        "canteen.model",
        "canteen.model.adapter",
        "canteen.rpc",
        "canteen.rpc.protocol",
        "canteen.runtime",
        "canteen.util",
        "canteen_tests"
      ),
      install_requires=(
        "jinja2",
        "werkzeug",
        "protorpc",
        "git+git://github.com/keenlabs/protobuf.git#egg=protobuf",
        "git+git://github.com/keenlabs/hamlish-jinja.git#egg=hamlish_jinja"
      ),
      tests_require=("nose",)
)
