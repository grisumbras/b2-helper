# Copyright (c) 2018-2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


import os
from conans import ConanFile
from get_helper_package import (
    b2,
    b2_reference,
)


class B2ToolTestConan(b2.B2.mixin, ConanFile):
    settings = "os", "compiler", "build_type", "arch", "cppstd",
    build_requires = b2_reference
    options = {"shared": [True, False]}
    default_options = {"shared": False}
    exports_sources = "src/*"

    def b2_setup_builder(self, builder):
        builder.source_folder = "src"
        builder.build_folder = "build"

        builder.options.foo = True
        builder.options.update(bar="baz")

        builder.properties.threading = "multi"

        return builder
