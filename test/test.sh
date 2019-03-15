#!/bin/sh

# Copyright (c) 2018-2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


set -e


here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
cd $here

export CONAN_PACKAGE_VERSION=$(conan inspect .. -a version | cut -d\  -f2)
export PYTHONPATH=$here/modules:$PYTHONPATH

run_test()  {
  test_name=$1
  shift
  echo ====================================
  echo Running test: $test_name
  echo

  cd ./$test_name
  rm -rf ./tmp
  conan install . -if tmp/conan
  conan source . -if tmp/conan -sf tmp/src
  conan build . -if tmp/conan -sf tmp/src -bf tmp/build -pf tmp/stage
  conan package . -if tmp/conan -sf tmp/src -bf tmp/build -pf tmp/stage
  cd $here
}

run_test minimal
run_test source_folder
run_test build_folder
run_test options
run_test pre-generated
run_test misc
