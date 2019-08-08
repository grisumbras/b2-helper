from conans import (
    ConanFile,
    tools,
)
import os


class TestB2Helper(ConanFile):
    _tests = (
        "minimal",
        "explicit_require_b2",
        "custom_build_requires",
        "custom_b2_reference",
        "source_folder",
        "build_folder",
        "options",
        "properties",
        "pre-generated",
        "default-properties",
        "free",
        "propagate-subdir",
        "build-targets",
    )
    _intall_cmd = "conan install %s -if tmp/conan"
    _source_cmd = "conan source %s -if tmp/conan -sf tmp/src"
    _build_cmd = (
        "conan build %s -if tmp/conan -sf tmp/src -bf tmp/build -pf tmp/stage"
    )
    _package_cmd = (
        "conan package %s"
        " -if tmp/conan"
        " -sf tmp/src"
        " -bf tmp/build"
        " -pf tmp/stage"
    )

    def test(self):
        env = {
            "PACKAGE_REFERENCE": str(self.requires["b2-helper"].ref),
            "PYTHONPATH": [os.path.join(self.source_folder, "modules")],
        }
        with tools.environment_append(env):
            for test_name in self._tests:
                self.run_test(test_name)

    def run_test(self, test_name):
        self.output.info("Running test %s" % test_name)
        tools.mkdir(test_name)
        with tools.chdir(test_name):
            test_path = os.path.join(self.source_folder, test_name)
            self.run(self._intall_cmd % test_path)
            self.run(self._source_cmd % test_path)
            self.run(self._build_cmd % test_path)
            self.run(self._package_cmd % test_path)
