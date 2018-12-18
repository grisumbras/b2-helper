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
    _special_keys = {}

    def __init__(self, b2):
        super().__init__()
        super().__setattr__("_b2", b2)

    def __getitem__(self, key):
        return self._interact_with_item(getattr, super().__getitem__, key)

    def __setitem__(self, key, value):
        self._interact_with_item(setattr, super().__setitem__, key, value)

    def __delitem__(self, key):
        self._interact_with_item(delattr, super().__delitem__, key)

    __getattr__ = __getitem__
    __setattr__ = __setitem__
    __delattr__ = __delitem__

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

    def jamify(self, key):
        return jamify(key)

    def _interact_with_item(self, special, regular, key, *args):
        key = self.jamify(key)
        reflist = self._special_keys.get(key)
        if reflist is None:
            return regular(key, *args)

        reflist = reflist.split(".")
        obj = self
        for ref in reflist[:-1]:
            obj = getattr(obj, ref)

        return special(obj, reflist[-1])


class OptionsProxy(AttrDict):
    _special_keys = {
        "--project-config": "_b2.project_config",
        "--build-dir": "_b2.build_folder",
    }

    def strings(self):
        return (self._stringify(k, v) for (k, v) in self.items())

    def jamify(self, key):
        if key.startswith('-'):
            return key

        key = super().jamify(key)
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
        self._init_from_conanfile("setting")
        self._init_from_conanfile("option")

    def init_setting_build_type(self, value):
        self["variant"] = str(value).lower()

    def init_setting_cppstd(self, value):
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

    def init_setting_os(self, host_os):
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

    def init_setting_arch(self, arch):
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

    def init_option_shared(self, value):
        self["link"] = "shared" if value else "static"

    def init_option_static(self, value):
        self.init_option_shared(not value)

    def __str__(self):
        return "/".join((self._stringify(k, v) for (k, v) in self.items()))

    def _stringify(self, option, value):
        return "{option}={value}".format(option=option, value=value)

    def _init_from_conanfile(self, source):
        for name, value in getattr(self._b2._conanfile, source + "s").items():
            name = "init_%s_%s" % (source, name.replace(".", "_"))
            if hasattr(self._b2, name):
                func = getattr(self._b2, name)
                func(self, value)
            else:
                try:
                    func = self.__getattribute__(name)
                    func(value)
                except AttributeError:
                    continue


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
                    "<{k}>{v}".format(k=jamify(k), v=v)
                    for k, v in v[1].items()
                )
                items.append(" ".join(opts))
            contents += "using %s ;\n" % " : ".join(items)
        return contents


class B2(object):
    def __init__(self, conanfile):
        """
        :param conanfile: Conanfile instance
        """

        self._conanfile = conanfile
        self._settings = conanfile.settings

        self.options = OptionsProxy(self)
        self.options.update(
            hash=True,
            j=tools.cpu_count(),
            d=tools.get_env("CONAN_B2_DEBUG", "1"),
        )

        self.properties = PropertiesProxy(self)

        self.using = ToolsetModulesProxy()
        self.using("gcc")

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
{toolset_init}
project : requirements <toolset>gcc ;
'''
