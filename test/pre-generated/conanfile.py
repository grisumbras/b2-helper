# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
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


class MyConan(b2.B2.mixin, ConanFile):
    """This package bootstraps its own project-config.jam"""

    requires = b2_reference
    exports_sources = "*.sh", "*.jam", "*.cpp"

    def b2_setup_builder(self, builder):
        builder.include.append(self._bootstrap())
        builder.project_config = os.path.join(self.build_folder, "helper.jam")
        return builder

    def _bootstrap(self):
        if self.should_configure:
            self.run(os.path.join(self.source_folder, "bootstrap.sh"))
        return os.path.join(self.build_folder, "project-config.jam")
