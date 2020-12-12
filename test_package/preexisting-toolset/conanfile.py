# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


import os
from conans import ConanFile
from get_helper_package import package_ref


class MyConan(ConanFile):
    build_requires = "b2/[*]"
    python_requires = package_ref
    python_requires_extend = "b2-helper.Mixin"
    exports_sources = "*.jam"

    def b2_setup_builder(self, builder):
        builder.using(("foobar", "1"))
        builder.options.user_config = os.path.join(
            self.source_folder, "user-config.jam",
        )
        return builder

    def package(self):
        pass

