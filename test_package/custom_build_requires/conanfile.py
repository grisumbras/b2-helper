# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import ConanFile
from get_helper_package import b2
import os


@b2.build_with_b2
class MyConan(ConanFile):
    exports_sources = "jamroot*", "*.cpp"

    def build_requirements(self):
        f = open("marker", "w")
        f.close()

    def build(self):
        assert(os.path.exists(os.path.join("..", "..", "marker")))

    def package(self):
        pass
