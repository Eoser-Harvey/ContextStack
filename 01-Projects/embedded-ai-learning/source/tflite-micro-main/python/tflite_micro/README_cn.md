<!-- 翻译：AI助手，于 2026年5月13日 -->
<!-- 格式：中英文对照，便于学习 -->

# `tflite_micro` Python 包
# The `tflite_micro` Python Package

此目录包含 `tflite_micro` Python 包。以下主要是其开发人员的文档。
This directory contains the `tflite_micro` Python package. The following is
mainly documentation for its developers.

`tflite_micro` 包包含一个完整的 TFLM 解释器，构建为 CPython 扩展模块。简单 Python 包的构建可能由标准 Python 包构建器（如 `build`、`setuptools` 和 `flit`）驱动；然而，由于 TFLM 首先是一个大型 C/C++ 项目，`tflite_micro` 的构建由其 C/C++ 构建系统 Bazel 驱动。
The `tflite_micro` package contains a complete TFLM interpreter built as a
CPython extension module. The build of simple Python packages may be driven by
standard Python package builders such as `build`, `setuptools`, and `flit`;
however, as TFLM is first and foremost a large C/C++ project, `tflite_micro`'s
build is instead driven by its C/C++ build system Bazel.

## 本地构建和安装
## Building and installing locally

### 构建
### Building

Bazel 目标 `//python/tflite_micro:whl.dist` 在输出目录 `bazel-bin/python/tflite_micro/whl_dist` 下构建一个 `tflite_micro` Python *.whl*。例如：
The Bazel target `//python/tflite_micro:whl.dist` builds a `tflite_micro`
Python *.whl* under the output directory `bazel-bin/python/tflite_micro/whl_dist`. For example:

```
% bazel build //python/tflite_micro:whl.dist
....
Target //python/tflite_micro:whl.dist up-to-date:
  bazel-bin/python/tflite_micro/whl_dist

% tree bazel-bin/python/tflite_micro/whl_dist
bazel-bin/python/tflite-micro/whl_dist
└── tflite_micro-0.dev20230920161638-py3-none-any.whl
```

### 安装
### Installing

通过 pip 安装生成的 *.whl*。例如，在 Python 虚拟环境中：
Install the resulting *.whl* via pip. For example, in a Python virtual
environment:

```
% python3 -m venv ~/tmp/venv
% source ~/tmp/venv/bin/activate
(venv) $ pip install bazel-bin/python/tflite_micro/whl_dist/tflite_micro-0.dev20230920161638-py3-none-any.whl
Processing ./bazel-bin/python/tflite_micro/whl_dist/tflite_micro-0.dev20230920161638-py3-none-any.whl
....
Installing collected packages: [....]
```

现在该包应该可以导入和使用。例如：
The package should now be importable and usable. For example:

```
(venv) $ python
Python 3.10.12 (main, Jun 11 2023, 05:26:28) [GCC 11.4.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import tflite_micro
>>> tflite_micro.postinstall_check.passed()
True
>>>  i = tflite_micro.runtime.Interpreter.from_file("foo.tflite")
>>> # 等等。
>>> # etc.
```

## 构建并上传到 PyPI
## Building and uploading to PyPI

上述生成的 *.whl* 不适合通过 PyPI 分发给更广泛的世界。扩展模块不可避免地针对特定的 Python 实现和平台 C 库进行编译。生成的包仅与运行相同 Python 实现和兼容（通常相同或更新）C 库的系统二进制兼容。
The *.whl* generated above is unsuitable for distribution to the wider world
via PyPI. The extension module is inevitably compiled against a particular
Python implementation and platform C library. The resulting package is only
binary-compatible with a system running the same Python implementation and a
compatible (typically the same or newer) C library.

解决方案是分发多个 *.whl*，每个针对特定的 Python 实现和平台组合构建。TFLM 通过从多个唯一配置的 Docker 容器中运行 Bazel 构建来实现这一点。使用的镜像基于 Python 包权威机构 (PyPA) 发布的符合标准的镜像，专门用于此类用途。
The solution is to distribute multiple *.whl*s, one built for each Python
implementation and platform combination. TFLM accomplishes this by running
Bazel builds from within multiple, uniquely configured Docker containers. The
images used are based on standards-conforming images published by the Python
Package Authority (PyPA) for exactly such use.

Python *.whl* 包含由安装程序（如 `pip`）使用的元数据，以确定哪些发行版（*.whl*）与目标平台兼容。请参阅 PyPA 关于[平台兼容性标签](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/)的规范。
Python *.whl*s contain metadata used by installers such as `pip` to determine
which distributions (*.whl*s) are compatible with the target platform. See the PyPA
specification for [platform compatibility
tags](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/).

### 构建
### Building

在具有工作 Docker 安装的环境中，为每个标签运行一次脚本 `python/tflite_micro/pypi_build.sh <python-tag>`。脚本的在线帮助 (`--help`) 列出了可用的标签。该脚本构建一个适当的 Docker 容器，并在其中调用 Bazel 构建和测试。例如：
In an environment with a working Docker installation, run the script
`python/tflite_micro/pypi_build.sh <python-tag>` once for each tag. The
script's online help (`--help`) lists the available tags. The script builds an
appropriate Docker container and invokes a Bazel build and test within it.
For example:

```
% python/tflite_micro/pypi_build.sh cp310
[+] Building 2.6s (7/7) FINISHED
=> writing image sha256:900704dad7fa27938dcc1c5057c0e760fb4ab0dff676415182455ae66546bbd4
bazel build //python/tflite_micro:whl.dist \
    --//python/tflite_micro:compatibility_tag=cp310_cp310_manylinux_2_28_x86_64
bazel test //python/tflite_micro:whl_test \
    --//python/tflite_micro:compatibility_tag=cp310_cp310_manylinux_2_28_x86_64
//python/tflite_micro:whl_test
Executed 1 out of 1 test: 1 test passes.
Output:
bazel-pypi-out/tflite_micro-0.dev20230920031310-cp310-cp310-manylinux_2_28_x86_64.whl
```

默认情况下，*.whl* 在输出目录 `bazel-pypi-out/` 下生成。
By default, *.whl*s are generated under the output directory `bazel-pypi-out/`.

### 上传到 PyPI
### Uploading to PyPI

使用脚本 `python/tflite_micro/pypi_upload.sh` 将生成的 *.whl* 上传到 PyPI。此脚本轻度包装了标准上传工具 `twine`。必须将 PyPI 身份验证令牌分配给环境变量 `TWINE_PASSWORD`。
Upload the generated *.whl*s to PyPI with the script
`python/tflite_micro/pypi_upload.sh`. This script lightly wraps the standard
upload tool `twine`. A PyPI authentication token must be assigned to the
environment variable `TWINE_PASSWORD`.