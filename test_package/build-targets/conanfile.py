# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


import os
from conans import (
    ConanFile,
    tools,
)
from get_helper_package import b2


@b2.build_with_b2
class MyConan(ConanFile):
    exports_sources = "*.jam", "*.cpp"

    b2_build_targets = "install1", "install2"

    def package(self):
        ext = ".exe" if tools.os_info.is_windows else ""
        for i in range(1, 3):
            path = os.path.join(
                self.package_folder,
                "bin",
                "main" + str(i) + ext
            )
            assert os.path.exists(path), i
