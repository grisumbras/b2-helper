from conans import (
    ConanFile,
    tools,
)
from conans.client import join_arguments
from conans.util.files import mkdir
import itertools
import os


class B2ToolConan(ConanFile):
    name = "b2-helper"
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

    def configure(self, requirements=None, options=None, **kw_options):
        if not self._conanfile.should_configure:
            return

        kw_options.update(options or dict())

        mkdir(self.build_folder)
        with open(self.config_file, "w") as config_file:
            self._write_toolchain(config_file)
            self._write_options(config_file, kw_options)
            self._write_project(config_file, requirements or [])

    def build(self, args=None, *targets):
        if not self._conanfile.should_build:
            return
        self._build(args or [], targets)

    def install(self, args=None):
        if not self._conanfile.should_install:
            return
        self._build(args or [], ["install"])

    def test(self, args=None):
        if not self._conanfile.should_test:
            return
        self._build(args or [], ["test"])

    def _build(self, args, targets):
        options = [
            "--project-config=" + self.config_file,
            "-j%s" % tools.cpu_count(),
            "-d+%s" % tools.get_env("CONAN_B2_DEBUG", "1"),
            "--hash",
        ]
        args = itertools.chain(options, args, targets)
        with tools.chdir(self.source_folder):
            b2_command = "b2 " + join_arguments(args)
            self._conanfile.output.info("%s" % b2_command)
            self._conanfile.run(b2_command)

    def _write_toolchain(self, config_file):
        config_file.write("using gcc ;\n\n")

    def _write_options(self, config_file, options):
        config_file.write("import option ;\n")
        for k, v in options.items():
            if v is not None:
                pattern = "option.set {k} : {v} ;\n"
            else:
                pattern = "option.set {k} ;\n"
            config_file.write(pattern.format(k=k, v=v))
        config_file.write("\n")

    def _write_project(self, config_file, requirements):
        config_file.write("project\n")
        config_file.write("  : build-dir {0}\n".format(self.build_folder))
        config_file.write("  : requirements\n")
        requirements = itertools.chain(
            requirements,
            [("variant", "release"), ("link", "static"), ("toolset", "gcc")],
        )
        for k, v in requirements:
            config_file.write("      <{k}>{v}\n".format(k=k, v=v))
        config_file.write("  ;\n")
