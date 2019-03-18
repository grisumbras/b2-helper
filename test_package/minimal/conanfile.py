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


class MyConan(b2.B2.Mixin, ConanFile):
    """This is pretty much the bare minimum package definition"""

    requires = b2_reference
    exports_sources = "*.jam", "*.cpp"
