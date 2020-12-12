# Copyright (c) 2018-2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import ConanFile
from get_helper_package import package_ref


class B2ToolTestConan(ConanFile):
    build_requires = "b2/[*]"
    python_requires = package_ref
    python_requires_extend = "b2-helper.Mixin"

    settings = "os", "compiler", "build_type", "arch",
    options = {"shared": [True, False]}
    default_options = {"shared": False}
    exports_sources = "*.cpp", "*.jam"
