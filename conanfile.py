from nxtools import NxConanFile
from conans import CMake, tools
from shutil import copy, copytree
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
    requires = "libfuse/2.9.7@hoxnox/stable", "libressl/2.5.3@hoxnox/stable"
    default_options = "libfuse:shared=False", "libressl:shared=False"
    exports = "patch/*", "nxtools/__init__.py", "nxtools/nx_conan_file.py"

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
        copytree("patch", "{src_dir}/patch".format(src_dir=src_dir))
        makedirs("{include_dir}/internal".format(include_dir=include_dir))
        makedirs(cmake.build_dir)

        for file in sorted(glob("patch/*.patch")):
            self.output.info("Applying patch '{file}'".format(file=file))
            tools.patch(base_path=src_dir, patch_file=file, strip=0)

        cmake_defs = {"CMAKE_INSTALL_PREFIX": self.staging_dir,
                      "CMAKE_INSTALL_LIBDIR": "lib",
                      "CMAKE_C_FLAGS": "-DBUILD_NLS=0",
                      "FUSE_USE_STATIC_LIBS": "0" if self.options["libfuse"].shared else "1",
                      "INSTALL_LIBENCFS": "True"}
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
