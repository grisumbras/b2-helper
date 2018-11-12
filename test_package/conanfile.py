import os

from conans import (
    ConanFile,
    python_requires,
)


b2_tool = python_requires("b2-tool/0.0.1@grisumbras/testing")


class B2ToolTestConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "b2"
    build_requires = "boost_build/1.67.0@bincrafters/testing"

    def build(self):
        builder = b2_tool.B2(self)
        builder.configure(foo=None, bar="baz")
        builder.build()

    def test(self):
        pass
