# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import (
    ConanFile,
    tools,
)
from get_helper_package import package_ref
import os


class MyConan(ConanFile):
    """This package bootstraps its own project-config.jam"""

    build_requires = "b2/[*]"
    python_requires = package_ref
    python_requires_extend = "b2-helper.Mixin"
    exports_sources = "*.bat", "*.sh", "*.jam", "*.cpp"

    def build(self):
        try:
            super(MyConan, self).build()
        except Exception as exc:
            self.output.info(tools.load(self._bootstrap_script))
            self.output.info(tools.load(
                os.path.join(self.build_folder, "project-config.jam")
            ))
            self.output.info(tools.load(
                os.path.join(self.build_folder, "helper.jam")
            ))
            raise

    def b2_setup_builder(self, builder):
        builder.include.append(self._bootstrap())
        builder.project_config = os.path.join(self.build_folder, "helper.jam")
        return builder

    @property
    def _bootstrap_script(self):
        script = "bootstrap." + ("bat" if tools.os_info.is_windows else "sh")
        return os.path.join(self.source_folder, script)

    def _bootstrap(self):
        if self.should_configure:
            self.run(self._bootstrap_script)
        return os.path.join(self.build_folder, "project-config.jam")
