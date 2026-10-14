#!/bin/env python

# MizProject Code for MizKernel XZ1 Build

import os
import sys
import subprocess
import argparse as agp

TARGETS = ["poplar", "poplar-dsds", "poplar-kddi", "lilac", "lilac-dcm", "maple", "maple-dsds"]

parse = agp.ArgumentParser(description="MizKernel Build Script for Xperia XZ1")
parse.add_argument("-M", "--menuconf", help="Run menuconfig for kconfig", action="store_true" )
parse.add_argument("-b", "--build", help="Build the kernel, adding another value points what specific build you want to build, see -eh build for more.", nargs="?", const="poplar-kddi", choices=TARGETS)
parse.add_argument("-d", "--download-deps", help="Download Dependencies needed for the build", action="store_true")
parse.add_argument("-eh", "--extra-help", help="Show extra help message and exit", action="store_true")

args = parse.parse_args()

def nl():
    print("\n")

def extra_help():
    print("Extra Help:")
    print("-b build: Specify the build target") 
    print("Available build targets:")
    print(f"  {', '.join(TARGETS)}")
    print("(note that default without specifiying a target is 'poplar-kddi')")
    nl()
    print("-M: Run menuconfig for kconfig")
    print("-d: Download dependencies needed for the build")
    print("-h: Show this help message and exit")
    print("-eh: Show extra help message and exit")
    quit()


COMMON_MAKE_FLAGS = [
    "O=out",
    "ARCH=arm64",
    "SUBARCH=arm64",
    "LLVM=1",
    "LLVM_IAS=1",
    "KBUILD_BUILD_USER='@Mizumo_prjkt'",
    "KBUILD_BUILD_HOST='MizProject_ContainerBuild'",
    "CROSS_COMPILE=aarch64-linux-gnu-",
    "CROSS_COMPILE_ARM32=arm-linux-gnueabi-"
]

clang_dir = "toolchains/clang-r547379"
tarball = "clang-r547379.tar.gz"
url = "https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+archive/refs/heads/main/clang-r547379.tar.gz"


if args.extra_help:
    extra_help()


def grab_clang():
    print("Grabbing Clang r547379")
    dl = subprocess.run(["curl", "-L", "-o", tarball, url])
    print("Confirming Clang r547379 is downloaded")
    if dl.returncode != 0 or not os.path.exists(tarball):
        print("Error: Clang r547379 failed to download.")
        sys.exit(1)
    print("Extracting clang-r547379 to toolchains/clang-r547379")
    print("First, check if toolchains/clang-r547379 exists, if it does, delete it and re-extract")
    if os.path.exists(clang_dir):
        print("toolchains/clang-r547379 exists, deleting it")
        subprocess.run(["rm", "-rf", clang_dir])
        os.makedirs(clang_dir)
    else:
        print("toolchains/clang-r547379 does not exist, creating it")
        os.makedirs(clang_dir)
    print("Extracting clang-r547379 to toolchains/clang-r547379")
    subprocess.run(["tar", "-xf", tarball, "-C", clang_dir, "--strip-components=1"])
    print("Clang r547379 extracted to toolchains/clang-r547379")
    print("Cleaning up, removing clang-r547379.tar.gz")
    os.remove(tarball)

def package_manager_dl():
    print("Downloading dependencies needed for the build")
    subprocess.run(["sudo", "apt-get", "update"])
    p1 = subprocess.run(["sudo", "apt-get", "install", "-y", "build-essential", "bc", "bison", "flex", "libssl-dev", "libncurses6","libelf-dev", "libncurses6", "libncurses-dev", "x11proto-core-dev", "zip", "unzip", "aria2", "python3", "python-is-python3", "cpio", "kmod", "rsync", "pahole", "fontconfig", "bc", "xsltproc", "libxml2-utils", "zlib1g-dev", "libc6-dev-i386"])
    if p1.returncode != 0:
        print("Error: Failed to install dependencies. Please check your internet connection and try again.")
        quit()
    print("Dependencies downloaded successfully")

def modernized_gnu_assemblers_dl():
    print("Downloading modernized GNU assemblers")
    p2 = subprocess.run(["sudo", "apt-get", "install", "-y", "gcc-aarch64-linux-gnu", "gcc-arm-linux-gnueabi", "binutils-aarch64-linux-gnu", "binutils-arm-linux-gnueabi"])
    if p2.returncode != 0:
        print("Error: Failed to install modernized GNU assemblers. Please check your internet connection and try again.")
        quit()
    print("Modernized GNU assemblers downloaded successfully")

def download_dependencies():
    print("Downloading dependencies needed for the build")
    package_manager_dl()
    grab_clang()
    modernized_gnu_assemblers_dl()
    print("Dependencies downloaded successfully")

def setup_build_env():
    os.environ["ARCH"] = "arm64"
    os.environ["SUBARCH"] = "arm64"
    os.environ["PATH"] = os.path.join(os.getcwd(), clang_dir, "bin") + ":" + os.environ["PATH"]




if args.download_deps:
    download_dependencies()

if args.menuconf:
    setup_build_env()
    print("Running menuconfig for kernel")
    subprocess.run(["make", "menuconfig"])

if args.extra_help:
    extra_help()

if args.download_deps:
    download_dependencies()

def check_tools():
    print("Checking for required tools...")
    required_tools = ["make", "gcc", "clang", "aarch64-linux-gnu-gcc", "arm-linux-gnueabi-gcc"]
    missing_tools = []
    for tool in required_tools:
        if subprocess.run(["which", tool], stdout=subprocess.DEVNULL).returncode != 0:
            missing_tools.append(tool)
    if missing_tools:
        print(f"Error: Missing required tools: {', '.join(missing_tools)}")
        print("Please install the missing tools and try again.")
        quit()
    print("All required tools are present.")

if args.build:
    setup_build_env()
    check_tools()
    defconfig_target = f"lineage-msm8998-yoshino-{args.build.replace('-', '_')}_defconfig"
    cores = os.cpu_count() or 16

    print(f"Generating defconfig for {defconfig_target}...")
    subprocess.run(["make"] + COMMON_MAKE_FLAGS + [defconfig_target], check=True)

    if args.menuconf:
        print("Running menuconfig for kernel...")
        subprocess.run(["make"] + COMMON_MAKE_FLAGS + ["menuconfig"], check=True)

    print(f"Building kernel for {args.build} with {cores} in system.")
    subprocess.run(["make", f"-j{cores}"] + COMMON_MAKE_FLAGS, check=True)