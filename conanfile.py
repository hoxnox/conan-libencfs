from nxtools import NxConanFile
from conans import CMake, tools
from shutil import copy
from os import makedirs
from glob import glob


class LibEncfsConan(NxConanFile):
    name = "libencfs"
    version = "1.9.2"
    license = "LGPL"
    url = "https://github.com/hoxnox/conan-libencfs"
    license = "https://github.com/vgough/encfs/blob/master/COPYING.LGPL"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    description = "EncFS - an Encrypted Filesystem"
    requires = "libfuse/2.9.7@hoxnox/stable", "OpenSSL/1.0.2k@lasote/testing"
    default_options = "libfuse:shared=False"

    def do_source(self):
        self.retrieve("cd9e972cd9565cdc26473c86d2c77c98de31fc6f604fa7d149dd5d6e35d46eaa",
                [
                    "vendor://vgough/encfs/encfs-{v}.tar.gz".format(v=self.version),
                    "https://github.com/vgough/encfs/releases/download/v{v}/encfs-{v}.tar.gz".format(v=self.version)
                ],
                "encfs-{v}.tar.gz".format(v=self.version))

    def do_build(self):
        cmake = CMake(self)

        tools.untargz("encfs-{v}.tar.gz".format(v=self.version), "{staging_dir}/src".format(staging_dir=self.staging_dir))
        src_dir = "{staging_dir}/src/encfs-{v}".format(staging_dir=self.staging_dir, v=self.version)
        cmake.build_dir = "{src_dir}/build".format(src_dir=src_dir)
        include_dir = "{staging_dir}/include/encfs".format(staging_dir=self.staging_dir)
        makedirs("{include_dir}/internal".format(include_dir=include_dir))
        makedirs(cmake.build_dir)

        for file in sorted(glob("patch/[0-9]*.patch")):
            self.output.info("Applying patch '{file}'".format(file=file))
            tools.patch(base_path=src_dir, patch_file=file, strip=0)
        if self.settings.os == "Android":
            for file in sorted(glob("patch/android-[0-9]*.patch")):
                self.output.info("Applying patch '{file}'".format(file=file))
                tools.patch(base_path=src_dir, patch_file=file, strip=0)


        cmake_prefix_path = ""
        for k,_ in self.deps_cpp_info.dependencies:
            cmake_prefix_path = "%s;%s" % (cmake_prefix_path, self.deps_cpp_info[k].rootpath)
        cmake_defs = {"CMAKE_INSTALL_PREFIX": self.staging_dir,
                      "CMAKE_INSTALL_LIBDIR": "lib",
                      "CMAKE_PREFIX_PATH": cmake_prefix_path,
                      "ENABLE_NLS": "OFF",
                      "BUILD_SHARED_LIBS": "OFF",
                      "INSTALL_LIBENCFS": "ON"}
        cmake.verbose = True
        cmake_defs.update(self.cmake_crt_linking_flags())
        cmake.configure(defs=cmake_defs, source_dir=src_dir)
        cmake.build(target="install")
        for file in glob("{src_dir}/encfs/*.h".format(src_dir=src_dir)):
            copy(file, include_dir)
        copy("{src_dir}/internal/easylogging++.h".format(src_dir=src_dir),
                "{include_dir}/internal".format(include_dir=include_dir))
        copy("{build_dir}/internal/tinyxml2-3.0.0/libtinyxml2.a".format(build_dir=cmake.build_dir),
                "{staging_dir}/lib".format(staging_dir=self.staging_dir))
        copy("{build_dir}/config.h".format(build_dir=cmake.build_dir), include_dir)

    def do_package_info(self):
        self.cpp_info.libs = ["encfs", "tinyxml2"]
