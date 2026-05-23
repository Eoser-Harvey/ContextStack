<!-- mdformat off(b/169948621#comment2) -->

# 通用 Cortex-Mx 自定义

自定义需要定义调试日志的输出位置。通用 Cortex-Mx 目标的目的是生成一个 TFLM 库文件，供此仓库外部的应用程序项目使用。由于芯片 HAL 和板级特定层仅在应用程序项目中定义，TFLM 库无法将调试日志写入任何位置。相反，我们允许应用程序层注册一个回调函数来写入 TFLM 内核调试日志。

# 用法

请参阅 debug_log_callback.h

# 如何构建

必需参数：

  - TARGET: cortex_m_generic
  - TARGET_ARCH: cortex-mXX 有关所有选项，请参阅：[链接](https://github.com/tensorflow/tflite-micro/tree/main/tensorflow/lite/micro/tools/make/targets/cortex_m_generic_makefile.inc)

可选参数：

  - TOOLCHAIN: gcc（默认）或 armclang
  - 对于 Cortex-M55，需要 ARM Compiler 6.14 或更高版本。

一些示例：

使用 arm-gcc 构建

```
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_generic TARGET_ARCH=cortex-m7 microlite
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_generic TARGET_ARCH=cortex-m7 OPTIMIZED_KERNEL_DIR=cmsis_nn microlite

make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_generic TARGET_ARCH=cortex-m4 OPTIMIZED_KERNEL_DIR=cmsis_nn microlite
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_generic TARGET_ARCH=cortex-m4+fp OPTIMIZED_KERNEL_DIR=cmsis_nn microlite
```

使用 armclang 构建

```
make -f tensorflow/lite/micro/tools/make/Makefile TOOLCHAIN=armclang TARGET=cortex_m_generic TARGET_ARCH=cortex-m55 microlite
make -f tensorflow/lite/micro/tools/make/Makefile TOOLCHAIN=armclang TARGET=cortex_m_generic TARGET_ARCH=cortex-m55 OPTIMIZED_KERNEL_DIR=cmsis_nn microlite
make -f tensorflow/lite/micro/tools/make/Makefile TOOLCHAIN=armclang TARGET=cortex_m_generic TARGET_ARCH=cortex-m55+nofp OPTIMIZED_KERNEL_DIR=cmsis_nn microlite
```

Tensorflow Lite Micro makefile 将特定版本的 arm-gcc 编译器下载到 tensorflow/lite/micro/tools/make/downloads/gcc_embedded。

如果需要，可以通过向 Makefile 提供 `TARGET_TOOLCHAIN_ROOT` 选项来使用不同版本：

```
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_generic TARGET_ARCH=cortex-m4+fp TARGET_TOOLCHAIN_ROOT=/path/to/arm-gcc/ microlite
```

类似地，`OPTIMIZED_KERNEL_DIR=cmsis_nn` 将特定版本的 CMSIS 下载到 tensorflow/lite/micro/tools/make/downloads/cmsis。虽然这是定期测试的唯一版本，但您也可以通过向 Makefile 提供 `CMSIS_PATH` 来使用自己的 CMSIS 版本：

```
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_generic TARGET_ARCH=cortex-m4+fp OPTIMIZED_KERNEL_DIR=cmsis_nn CMSIS_PATH=/path/to/own/cmsis microlite
```