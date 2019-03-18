# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


import os
from conans import python_requires


package_ref = os.environ.get("PACKAGE_REFERENCE")
b2 = python_requires(package_ref)
b2_reference = "boost_build/1.69.0@bincrafters/stable"
