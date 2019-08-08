# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import ConanFile
from get_helper_package import b2


@b2.build_with_b2(build_require_b2="boost_build/1.69.0@bincrafters/stable")
class MyConan(ConanFile):
    def build_requirements(self):
        super(MyConan, self).build_requirements()
        b2_ref = str(self.build_requires["boost_build"])
        assert(b2_ref == "boost_build/1.69.0@bincrafters/stable")

    def build(self):
        pass

    def package(self):
        pass
