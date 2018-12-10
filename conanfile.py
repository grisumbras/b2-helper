from conans import (
    ConanFile,
    tools,
)
from conans.client import join_arguments
from conans.util.files import mkdir
import collections
import functools
import itertools
import os
import six


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


class OptionsProxy(object):
    _special_options = {
        "--project-config": "project_config",
        "--build-dir": "build_folder",
    }

    def __init__(self, b2):
        setter = super(OptionsProxy, self).__setattr__
        setter("_b2", b2)
        setter("_conanfile", getattr(b2, "_conanfile"))
        setter("_values", {})

    def __getitem__(self, key):
        key = self._b2ify(key)
        return self._values[key]

    def __setitem__(self, key, value):
        key = self._b2ify(key)

        if key in self._special_options.keys():
            setattr(self._b2, self._special_options[key], value)
        else:
            self._values[key] = value

    def __delitem__(self, key):
        key = self._b2ify(key)
        del self._values[key]

    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]

    def __call__(self, *args, **kw):
        # pylint: disable=dict-items-not-iterating
        for k, v in itertools.chain([(a, True) for a in args], kw.items()):
            self[k] = v

    def items(self):
        return self._values.items()

    def dir(self):
        return [
            opt.lstrip("-").replace("-", "_") for opt in self._values.keys()
        ]

    def strings(self):
        return (self._stringify(k, v) for (k, v) in self.items())

    def _b2ify(self, key):
        if key.startswith('-'):
            return key

        key = key.replace("_", "-")
        if len(key) == 1:
            key = "-" + key
        else:
            key = "--" + key
        return key

    def _stringify(self, option, value):
        if value is True:
            return option

        if (
            not isinstance(value, six.string_types)
            and isinstance(value, collections.Iterable)
        ):
            return "{option} {values}".format(
                option=option,
                values=" ".join([str(v) for v in value]),
            )
        elif option[1] != '-':
            return option + str(value)
        else:
            return "{option}={value}".format(
                option=option,
                value=value,
            )


class B2(object):
    def __init__(self, conanfile):
        """
        :param conanfile: Conanfile instance
        """

        self._conanfile = conanfile
        self._settings = conanfile.settings

        self.options = OptionsProxy(self)
        self.options(
            "hash",
            j=tools.cpu_count(),
            d=tools.get_env("CONAN_B2_DEBUG", "1"),
        )

    @folder
    def source_folder(self): pass

    @folder
    def build_folder(self): pass

    @folder
    def package_folder(self): pass

    @property
    def project_config(self):
        return os.path.join(self.build_folder, "project-config.jam")

    def configure(self, requirements=None):
        if not self._conanfile.should_configure:
            return

        mkdir(self.build_folder)
        with open(self.project_config, "w") as config_file:
            self._write_toolchain(config_file)
            self._write_project(config_file, requirements or [])

    def build(self, *targets):
        if not (targets or self._conanfile.should_build):
            return
        self._build(targets)

    def install(self):
        if not self._conanfile.should_install:
            return
        self._build(["install"])

    def test(self):
        if not self._conanfile.should_test:
            return
        self._build(["test"])

    def _build(self, targets):
        special_options = (
            "--project-config=" + self.project_config,
            "--build-dir=" + self.build_folder,
        )
        args = itertools.chain(
            special_options,
            self.options.strings(),
            targets,
        )
        with tools.chdir(self.source_folder):
            b2_command = "b2 " + join_arguments(args)
            self._conanfile.output.info("%s" % b2_command)
            self._conanfile.run(b2_command)

    def _write_toolchain(self, config_file):
        config_file.write("using gcc ;\n\n")

    def _write_project(self, config_file, requirements):
        config_file.write("project\n")
        config_file.write("  : requirements\n")
        requirements = itertools.chain(
            requirements,
            [("variant", "release"), ("link", "static"), ("toolset", "gcc")],
        )
        for k, v in requirements:
            config_file.write("      <{k}>{v}\n".format(k=k, v=v))
        config_file.write("  ;\n")
