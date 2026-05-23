<!--ts-->
<!-- 翻译：AI助手，于 2026年5月12日 -->
<!--te-->

# 为 Synopsys DesignWare ARC VPX 和 EM/HS 处理器构建 TensorFlow Lite for Microcontrollers
# Building TensorFlow Lite for Microcontrollers for Synopsys DesignWare ARC VPX and EM/HS Processors

## 维护者
## Maintainers

*   [dzakhar](https://github.com/dzakhar)
*   [JaccovG](https://github.com/JaccovG)
*   [gerbauz](https://github.com/gerbauz)

## 介绍
## Introduction

本文档包含有关为基于 Synopsys ARC VPX 和 EM/HS 处理器的目标构建和运行 TensorFlow Lite Micro 的一般信息。
This document contains the general information on building and running
TensorFlow Lite Micro for targets based on the Synopsys ARC VPX and EM/HS Processors.

## 目录
## Table of Contents

-   [安装 Synopsys DesignWare ARC MetaWare 开发工具包](#安装-synopsys-designware-arc-metaware-开发工具包)
-   [Install the Synopsys DesignWare ARC MetaWare Development Toolkit](#install-the-synopsys-designware-arc-metaWare-development-toolkit)
-   [ARC EM 软件开发平台 (ARC EM SDP)](#arc-em-软件开发平台-arc-em-sdp)
-   [ARC EM Software Development Platform (ARC EM SDP)](#ARC-EM-Software-Development-Platform-ARC-EM-SDP)
-   [使用 EmbARC MLI 库 2.0（实验性功能）](#使用-embarc-mli-库-20实验性功能)
-   [Using EmbARC MLI Library 2.0 (experimental feature)](#Using-EmbARC-MLI-Library-2.0-experimental-feature)
-   [模型适配工具（实验性功能）](#模型适配工具实验性功能)
-   [Model Adaptation Tool (experimental feature)](#Model-Adaptation-Tool-experimental-feature)
-   [自定义 ARC EM/HS/VPX 平台](#自定义-arc-emhsvpx-平台)
-   [Custom ARC EM/HS/VPX Platform](#Custom-ARC-EMHSVPX-Platform)

## 安装 Synopsys DesignWare ARC MetaWare 开发工具包
## Install the Synopsys DesignWare ARC MetaWare Development Toolkit

Synopsys DesignWare ARC MetaWare 开发工具包 (MWDT) 是为所有 ARC VPX 和 EM/HS 目标构建和运行 Tensorflow Lite Micro 应用程序所必需的。
The Synopsys DesignWare ARC MetaWare Development Toolkit (MWDT) is required to
build and run Tensorflow Lite Micro applications for all ARC VPX and EM/HS targets.

要许可 MWDT，请参阅[此处](https://www.synopsys.com/dw/ipdir.php?ds=sw_metaware)的详细信息。
To license MWDT, please see further details
[here](https://www.synopsys.com/dw/ipdir.php?ds=sw_metaware)

要请求 MWDT 的评估版本，请使用[Synopsys 评估门户](https://eval.synopsys.com/)并遵循 MetaWare 开发工具包的链接（重要：不要与此页面上也提供的 MetaWare EV 开发工具包或 MetaWare Lite 选项混淆）。
To request an evaluation version of MWDT, please use the
[Synopsys Eval Portal](https://eval.synopsys.com/) and follow the link for the
MetaWare Development Toolkit (Important: Do not confuse this with MetaWare EV
Development Toolkit or MetaWare Lite options also available on this page)

运行下载的安装程序并按照说明在您的平台上设置工具链。
Run the downloaded installer and follow the instructions to set up the toolchain
on your platform.

TensorFlow Lite for Microcontrollers 构建分为两个阶段：应用程序项目生成和应用程序项目构建/运行。前一个阶段需要 *nix 环境，而后一个阶段则不需要。
TensorFlow Lite for Microcontrollers builds are divided into two phases:
Application Project Generation and Application Project Building/Running. The
former phase requires \*nix environment while the latter does not.

针对[ARC EM 软件开发平台](#ARC-EM-Software-Development-Platform-ARC-EM-SDP)的基本项目生成，项目生成阶段不需要 MetaWare。但是，在以下情况下需要 MetaWare：- 为自定义（非 EM SDP）目标生成项目 - 构建包含所有所需 TFLM 对象的微库目标库以供外部使用。
For basic project generation targeting
[ARC EM Software Development Platform](#ARC-EM-Software-Development-Platform-ARC-EM-SDP),
MetaWare is NOT required for the Project Generation Phase. However, it is
required in case the following: - For project generation for custom (not EM SDP)
targets - To build microlib target library with all required TFLM objects for
external use

请根据上述情况选择是安装 Windows 还是 Linux 或两者版本的 MWDT。
Please consider the above when choosing whether to install Windows or Linux or
both versions of MWDT.

## ARC EM 软件开发平台 (ARC EM SDP)
## ARC EM Software Development Platform (ARC EM SDP)

本节介绍如何在[ARC EM SDP 板](https://www.synopsys.com/dw/ipdir.php?ds=arc-em-software-development-platform)上部署。
This section describes how to deploy on an
[ARC EM SDP board](https://www.synopsys.com/dw/ipdir.php?ds=arc-em-software-development-platform).

### 初始设置
### Initial Setup

要使用 EM SDP，您需要以下硬件和软件：
To use the EM SDP, you need the following hardware and software:

#### ARC EM SDP
#### ARC EM SDP

有关该平台的更多信息，包括订购信息，请参阅[此处](https://www.synopsys.com/dw/ipdir.php?ds=arc-em-software-development-platform)。
More information on the platform, including ordering information, can be found
[here](https://www.synopsys.com/dw/ipdir.php?ds=arc-em-software-development-platform).

#### MetaWare 开发工具包
#### MetaWare Development Toolkit

有关工具链安装说明，请参阅[安装 Synopsys DesignWare ARC MetaWare 开发工具包](#install-the-synopsys-designware-arc-metaware-development-toolkit)部分。
See
[Install the Synopsys DesignWare ARC MetaWare Development Toolkit](#install-the-synopsys-designware-arc-metaWare-development-toolkit)
section for instructions on toolchain installation.

#### Digilent Adept 2 系统软件包
#### Digilent Adept 2 System Software Package

如果您希望使用 MetaWare 调试器调试代码，还需要安装 Digilent Adept 2 软件，其中包括连接到目标所需的驱动程序。这可以从官方[Digilent 网站](https://reference.digilentinc.com/reference/software/adept/start?redirect=1#software_downloads)获得。您应该安装“系统”组件和运行时。不需要实用程序和 SDK。
If you wish to use the MetaWare Debugger to debug your code, you need to also
install the Digilent Adept 2 software, which includes the necessary drivers for
connecting to the targets. This is available from official
[Digilent site](https://reference.digilentinc.com/reference/software/adept/start?redirect=1#software_downloads).
You should install the "System" component, and Runtime. Utilities and SDK are
NOT required.

如果您计划通过 SD 卡部署到 EM SDP，而不是使用调试器，则不需要 Digilent 安装。
Digilent installation is NOT required if you plan to deploy to EM SDP via the SD
card instead of using the debugger.

#### Make 工具
#### Make Tool

部署 Tensorflow Lite Micro 应用程序在 ARC EM SDP 上的两个阶段都需要 `'make'` 工具：1. 测试二进制文件生成。2. TFLM 静态库生成。
A `'make'` tool is required for both phases of deploying Tensorflow Lite Micro
applications on ARC EM SDP: 
1. Test binaries generation.
2. TFLM static library generation.

对于第一阶段，您需要一个与 Tensorflow Lite for Micro 构建系统兼容的环境和 make 工具。在撰写本文时，这需要 make >=3.82 和支持 shell 和文件操作本机命令的 *nix 类环境。此阶段不需要 MWDT 工具包。
For the first phase you need an environment and make tool compatible with
Tensorflow Lite for Micro build system. At the moment of this writing, this
requires make >=3.82 and a *nix-like environment which supports shell and native
commands for file manipulations. MWDT toolkit is not required for this phase.

对于第二阶段，要求不那么严格。MetaWare 开发工具包提供的 gmake 版本就足够了。没有 shell 和 *nix 命令依赖，因此可以使用 Windows。
For the second phase, requirements are less strict. The gmake version delivered
with MetaWare Development Toolkit is sufficient. There are no shell and *nix
command dependencies, so Windows can be used.

#### 串行终端仿真应用程序
#### Serial Terminal Emulation Application

EM SDP 的调试 UART 端口用于打印应用程序输出。USB 连接同时提供调试通道和 RS232 传输。您可以使用任何终端仿真程序（如 [PuTTY](https://www.putty.org/)）来查看来自 EM SDP 的 UART 输出。
The Debug UART port of the EM SDP is used to print application output. The USB
connection provides both the debug channel and RS232 transport. You can use any
terminal emulation program (like [PuTTY](https://www.putty.org/)) to view UART
output from the EM SDP.

#### microSD 卡
#### microSD Card

如果您希望自启动应用程序（独立于调试器连接启动它），还需要一个容量至少为 512 MB 的 microSD 卡以及一种从开发主机写入卡的方法。请注意，该卡必须格式化为 FAT32，簇大小为默认值（但小于 32 Kbytes）。
If you want to self-boot your application (start it independently from a
debugger connection), you also need a microSD card with a minimum size of 512 MB
and a way to write to the card from your development host. Note that the card
must be formatted as FAT32 with default cluster size (but less than 32 Kbytes).

### 连接开发板
### Connect the Board

1.  确保开发板的启动开关 (S3) 按以下方式配置：
1.  Make sure Boot switches of the board (S3) are configured in the next way:

开关编号 | 开关位置
Switch # | Switch position
:------: | :-------------:
1        | 低 (0)
1        | Low (0)
2        | 低 (0)
2        | Low (0)
3        | 高 (1)
3        | High (1)
4        | 低 (0)
4        | Low (0)

1.  将产品包装中包含的电源连接到 ARC EM SDP。
1.  Connect the power supply included in the product package to the ARC EM SDP.
2.  将 USB 电缆连接到 ARC EM SDP 上的连接器 J10（靠近 RST 和 CFG 按钮）以及开发主机上可用的 USB 端口。
2.  Connect the USB cable to connector J10 on the ARC EM SDP (near the RST and
    CFG buttons) and to an available USB port on your development host.
3.  确定分配给 USB 串行端口的 COM 端口（在 Windows 上，使用设备管理器是一种简单的方法）。
3.  Determine the COM port assigned to the USB Serial Port (on Windows, using
    Device Manager is an easy way to do this)
4.  执行您在上一步安装的串行终端应用程序，并使用早期定义的 COM 端口打开串行连接（速度 115200 波特；8 位；1 停止位；无奇偶校验）。
4.  Execute the serial terminal application you installed in the previous step
    and open the serial connection with the early defined COM port (speed 115200
    baud; 8 bits; 1 stop bit; no parity).
5.  按下开发板上的 CFG 按钮。几秒钟后，您应该在终端中看到启动日志，该日志开始如下：
5.  Push the CFG button on the board. After a few seconds you should see the
    boot log in the terminal which begins as follows:

```
U-Boot <版本信息>
U-Boot <Versioning info>

CPU:   ARC EM11D v5.0 at 40 MHz
Subsys:ARC 数据融合 IP 子系统
Subsys:ARC Data Fusion IP Subsystem
Model: snps,emsdp
Board: ARC EM 软件开发平台 v1.0
Board: ARC EM Software Development Platform v1.0
…
```

### 为 ARC EM SDP 生成 TFLM 静态库
### Generate TFLM as Static Library for ARC EM SDP

如果您希望在您自己的应用程序中使用 TensorFlow Lite Micro 框架，您需要将 TFLM 生成为静态库。可以使用以下命令为 ARC EM SDP 生成 TFLM 库：
If you want to use TensorFlow Lite Micro framework in your own application, you need to generate TFLM as a static library.
Next command can be used to generate TFLM library for ARC EM SDP:

```bash
make -f tensorflow/lite/micro/tools/make/Makefile clean
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=arc_emsdp \ 
TARGET_ARCH=arc \
OPTIMIZED_KERNEL_DIR=arc_mli \
microlite
```

生成的库 *libtensorflow-microlite.a* 可以在 *gen/{target}/lib* 中找到。
Generated library *libtensorflow-microlite.a* can be found in *gen/{target}/lib*.

### ARC EM SDP 的示例应用程序
### Example Applications for ARC EM SDP

示例应用程序可以在 ARC 示例仓库中找到。
Example applications can be found on ARC examples repository.

## 使用 EmbARC MLI 库 2.0（实验性功能）
## Using EmbARC MLI Library 2.0 (experimental feature)

本节介绍如何使用 [embARC MLI 库 2.0](https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_mli/tree/Release_2.0_EA) 构建 TFLM。
This section describes how to build TFLM using [embARC MLI Library 2.0](https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_mli/tree/Release_2.0_EA). 

EmbARC MLI 库 2.0 可用于构建 TFLM 库和运行应用程序（特别是对于 VPX 处理器）。
The EmbARC MLI Library 2.0 can be used to build TFLM library and run applications (especially for VPX processors).

由于权重布局的差异，TFLM 模型必须使用模型适配工具进行预适配。对于本机 TFLM 示例（人员检测、微型语音），当使用 MLI 2.0 时，模型适配工具会自动应用，因此无需手动运行它。
Because of difference in weights layout, TFLM models must be pre-adapted using a Model Adaptation Tool. For native TFLM examples (person detection, micro speech) Model Adaptation Tool is applied automatically when MLI 2.0 is used, so there is no need to run it maually.

要在所有情况下（包括本机示例）使用 embARC MLI 库 2.0，您还需要模型适配工具的额外依赖项。请查看[模型适配工具](#​Model-Adaptation-Tool-experimental-​feature)部分以获取更多信息。
To use the embARC MLI Library 2.0 in all cases (including native examples), you will also need extra dependencies for the Model Adaptation Tool. Please check the [Model Adaptation Tool](#​Model-Adaptation-Tool-experimental-​feature) section for more information.

要使用 embARC MLI 库 2.0 构建 TFLM，请将以下标签添加到命令中：
To build TFLM using the embARC MLI Library 2.0, add the following tag to the command:

```bash
ARC_TAGS=mli20_experimental
```

此外，某些配置可能需要自定义 BUILD_LIB。请查看 MLI 库 2.0 [文档](https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_mli/tree/Release_2.0_EA#build-configuration-options)以获取更多详细信息。可以添加以下选项：
Also, some of configurations may require custom BUILD_LIB. Please, check MLI Library 2.0 [documentation](https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_mli/tree/Release_2.0_EA#build-configuration-options) for more details. Following option can be added:

```bash
BUILD_LIB_DIR=<path_to_buildlib>
```

为 VPX5 构建 TFLM 库的命令示例：
Example of command to build TFLM lib for VPX5:

```bash
make -f tensorflow/lite/micro/tools/make/Makefile \
TARGET=arc_custom \
TCF=<path_to_tcf_file> \
BUILD_LIB_DIR=vpx5_integer_full \
ARC_TAGS=mli20_experimental microlite
```

## 模型适配工具（实验性功能）
## Model Adaptation Tool (experimental feature)

由于某些内核中权重张量布局的差异，TFLM 格式的模型需要在使用 MLI 2.0 之前进行预适配。适配在 TFLM 项目生成期间自动完成，但需要安装 TensorFlow。
Models in TFLM format need to be pre-adapted before being used with MLI 2.0 due to differences in weights' tensor layout in some kernels. Adaptation is done automatically during TFLM project generation, but requires TensorFlow to be installed.

要使用模型适配工具，除了常见要求外，还需要以下工具：
To use the Model Adaptation Tool, you need the following tools in addition to common requirments:
* [Python](https://www.python.org/downloads/) 3.7 或更高版本
* [Python](https://www.python.org/downloads/) 3.7 or higher
* [TensorFlow for Python](https://www.tensorflow.org/install/pip) 版本 2.5 或更高版本
* [TensorFlow for Python](https://www.tensorflow.org/install/pip) version 2.5 or higher

如果您希望使用从 TensorFlow 导出的自己的模型，格式为 **.tflite** 或 **.cc**，您将需要使用当前文件夹中的模型适配工具手动适配它，使用以下命令：
If you want to use your own model, exported from TensorFlow in **.tflite** or **.cc** format, you will need to adapt it manually using the Model Adaptation Tool from the current folder, using the following command:

```bash
python adaptation_tool.py <path_to_input_model_file> \
<path_to_adapted_model_file>
```

## 自定义 ARC EM/HS/VPX 平台
## Custom ARC EM/HS/VPX Platform

本节介绍如何部署到仅由 TCF（工具配置文件，在 CPU 配置时创建）和可选的 LCF（链接器命令文件）定义的自定义 ARC VPX 或 EM/HS 平台。在这种情况下，实际硬件未知，应用程序只能在 MetaWare 工具包中包含的 nSIM 模拟器中运行。
This section describes how to deploy on a Custom ARC VPX or EM/HS platform defined only by a TCF (Tool onfiguration File, created at CPU configuration time) and optional LCF (Linker Command File). In this case, the real hardware is unknown, and applications can be run only in the nSIM simulator included with the MetaWare toolkit.

VPX 支持作为支持 embARC MLI 库版本 2.0 和模型适配的实验性功能呈现。有关 embARC MLI 库 2.0 支持的更多信息，请参阅[相关部分](#Using-EmbARC-MLI-Library-2.0-experimental-feature)。
VPX support is presented as an experimental feature of supporting embARC MLI Library version 2.0 and model adaptation. Read more about embARC MLI Library 2.0 support in the [related section](#Using-EmbARC-MLI-Library-2.0-experimental-feature).

### 初始设置
### Initial Setup

要使用自定义 ARC EM/HS/VPX 平台，您需要以下内容：* Synopsys MetaWare 开发工具包版本 2019.12 或更高（对于 MLI 库 2.0 需要 2021.06 或更高）* Make 工具（make 或 gmake）* CMake 3.18 或更高\如果您使用[模型适配工具](#Model-Adaptation-Tool-experimental-feature)，您还需要安装：* [Python](https://www.python.org/downloads/) 3.7 或更高版本 * [TensorFlow for Python](https://www.tensorflow.org/install/pip) 版本 2.5 或更高版本。
To use a custom ARC EM/HS/VPX platform, you need the following : 
* Synopsys MetaWare
Development Toolkit version 2019.12 or higher (2021.06 or higher for MLI Library 2.0) 
* Make tool (make or gmake)
* CMake 3.18 or higher\
If you are using the [Model Adaptation Tool](#Model-Adaptation-Tool-experimental-feature), you will also need to install:
* [Python](https://www.python.org/downloads/) 3.7 or higher
* [TensorFlow for Python](https://www.tensorflow.org/install/pip) version 2.5 or higher

有关工具链安装说明，请参阅[安装 Synopsys DesignWare ARC MetaWare 开发工具包](#install-the-synopsys-designware-arc-metaware-development-toolkit)部分。有关工具链安装和 make 版本的注释，请参阅[MetaWare 开发工具包](#MetaWare-Development-Toolkit)和[Make 工具](#Make-Tool)部分。
See
[Install the Synopsys DesignWare ARC MetaWare Development Toolkit](#install-the-synopsys-designware-arc-metaWare-development-toolkit)
section for instructions on toolchain installation. See
[MetaWare Development Toolkit](#MetaWare-Development-Toolkit) and
[Make Tool](#Make-Tool) sections for instructions on toolchain installation and
comments about make versions.

### 生成 TFLM 静态库
### Generate TFLM as Static Library

如果您希望在您自己的应用程序中使用 TensorFlow Lite Micro 框架，您需要将 TFLM 生成为静态库。可以使用以下命令生成 TFLM 库：
If you want to use TensorFlow Lite Micro framework in your own application, you need to generate TFLM as a static library.
Next command can be used to generate TFLM library:

```bash
make -f tensorflow/lite/micro/tools/make/Makefile clean
make -f tensorflow/lite/micro/tools/make/Makefile \
TARGET_ARCH=arc \
TARGET=arc_custom \
OPTIMIZED_KERNEL_DIR=arc_mli \
TCF_FILE=<path_to_tcf_file> \
LCF_FILE=<path_to_lcf_file> \
microlite
```

对于 MLI 库 2.0（实验性功能）：
For MLI Library 2.0 (experimental feature):

```bash
make -f tensorflow/lite/micro/tools/make/Makefile clean
make -f tensorflow/lite/micro/tools/make/Makefile \
TARGET_ARCH=arc \
TARGET=arc_custom \
OPTIMIZED_KERNEL_DIR=arc_mli \
ARC_TAGS=mli20_experimental \
BUILD_LIB_DIR=<path_to_buildlib> \
TCF_FILE=<path_to_tcf_file> \
microlite
```

生成的库 *libtensorflow-microlite.a* 可以在 *gen/{target}/lib* 中找到。
Generated library *libtensorflow-microlite.a* can be found in *gen/{target}/lib*.

### ARC EM/HS/VPX 自定义配置的示例应用程序。
### Example Applications for ARC EM/HS/VPX custom configuration.

示例应用程序可以在 ARC 示例仓库中找到。
Example applications can be found on ARC examples repository.

## 许可证
## License

TensorFlow 的代码由存储库中包含的 Apache2 许可证涵盖，第三方依赖项由它们各自的许可证涵盖，位于此包的 third_party 文件夹中。
TensorFlow's code is covered by the Apache2 License included in the repository,
and third-party dependencies are covered by their respective licenses, in the
third_party folder of this package.