from conans import (
    ConanFile,
    tools,
)
from conans.client import join_arguments
from conans.util.files import mkdir
import functools
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


class folder(object):
    def __init__(self, wrapped):
        self.name = wrapped.__name__
        functools.update_wrapper(self, wrapped)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = getattr(instance, "_" + self.name, None)
        conanfile = getattr(instance, "_conanfile")
        if not value:
            return getattr(conanfile, self.name)
        elif os.path.isabs(value):
            return value
        else:
            return os.path.join(getattr(conanfile, self.name), value)

    def __set__(self, instance, value):
        setattr(instance, "_" + self.name, value)

    def __delete__(self, instance):
        delattr(instance, "_" + self.name)


class B2(object):
    def __init__(self, conanfile):
        """
        :param conanfile: Conanfile instance
        """

        self._conanfile = conanfile
        self._settings = conanfile.settings

    @folder
    def source_folder(self): pass

    @folder
    def build_folder(self): pass

    @folder
    def package_folder(self): pass

    @property
    def project_config(self):
        return os.path.join(self.build_folder, "project-config.jam")

    def configure(self, requirements=None, options=None, **kw_options):
        if not self._conanfile.should_configure:
            return

        kw_options.update(options or dict())

        mkdir(self.build_folder)
        with open(self.project_config, "w") as config_file:
            self._write_toolchain(config_file)
            self._write_options(config_file, kw_options)
            self._write_project(config_file, requirements or [])

    def build(self, *targets, args=None):
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
            "--project-config=" + self.project_config,
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
