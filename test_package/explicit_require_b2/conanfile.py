# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


import os
from conans import ConanFile
from get_helper_package import b2


@b2.build_with_b2(build_require_b2=True)
class MyConan(ConanFile):
    exports_sources = "jamroot*", "*.cpp"
