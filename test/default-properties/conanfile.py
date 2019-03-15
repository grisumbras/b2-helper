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


class B2ToolTestConan(b2.B2.Mixin, ConanFile):
    settings = "os", "compiler", "build_type", "arch", "cppstd",
    build_requires = b2_reference
    options = {"shared": [True, False]}
    default_options = {"shared": False}
    exports_sources = "*.cpp", "*.jam"
