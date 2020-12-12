# Copyright (c) 2018-2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import (
    ConanFile,
    tools,
)
from get_helper_package import package_ref
import os


class B2ToolTestConan(ConanFile):
    build_requires = "b2/[*]"
    python_requires = package_ref
    python_requires_extend = "b2-helper.Mixin"
    exports_sources = "*.cpp", "*.jam"

    def b2_setup_builder(self, builder):
        ps = builder.properties
        ps.threading = "multi"
        ps.link = "shared"
        return builder

    def package(self):
        super(B2ToolTestConan, self).package()

        exe = "main" + (".exe" if tools.os_info.is_windows else "")
        assert(os.path.exists(os.path.join(self.package_folder, "bin", exe)))
