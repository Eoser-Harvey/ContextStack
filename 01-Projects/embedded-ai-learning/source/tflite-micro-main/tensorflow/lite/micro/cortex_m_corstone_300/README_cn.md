<!-- mdformat off(b/169948621#comment2) -->

# 运行基于 Arm(R) Corstone(TM)-300 软件的固定虚拟平台

此目标使用基于 Arm Corstone-300 软件的固定虚拟平台 (FVP)。
- [有关 Arm Corstone-300 的更多信息](https://developer.arm.com/ip-products/subsystem/corstone/corstone-300)
- [有关 FVP 的更多信息](https://developer.arm.com/tools-and-software/simulation-models/fixed-virtual-platforms)

构建基于 Corstone-300 的目标具有以下依赖项：

-   [Arm Ethos-U 核心平台](https://gitlab.arm.com/artificial-intelligence/ethos-u/ethos-u-core-platform)
    -   Arm Ethos-U 核心平台提供链接器文件以及 UART 和重定向功能。
-   [CMSIS](https://github.com/ARM-software/CMSIS_6) + [CMSIS-Cortex_DFP](https://github.com/ARM-software/Cortex_DFP)
    -   CMSIS 提供启动功能，例如设置中断处理程序和时钟速度。
    -   有关这些如何针对给定示例和 make 目标相互下载，请参阅 cmsis_download.sh。

这两个仓库都由 TFLM 中的构建过程自动下载。

# 通用构建信息

您可以为多个 Cortex-M CPU 编译 Corstone-300 目标。请参见下文。

必需参数：

-   ```TARGET```: cortex_m_corstone_300
-   ```TARGET_ARCH```: cortex-mXX。将 XX 替换为 [Corstone-300 makefile](https://github.com/tensorflow/tflite-micro/tree/main/tensorflow/lite/micro/tools/make/targets/cortex_m_corstone_300_makefile.inc) 中的任一选项。

# 如何运行

请注意，Corstone-300 模拟 Cortex-M55 系统，但它是向后兼容的。这意味着可以运行为例如 Cortex-M7 编译的代码。

一些示例：

```
make -f tensorflow/lite/micro/tools/make/Makefile CO_PROCESSOR=ethos_u TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 test_network_tester_test
make -f tensorflow/lite/micro/tools/make/Makefile OPTIMIZED_KERNEL_DIR=cmsis_nn TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 test_network_tester_test
make -f tensorflow/lite/micro/tools/make/Makefile CO_PROCESSOR=ethos_u OPTIMIZED_KERNEL_DIR=cmsis_nn TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 test_network_tester_test
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 test_network_tester_test
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 test_kernel_fully_connected_test
make -f tensorflow/lite/micro/tools/make/Makefile OPTIMIZED_KERNEL_DIR=cmsis_nn TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m7+fp test_kernel_fully_connected_test
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m3 test_kernel_fully_connected_test
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 BUILD_TYPE=release_with_logs TOOLCHAIN=armclang test_network_tester_test
```