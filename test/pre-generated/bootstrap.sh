#!/bin/sh

# Copyright (c) 2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)

cat >project-config.jam <<EOF
import option ;
option.set foobar : 1 ;
EOF
