# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import ConanFile
from get_helper_package import package_ref
import os


class B2ToolTestConan(ConanFile):
    build_requires = "b2/[*]"
    python_requires = package_ref
    python_requires_extend = "b2-helper.Mixin"
    exports_sources = "*.cpp", "*.hpp", "*.jam"

    def b2_setup_builder(self, builder):
        builder.properties.include = [
            os.path.join(self.source_folder, "include1"),
            os.path.join(self.source_folder, "include2"),
        ]
        return builder
