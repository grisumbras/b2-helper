from conans import (
    ConanFile,
    tools,
)
from conans.client import join_arguments
from conans.util.files import mkdir
import os


class B2ToolConan(ConanFile):
    name = "b2-tool"
    version = "0.0.1"
    description = "conan helper for projects built with b2"
    url = "http://github.com/grisumbras/b2-tools"
    homepage = url
    license = "BSL-1.0"

    def package_info(self):
        self.info.header_only()


class B2(object):
    def __init__(self, conanfile, source_folder=None, build_folder=None):
        """
        :param conanfile: Conanfile instance
        """

        self._conanfile = conanfile
        self._settings = conanfile.settings

        self._source_folder = source_folder
        self._build_folder = build_folder

    @property
    def config_file(self):
        return os.path.join(self.build_folder, "project-config.jam")

    @property
    def source_folder(self):
        if not self._source_folder:
            return self._conanfile.source_folder
        elif os.path.isabs(self._source_folder):
            return self._source_folder
        else:
            return os.path.join(
                self._conanfile.source_folder, self._source_folder
            )

    @property
    def build_folder(self):
        if not self._build_folder:
            return self._conanfile.build_folder
        elif os.path.isabs(self._build_folder):
            return self._build_folder
        else:
            return os.path.join(
                self._conanfile.build_folder, self._build_folder
            )

    def configure(self):
        if not self._conanfile.should_configure:
            return

        mkdir(self.build_folder)
        with open(self.config_file, "w") as config_file:
            self._write_prologue(config_file)
            self._write_epilogue(config_file)

    def build(self):
        if not self._conanfile.should_build:
            return
        self._build()

    def _build(self):
        arg_string = join_arguments(
            [
                "--project-config=" + self.config_file,
                "toolset=gcc",
            ]
        )
        with tools.chdir(self.source_folder):
            self._conanfile.run("b2 " + arg_string)

    def _write_prologue(self, config_file):
        config_file.write(_project_config_prologue.format(
            build_folder=self.build_folder,
            variant="release",
            link="static",
        ))

    def _write_epilogue(self, config_file):
        config_file.write(" ;")


_project_config_prologue = """\
project
    : build-dir {build_folder}
    : requirements
        <variant>{variant}
        <link>{link}
"""
