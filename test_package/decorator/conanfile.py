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


@b2.build_with_b2
class MyConan(ConanFile):
    """This is pretty much the bare minimum package definition"""

    requires = b2_reference
    exports_sources = "*.jam", "*.cpp"
