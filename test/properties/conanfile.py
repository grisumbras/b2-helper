# Copyright (c) 2018-2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


import os
from conans import (
    ConanFile,
    tools,
)
from get_helper_package import (
    b2,
    b2_reference,
)


class B2ToolTestConan(b2.B2.mixin, ConanFile):
    build_requires = b2_reference
    exports_sources = "*.cpp", "*.jam"

    def b2_setup_builder(self, builder):
        ps1 = builder.properties[0]
        ps1.threading = "multi"
        ps1.link = "shared"

        ps2 = builder.properties.add()
        ps2.threading = "single"
        ps2.link = "static"

        return builder

    def package(self):
        super(B2ToolTestConan, self).package()

        if tools.os_info.is_windows:
            ext = ".exe"
        else:
            ext = ""
        assert(os.path.exists(
            os.path.join(self.package_folder, "bin", "main1" + ext)
        ))
        assert(os.path.exists(
            os.path.join(self.package_folder, "bin", "main2" + ext)
        ))
