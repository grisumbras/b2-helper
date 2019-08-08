# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import ConanFile
from get_helper_package import b2
import os


@b2.build_with_b2
class MyConan(ConanFile):
    """This package bootstraps its own project-config.jam"""

    exports_sources = "*.sh", "*.jam", "*.cpp"

    def b2_setup_builder(self, builder):
        builder.include.append(self._bootstrap())
        builder.project_config = os.path.join(self.build_folder, "helper.jam")
        return builder

    def _bootstrap(self):
        if self.should_configure:
            self.run(os.path.join(self.source_folder, "bootstrap.sh"))
        return os.path.join(self.build_folder, "project-config.jam")
