# Copyright (c) 2018-2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import (
    ConanFile,
    tools,
)
from get_helper_package import b2
import os


@b2.build_with_b2
class B2ToolTestConan(ConanFile):
    exports_sources = "*.cpp", "*.jam"

    def b2_setup_builder(self, builder):
        ps = builder.properties
        ps.threading = "multi"
        ps.link = "shared"

        return builder

    def package(self):
        super(B2ToolTestConan, self).package()

        if tools.os_info.is_windows:
            ext = ".exe"
        else:
            ext = ""
        assert(os.path.exists(
            os.path.join(self.package_folder, "bin", "main" + ext)
        ))
