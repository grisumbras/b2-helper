# Copyright (c) 2018-2019 Dmitry Arkhipov <grisumbras@gmail.com>
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE or copy at http://www.boost.org/LICENSE_1_0.txt)


from conans import (
    ConanFile,
    tools,
)
from conans.errors import ConanException
from conans.util.files import mkdir
import collections
import functools
import itertools
import numbers
import os
import six


class B2ToolConan(ConanFile):
    name = "b2-helper"
    version = "0.7.1"
    description = "conan helper for projects built with b2"
    url = "http://github.com/grisumbras/b2-helper"
    homepage = url
    license = "BSL-1.0"
    exports = "LICENSE*"

    def package_info(self):
        self.info.header_only()


def jamify(s):
    """
    Convert a valid Python identifier to a string that follows Boost.Build
    identifier convention.
    """
    return s.replace("_", "-")


class folder(object):
    """
    Descriptor class that implements fallback mechanics for accessing
    Conan folders. When used like this:

        @folder
        def foobar_folder(self): pass

    `foobar_folder` becomes a property-like object that sets and deletes
    `self._foobar_folder` and uses the following algorithm for getting a value:

        * if `self` does not have attribure `_foobar_folder`, return
          `self.conanfile.foobar_folder`;
        * else, if the attribute's value is an absolute path, return it
          unchanged;
        * else return
          `os.path.join(self.conanfile.foobar_folder, self._foobar_folder)`.
    """

    def __init__(self, wrapped):
        self.name = wrapped.__name__
        functools.update_wrapper(self, wrapped)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        value = getattr(instance, "_" + self.name, None)
        if not value:
            return getattr(instance.conanfile, self.name)
        elif os.path.isabs(value):
            return value
        else:
            return os.path.join(getattr(instance.conanfile, self.name), value)

    def __set__(self, instance, value):
        setattr(instance, "_" + self.name, value)

    def __delete__(self, instance):
        delattr(instance, "_" + self.name)


