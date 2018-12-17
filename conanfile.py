from conans import (
    ConanFile,
    tools,
)
from conans.client import join_arguments
from conans.util.files import mkdir
import collections
import functools
import itertools
import numbers
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


class FancyDict(object):
    def __init__(self, b2):
        setter = super(FancyDict, self).__setattr__
        setter("_b2", b2)
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

    def items(self):
        return self._values.items()

    def dir(self):
        return [
            opt.lstrip("-").replace("-", "_") for opt in self._values.keys()
        ]


class OptionsProxy(FancyDict):
    _special_options = {
        "--project-config": "project_config",
        "--build-dir": "build_folder",
    }

    def __call__(self, *args, **kw):
        # pylint: disable=dict-items-not-iterating
        for k, v in itertools.chain([(a, True) for a in args], kw.items()):
            self[k] = v

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


class PropertySet(FancyDict):
    _special_options = {}

    def __call__(self, **kw):
        for k, v in kw.items():
            self[k] = v

    def __str__(self):
        return "/".join((self._stringify(k, v) for (k, v) in self.items()))

    def _b2ify(self, key):
        return key.replace("_", "-")

    def _stringify(self, option, value):
        return "{option}={value}".format(option=option, value=value)


class PropertiesProxy(object):
    def __init__(self, b2):
        setter = super(PropertiesProxy, self).__setattr__
        setter("_b2", b2)
        setter("_property_sets", [])
        self.add()

    def __getitem__(self, key):
        if isinstance(self, (numbers.Number, slice)):
            return self._property_sets[key]
        return self._property_sets[0][key]

    def __setitem__(self, key, value):
        if isinstance(self, (numbers.Number, slice)):
            self._property_sets[key] = value
        self._property_sets[0][key] = value

    def __delitem__(self, key):
        if isinstance(self, (numbers.Number, slice)):
            del self._property_sets[key]
        del self._property_sets[0][key]

    def __getattr__(self, key):
        return getattr(self._property_sets[0], key)

    def __setattr__(self, key, value):
        setattr(self._property_sets[0], key, value)

    def __delattr__(self, key):
        delattr(self._property_sets[0], key)

    def __iter__(self):
        return iter(self._property_sets)

    def add(self):
        self._property_sets.append(PropertySet(self._b2))
        return self._property_sets[-1]


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

        self.properties = PropertiesProxy(self)

    @folder
    def source_folder(self): pass

    @folder
    def build_folder(self): pass

    @folder
    def package_folder(self): pass

    @property
    def project_config(self):
        return os.path.join(self.build_folder, "project-config.jam")

    def configure(self):
        if not self._conanfile.should_configure:
            return

        mkdir(self.build_folder)
        tools.save(
            self.project_config,
            _project_config_template.format(
                install_folder=self._conanfile.install_folder,
            )
        )

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
            (str(ps) for ps in self.properties),
            targets,
        )
        with tools.chdir(self.source_folder):
            b2_command = "b2 " + join_arguments(args)
            self._conanfile.output.info("%s" % b2_command)
            self._conanfile.run(b2_command)


_project_config_template = '''\
use-packages "{install_folder}/conanbuildinfo.jam" ;
using gcc ;
project : requirements <toolset>gcc ;
'''
