# Copyright (c) 2018-2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import ConanFile
from get_helper_package import b2
import os


@b2.build_with_b2
class B2ToolTestConan(ConanFile):
    exports_sources = "*.cpp", "*.jam"

    def b2_setup_builder(self, builder):
        builder.build_folder = "build"
        return builder

    def build(self):
        super(B2ToolTestConan, self).build()
        assert(os.path.exists(os.path.join(self.build_folder, "build")))