class AttrDict(dict):
    """
    dict subclass that allows accessing keys as attributes (but with extra
    features).

    On dictionary access, a key is first converted to a valid Pyton identifier
    and then checked if it corresponds to an attribute of the instance. If it
    does, the attribute is accessed as a descriptor. If it doesn't, the key is
    converted to the string corresponding to its use in Boost.Build
    (by default, `jamify` is applied, but subclasses may modify this behavior).
    After that, that string is used as a final dictionary key.

    On attribute access a key is checked to correspond to an attribute on
    instance, then dictionary access is performed.

    For example:

        d = AttrDict()
        d["foo-bar"] = "baz"
        d["foo_bar"] = "baz" # does the same
        d.foo_bar = "baz"    # does the same
        list(d.items()) # [("foo-bar", "baz")]

    The special treatment of descriptor attributes allows tweaking the behavior
    for some keys (see subclasses for examples).
    """

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
    """
    AttrDict subclass that is specifically tailored for Boost.Build CLI
    options. On key/attribute access, when keys are jamified they are also
    prepended with dashes. Single letter keys are prepended with 1 dash,
    multi-letter keys are prepended with 2 dashes. For example:

        o = OptionsProxy(b2)
        o["--foo-bar"] = "baz"
        o["foo-bar"] = "baz" # does the same
        o["foo_bar"] = "baz" # does the same
        o.foo_bar = "baz"    # does the same
        o["-x"] = 1
        o["x"] = 1 # does the same
        o.x = 1    # does the same
        list(o.items()) # [("--foo-bar", "baz"), ("-x", 1)]
    """

    def __init__(self, b2):
        """
        :param b2: associated B2 instance.
        """

        super().__init__()
        dict.__setattr__(self, "_b2", b2)

    @property
    def project_config(self):
        """
        Forwards to associated B2 instance's property `project_config`.
        """

        return self._b2.project_config

    @project_config.setter
    def project_config(self, value):
        self._b2.project_config = value

    @property
    def build_dir(self):
        """
        Forwards to associated B2 instance's property `build_folder`.
        """

        return self._b2.build_folder

    @build_dir.setter
    def build_dir(self, value):
        self._b2.build_folder = value

    def strings(self):
        """
        Returns a generator that yields options converted to strings.
        If an option O has a value V, then the function yields:

            * "O v [v...]" for all v in V, if V iterable and is not a string;
            * "OV", if O is a short option (dash followed by a letter);
            * "O=V" otherwise.
        """

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
    """
    AttrDict subclass that is specifically tailored for Boost.Build property
    sets specified using CLI.
    """

    def __init__(self, b2, no_defaults=False):
        """
        Initializes PropertySet object. If defaults are not disabled, collects
        properties from `b2.conanfile.settings` and `b2.conanfile.options`.

        :param b2: associated B2 instance;
        :param no_defaults: disable collecting default values from conanfile's
                            settings and options.
        """

        super().__init__()
        dict.__setattr__(self, "_b2", b2)

        if no_defaults:
            return

        for setting in ("os", "arch", "build_type", "compiler", "cppstd"):
            self._init_setting(setting)
        self._init_setting("os_target", "os")

        for option in ("shared", "static"):
            value = self._b2.conanfile.options.get_safe(option)
            if value is None:
                return
            getattr(self, "_init_" + option)(value)

    @property
    def toolset(self):
        """
        Sets's the current property set's `toolset` property and requires its
        initialization from the associated B2 instance. For example,

            ps.toolset = "gcc-8"

        sets the `toolset` property to `gcc-8` and also invokes

            b2.using("gcc", "8")

        on the associated B2 instance.

        Allowed values:

            * string `s`. Sets `toolset` property to s. If s matches pattern
              `name-version`, then `b2.using((name, version))` is called
              for associated B2 instance. Otherwise, `b2.using(s)` is called.
            * any iterable `a`. Sets `toolset` property to `a[0]-a[1]`. If
              `a[-1]` is a dict calls
              `b2.using(tuple(a[:2]), *a[2:-1], **a[-1])` for associated B2
              instance. Otherwise, calls `b2.using(tuple(a[:2]), *a[2:])`.

        Examples:

            ps.toolset = "gcc"                            # b2.using("gcc",)
            ps.toolset = "msvc-14.1"                      # b2.using(("msvc", "14.1"))
            ps.toolset = ("sun", None, "/opt/sun/bin/CC") # b2.using("sun", "/opt/sun/bin/CC")
            ps.toolset = ("gcc", ", {"cxxflags: "-Wall"}) # b2.using("gcc", cxxflags="-Wall")
        """

        try:
            return self.get("toolset")
        except KeyError as e:
            raise AttributeError(e)

    @toolset.setter
    def toolset(self, args):
        if isinstance(args, six.string_types):
            args = args.split("-", maxsplit=1)

        name = tuple([str(a) for a in args[:2] if a])
        if len(name) < 2:
            name = name[0]
            full_name = name
        else:
            full_name = "-".join(name)

        args = list(args[2:])

        if args and isinstance(args[-1], dict):
            kw = args[-1]
            del args[-1]
        else:
            kw = {}

        self._b2.using(name, *args, **kw)

        dict.__setitem__(self, "toolset", full_name)

    @toolset.deleter
    def toolset(self):
        dict.__delitem__(self, "toolset")

    def flattened(self):
        for key, value in self.items():
            if (not isinstance(value, six.string_types)
                and isinstance(value, collections.Iterable)
            ):
                for subvalue in value:
                    yield (key, str(subvalue))
            else:
                yield (key, str(value))

    def _init_os(self, host_os):
        if not tools.cross_building(self._b2.conanfile.settings):
            return

        try:
            subsystem = host_os.subsystem
            if subsystem:
                host_os = subsystem
        except (AttributeError, ConanException):
            pass
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
        if not tools.cross_building(self._b2.conanfile.settings):
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

        if arch in (
            "x86_64", "ppc64", "ppc64le", "mips64", "armv8", "sparcv9"
        ):
            am = 64
        else:
            am = 32
        self["address_model"] = am

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

        if self._b2.conanfile.settings.get_safe("compiler.cppstd") is not None:
            self._init_cppstd(self._b2.conanfile.settings.compiler.cppstd)

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

    def _init_setting(self, setting, alias=None):
        if self._b2.conanfile.settings.get_safe(setting) is None:
            return
        value = getattr(self._b2.conanfile.settings, setting)
        getattr(self, "_init_" + (alias or setting))(value)


class ToolsetModulesProxy(dict):
    """
    dict subclass that acts as a collection of toolset modules.
    """

    def __call__(self, name, *args, **kw):
        """
        Register or update initialization of a toolset module.

        :param name: name of the module or name-version pair;
        :param args: positional arguments to module initialization ;
        :param kw: options for module initialization ;
        """

        self[name] = (args, kw)

    def tuples(self):
        """
        Dumps all toolset module configuraions into a multiline string usable
        as a part of Boost.Build configuration file.
        For example, if a module was registerd via
        `self.using(("a", "b"), "c", "d", e="f")`, then result will contain
        the line `using a : b : c : d : <e>"f" ;`
        """

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
            yield items

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


class Mixin(object):
    """
    Convenience mixin class that enables building with Boost.Build.
    Just add it to the list of bases for your ConanFile subclass and it
    will override methods `build`, `package` and `test`. Note, since
    `ConanFile` class declares those methods, you need to put this mixin
    *before* it. Example:

        b2 = python_requires(...)
        class MyConan(b2.Mixin, ConanFile):
            name = "..."
            version = "..."
            settings = "os", "arch", "compiler", "build_type"

    And that's it.
    """

    def __init__(self, *args, **kw):
        """
        Constructor. Adds `b2` generator if it wasn't present already.
        """

        super().__init__(*args, **kw)

        if not hasattr(self, "generators"):
            self.generators = ("b2",)
        elif "b2" not in self.generators:
            generators = self.generators
            if isinstance(generators, six.string_types):
                generators = [generators]
            else:
                generators = list(generators)
            generators.append("b2")
            self.generators = tuple(generators)

    def b2_setup_builder(self, builder):
        """
        If you want to customize the build helper, you need to override
        this method. It should return an instance of `B2` class.

        :param builder: an instance of `B2` class.
        """

        return builder

    def build(self):
        """Configures and builds default targets."""

        builder = self.b2_setup_builder(B2(self))
        builder.configure()

        targets = getattr(self, "b2_build_targets", [])
        if isinstance(targets, six.string_types):
            targets = [targets]
        builder.build(*targets)

    def package(self):
        """Builds target `install`."""

        builder = self.b2_setup_builder(B2(self))
        builder.install()

    def test(self):
        """Builds target `test`."""

        builder = self.b2_setup_builder(B2(self))
        builder.test()


