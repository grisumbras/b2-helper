import os

from conans import (
    ConanFile,
    python_requires,
)


build_helper = python_requires("b2-helper/0.0.1@grisumbras/testing")


class B2ToolTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "b2"
    build_requires = "boost_build/1.67.0@bincrafters/testing"

    def build(self):
        builder = build_helper.B2(self)
        builder.source_folder = "src"
        builder.build_folder = "build"
        builder.configure(foo=None, bar="baz")
        builder.build()

    def test(self):
        pass
