# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


import os
from conans import ConanFile
from get_helper_package import (
    b2,
    b2_reference,
)


class B2ToolTestConan(b2.B2.Mixin, ConanFile):
    build_requires = b2_reference
    exports_sources = "*.cpp", "*.hpp", "*.jam"

    def b2_setup_builder(self, builder):
        builder.properties.define = "QWERTY"
        return builder
