# Copyright (c) 2018-2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import ConanFile
from get_helper_package import b2


@b2.build_with_b2
class B2ToolTestConan(ConanFile):
    exports_sources = "*.cpp", "*.jam"

    def b2_setup_builder(self, builder):
        builder.options.foo = True
        builder.options["bar"] = 1234
        builder.options.update(baz="foobar")
        return builder
