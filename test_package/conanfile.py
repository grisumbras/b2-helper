import os

from conans import (
    ConanFile,
    python_requires,
)


build_helper = python_requires("b2-helper/0.0.1@grisumbras/testing")


class B2ToolTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch", "cppstd",
    generators = "b2"
    build_requires = "boost_build/1.68.0@bincrafters/testing"
    options = {"shared": [True, False]}
    default_options = {"shared": False}

    def build(self):
        builder = build_helper.B2(self)
        builder.source_folder = "src"
        builder.build_folder = "build"

        builder.options.foo = True
        builder.options(bar="baz")

        builder.properties.threading = "multi"

        builder.configure()
        builder.build()

    def test(self):
        pass
