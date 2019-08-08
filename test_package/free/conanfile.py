# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import ConanFile
from get_helper_package import b2
import os


@b2.build_with_b2
class B2ToolTestConan(ConanFile):
    exports_sources = "*.cpp", "*.hpp", "*.jam"

    def b2_setup_builder(self, builder):
        builder.properties.include = [
            os.path.join(self.source_folder, "include1"),
            os.path.join(self.source_folder, "include2"),
        ]
        return builder
