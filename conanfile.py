from conans import (
    ConanFile,
    tools,
)
from conans.errors import ConanException
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


def jamify(s):
    return s.replace("_", "-")


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


class AttrDict(dict):
    def __init__(self, b2):
        super().__init__()
        super().__setattr__("_b2", b2)

    def __getitem__(self, key):
        name = self._pythonify(key)
        descriptor = type(self).__dict__.get(name)
        if descriptor is None:
            return super(AttrDict, self).__getitem__(self._jamify(key))
        else:
            return descriptor.__get__(self, type(self))

    def __setitem__(self, key, value):
        name = self._pythonify(key)
        descriptor = type(self).__dict__.get(name)
        if descriptor is None:
            super(AttrDict, self).__setitem__(self._jamify(key), value)
        else:
            descriptor.__set__(self, value)

    def __delitem__(self, key):
        name = self._pythonify(key)
        descriptor = type(self).__dict__.get(name)
        if descriptor is None:
            super(AttrDict, self).__delitem__(self._jamify(key))
        else:
            descriptor.__delete__(self)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value
        self.__setitem__(name, value)

    def __delattr__(self, name):
        if name in self.__dict__:
            del self.__dict__[name]
        self.__delitem__(name)

    def update(self, *args, **kw):
        if args:
            d = args[0]
            args = args[1:]
            try:
                # pylint: disable=dict-items-not-iterating
                initial = d.items()
            except:
                initial = d
        else:
            initial = ()

        # pylint: disable=dict-items-not-iterating
        for k, v in itertools.chain(initial, args, kw.items()):
            self[k] = v

    def _jamify(self, key):
        return jamify(key)

    def _pythonify(self, key):
        return key.lstrip("-").replace("-", "_")


class OptionsProxy(AttrDict):
    @property
    def project_config(self):
        return self._b2.project_config

    @project_config.setter
    def project_config(self, value):
        self._b2.project_config = value

    @property
    def build_dir(self):
        return self._b2.build_folder

    @build_dir.setter
    def build_dir(self, value):
        self._b2.build_folder = value

    def strings(self):
        return (self._stringify(k, v) for (k, v) in self.items())

    def _jamify(self, key):
        if key.startswith('-'):
            return key

        key = super()._jamify(key)
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


