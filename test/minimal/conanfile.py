# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


import os
from conans import (
    ConanFile,
    python_requires,
)


package_version = os.environ.get("CONAN_PACKAGE_VERSION", "[>0]")
package_username = os.environ.get("CONAN_USERNAME", "grisumbras")
package_channel = os.environ.get("CONAN_CHANNEL", "dev")
b2 = python_requires("b2-helper/{version}@{username}/{channel}".format(
    version=package_version,
    username=package_username,
    channel=package_channel,
))


class MyConan(b2.B2.mixin, ConanFile):
    requires = "boost_build/1.69.0@bincrafters/stable"
    exports_sources = "*.jam", "*.cpp"
