# Copyright (c) 2018 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


import os

from conans import (
    ConanFile,
    python_requires,
)


b2 = python_requires("b2-helper/0.0.1@grisumbras/testing")


class B2ToolTestConan(b2.B2.mixin, ConanFile):
    settings = "os", "compiler", "build_type", "arch", "cppstd",
    generators = "b2"
    build_requires = "boost_build/1.69.0@bincrafters/stable"
    options = {"shared": [True, False]}
    default_options = {"shared": False}

    def b2_setup_builder(self, builder):
        builder.source_folder = "src"
        builder.build_folder = "build"

        builder.options.foo = True
        builder.options.update(bar="baz")

        builder.properties.threading = "multi"

        return builder