class PropertySet(AttrDict):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

        for setting in ("os", "arch", "build_type", "compiler", "cppstd"):
            value = getattr(self._b2._conanfile.settings, setting, None)
            if value is None:
                return
            getattr(self, "_init_" + setting)(value)

        for option in ("shared", "static"):
            value = self._b2._conanfile.options.get_safe(option)
            if value is None:
                return
            getattr(self, "_init_" + option)(value)

    @property
    def toolset(self):
        try:
            return self.get("toolset")
        except KeyError as e:
            raise AttributeError(e)

    @toolset.setter
    def toolset(self, args):
        if isinstance(args, six.string_types):
            full_name = args
            args = args.split("-", maxsplit=1)
        else:
            full_name = None
        name = tuple(args[:2])
        args = list(args[2:])

        if args and isinstance(args[-1], dict):
            kw = args[-1]
            del args[-1]
        else:
            kw = {}

        self._b2.using(name, *args, **kw)

        if full_name is None:
            full_name = "-".join(name)
        dict.__setitem__(self, "toolset", full_name)

    @toolset.deleter
    def toolset(self):
        dict.__delitem__(self, "toolset")

    def __str__(self):
        return "/".join((self._stringify(k, v) for (k, v) in self.items()))

    def _stringify(self, option, value):
        return "{option}={value}".format(option=option, value=value)

    def _init_os(self, host_os):
        if not tools.cross_building(self._b2._settings):
            return

        try:
            host_os = str(host_os.subsystem)
        except (AttributeError, ConanException):
            host_os = str(host_os)

        host_os = {
            "WindowsStore": "windows",
            "Macos": "darwin",
            "iOS": "iphone",
            "watchOS": "iphone",
            "tvOS": "appletv",
            "SunOS": "solaris",
            "Arduino": "linux",
            "WSL": "linux",
        }.get(host_os, host_os.lower())
        # Conan host OS corresponds to <target-os> in B2
        self["target_os"] = host_os

    def _init_arch(self, arch):
        if not tools.cross_building(self._b2._settings):
            return

        arch = str(arch)

        def architecture(arch):
            if arch.startswith("x86"):
                return "x86"
            elif arch.startswith("ppc"):
                return "power"
            elif arch.startswith("arm"):
                return "arm"
            elif arch.startswith("sparc"):
                return "sparc"
            elif arch == "mips64":
                return "mips64"
            elif arch == "mips":
                return "mips1"
        self["architecture"] = architecture(arch)

        def address_model(arch):
            if arch in (
                    "x86_64", "ppc64", "ppc64le", "mips64", "armv8", "sparcv9"
            ):
                return 64
            else:
                return 32
        self["address_model"] = address_model(arch)

        iset = {
            "ppc64": "powerpc64",
            "armv6": "armv6",
            "armv7": "armv7",
            "armv7s": "armv7s",
            "sparcv9": "v9",
        }.get(arch)
        if iset is not None:
            self["instruction_set"] = iset

    def _init_compiler(self, value):
        name = str(value)
        toolsets = {
            "Visual Studio": "msvc",
            "apple-clang": "clang",
            "sun-cc": "sun"
        }
        init = [toolsets.get(name, name)]

        version = value.get_safe("version")
        if value == "Visual Studio":
            if version == "15":
                version = "14.1"
            elif version is not None:
                version += ".0"

        command = tools.get_env("CXX") or tools.get_env("CC") or ""

        params = {}

        def get_flags(var):
            return [f for f in tools.get_env(var, "").split(" ") if f]

        cxxflags = get_flags("CXXFLAGS")
        cxxflags += get_flags("CPPFLAGS")
        if cxxflags:
            params["cxxflags"] = cxxflags

        cflags = get_flags("CFLAGS")
        if cflags:
            params["cflags"] = cflags

        ldflags = get_flags("LDFLAGS")
        if ldflags:
            params["ldflags"] = ldflags

        archiver = tools.get_env("AR")
        if archiver:
            params["archiver"] = archiver

        assembler = tools.get_env("AS")
        if assembler:
            params["assembler"] = assembler

        ranlib = tools.get_env("RANLIB")
        if ranlib:
            params["ranlib"] = ranlib

        strip = tools.get_env("STRIP")
        if strip:
            params["striper"] = strip

        rc = tools.get_env("RC")
        if rc:
            key = "resource-compiler" if name == "Visual Studio" else "rc"
            params[key] = rc

        if version or command or params:
            init.append(version)

        if command or params:
            init.append(command)

        if params:
            init.append(params)

        self["toolset"] = init

    def _init_build_type(self, value):
        self["variant"] = str(value).lower()

    def _init_cppstd(self, value):
        value = str(value)
        if value.startswith("gnu"):
            self["cxxstd_dialect"] = "gnu"
            value = value[3:]
        try:
            if int(value) >= 20:
                value = "2a"
        except ValueError:
            pass
        self["cxxstd"] = value

    def _init_shared(self, value):
        self["link"] = "shared" if value else "static"

    def _init_static(self, value):
        self.init_option_shared(not value)


class PropertiesProxy(object):
    def __init__(self, b2):
        setter = super().__setattr__
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


class ToolsetModulesProxy(dict):
    def __call__(self, name, *args, **kw):
        self[name] = (args, kw)

    def dumps(self):
        contents = ""
        for k, v in self.items():
            if isinstance(k, tuple):
                items = list(k)
            else:
                items = [k]
            items += v[0]
            if v[1]:
                opts = (
                    self._dump_param(k, v)
                    for k, v in v[1].items()
                )
                items.append(" ".join(opts))
            contents += "using %s ;\n" % " : ".join(items)
        return contents

    def _dump_param(self, param, value):
        param = jamify(param)
        pattern = '<{param}>"{value}"'
        if (
            not isinstance(value, six.string_types)
            and isinstance(value, collections.Iterable)
        ):
            return " ".join(
                (pattern.format(param=param, value=str(v)) for v in value)
            )
        else:
            return pattern.format(param=param, value=str(value))




class B2(object):
    def __init__(self, conanfile):
        """
        :param conanfile: Conanfile instance
        """

        self._conanfile = conanfile
        self._settings = conanfile.settings

        self.using = ToolsetModulesProxy()
        self.properties = PropertiesProxy(self)

        self.options = OptionsProxy(self)
        self.options.update(
            hash=True,
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

    def configure(self):
        if not self._conanfile.should_configure:
            return

        mkdir(self.build_folder)
        tools.save(
            self.project_config,
            _project_config_template.format(
                install_folder=self._conanfile.install_folder,
                toolset_init=self.using.dumps(),
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
{toolset_init}'''