class B2(object):
    """
    Build helper for Boost.Build build system.
    """

    def __init__(self, conanfile, no_defaults=False):
        """
        :param conanfile: Conanfile instance
        :param no_defaults: disable collecting default values from conanfile's
                            settings and options.
        """

        self.conanfile = conanfile
        self.include = []

        self.using = ToolsetModulesProxy()
        self.properties = PropertySet(self, no_defaults)

        self.options = OptionsProxy(self)
        if not no_defaults:
            self.options.update(
                hash=True,
                j=tools.cpu_count(),
                d=tools.get_env("CONAN_B2_DEBUG", "1"),
                prefix=self.package_folder,
            )

    @folder
    def source_folder(self):
        """Directory that contains jamroot file"""

    @folder
    def build_folder(self):
        """Directory that will contain build artifacts"""

    @folder
    def package_folder(self):
        """Directory that will contain installed artifacts (install prefix)"""

    @property
    def executable(self):
        """
        Boost.Build executable that will be used.
        """

        exe = getattr(self, "_executable", None)
        if exe is None:
            return "b2.exe" if tools.os_info.is_windows else "b2"
        else:
            return exe

    @executable.setter
    def executable(self, value):
        # pylint: disable=attribute-defined-outside-init
        self._executable = value

    @executable.deleter
    def executable(self):
        del self._executable

    @property
    def project_config(self):
        """
        Path to configuration file that will be created by the helper and
        loaded by Boost.Build as project configuration
        """

        result = getattr(self, "_project_config", None)
        if result is not None:
            return result
        return os.path.join(self.build_folder, "project-config.jam")

    @project_config.setter
    def project_config(self, value):
        # pylint: disable=attribute-defined-outside-init
        self._project_config = value

    @project_config.deleter
    def project_config(self):
        del self._project_config

    def configure(self):
        """Create the project configuration file"""
        if not self.conanfile.should_configure:
            return

        mkdir(self.build_folder)
        path = os.path.relpath(
            self.conanfile.install_folder, self.source_folder
        )
        with open(self.project_config, "w") as file:
            build_info = path_escaped(os.path.join(path, "conanbuildinfo.jam"))
            file.write((
                "import path ;\n"
                "import feature ;\n"
                "use-packages [ path.make \"{0}\" ] ;\n"
                "local all-toolsets = [ feature.values toolset ] ;\n"
            ).format(build_info))


            for module in self.using.tuples():
                if len(module) > 1:
                    file.write((
                        "if ! {0} in $(all-toolsets) ||"
                        " ! [ feature.is-subvalue toolset : {0}"
                        " : version : {1}"
                        " ]"
                    ).format(*module[:2]))
                else:
                    file.write("if ! ( %s in $(all-toolsets) )" % module[0])
                file.write(" { using %s ; }\n" % " : ".join(module))

            for include in self.include:
                include = path_escaped(include)
                file.write("include \"%s\" ;\n" % include)

            file.write("project : requirements\n")
            for k, v in self.properties.flattened():
                file.write("  <%s>%s\n" % (k, path_escaped(v)))
            file.write("  ;\n")


    def build(self, *targets):
        """
        Run Boost.Build and build targets `targets` using the active options,
        and property sets. Requires `self.configure()` to have been called
        before with the current configuration.

        :param targets: target references that will be built.
        """
        if not (targets or self.conanfile.should_build):
            return
        self._build(targets)

    def install(self, force=True):
        """
        Run Boost.Build to build target `install`. Doesn't do anything if
        `conanfile.should_install` is falsey.

        :param force: build anyway.
        """

        if force or self.conanfile.should_install:
            self._build(["install"])

    def test(self, force=False):
        """
        Run Boost.Build to build target `test`. Doesn't do anything if
        if environment variable `CONAN_RUN_TESTS` is defined and is falsey.

        :param force: test anyway.
        """

        if force or tools.get_env("CONAN_RUN_TESTS", True):
            self._build(["test"])

    def _build(self, targets):
        special_options = (
            "--project-config=" + self.project_config,
            "--build-dir=" + self.build_folder,
        )

        args = itertools.chain(
            [self.executable],
            targets,
            special_options,
            self.options.strings(),
        )

        with tools.chdir(self.source_folder):
            self.conanfile.run(join_arguments(args))


def join_arguments(args):
    return " ".join(filter(None, args))


def path_escaped(path):
    if os.sep == "\\":
        path  = path.replace("\\", "\\\\")
    return path
