#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""test_skbuild
----------------------------------

Tests for `skbuild` module.
"""

import os
import platform
import pytest
import sys

from pytest_shutil.cmdline import which

from skbuild.constants import CMAKE_BUILD_DIR
from skbuild.platform_specifics import get_platform

from . import project_setup_py_test, push_env


def test_generator_selection():
    version = sys.version_info
    env_generator = os.environ.get("CMAKE_GENERATOR")
    this_platform = platform.system().lower()
    get_best_generator = get_platform().get_best_generator
    arch = platform.architecture()[0]

    if env_generator:
        assert(get_best_generator(env_generator).name == env_generator)

    if this_platform == "windows":
        # assert that we are running a supported version of python
        py_27_32 = (
            (version.major == 2 and version.minor >= 7) or
            (version.major == 3 and version.minor <= 2)
        )

        py_33_34 = (
            version.major == 3 and (
                3 <= version.minor <= 4
            )
        )

        py_35 = (
            version.major == 3 and
            version.minor >= 5
        )

        assert(len(tuple(filter(bool, (py_27_32, py_33_34, py_35)))) == 1)

        vs_ide_vcvars_path_pattern = \
            "C:/Program Files (x86)/" \
            "Microsoft Visual Studio %.1f/VC/vcvarsall.bat"

        # As of Dec 2016, this is available only for VS 9.0
        vs_for_python_vcvars_path_pattern = \
            "~/AppData/Local/Programs/Common/" \
            "Microsoft/Visual C++ for Python/%.1f/vcvarsall.bat"

        if py_27_32:
            generator = "Visual Studio 9 2008"
            vs_version = 9
        elif py_33_34:
            generator = "Visual Studio 10 2010"
            vs_version = 10
        else:
            generator = "Visual Studio 14 2015"
            vs_version = 14

        generator += (" Win64" if arch == "64bit" else "")

        vs_ide_vcvars_path = vs_ide_vcvars_path_pattern % vs_version
        vs_for_python_vcvars_path = os.path.expanduser(
            vs_for_python_vcvars_path_pattern % vs_version)

        # If environment exists and ninja is found, update the
        # expected generator
        if (
                    os.path.exists(vs_for_python_vcvars_path) or
                    os.path.exists(vs_ide_vcvars_path)
        ) and which("ninja.exe"):
            generator = "Ninja"

        assert(get_best_generator().name == generator)


@pytest.mark.skipif(platform.system().lower() != "windows",
                    reason="NMake Makefiles generator is available "
                           "only on Windows")
def test_nmake_makefiles_generator():

    @project_setup_py_test("hello", ["build"])
    def run_build():
        pass

    with push_env(CMAKE_GENERATOR="NMake Makefiles"):
        tmp_dir = run_build()[0]
        cmakecache = tmp_dir.join(CMAKE_BUILD_DIR).join("CMakeCache.txt")
        assert cmakecache.exists()
        make_program = None
        for line in cmakecache.readlines():
            if line.startswith("CMAKE_MAKE_PROGRAM"):
                make_program = line.strip().split("=")[1]
                break
        assert make_program.endswith("nmake") or \
               make_program.endswith("nmake.exe")
