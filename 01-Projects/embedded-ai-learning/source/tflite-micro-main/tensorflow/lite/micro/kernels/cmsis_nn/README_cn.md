<!-- mdformat off(b/169948621#comment2) -->

# 通用信息
CMSIS-NN 是一个包含 Arm(R) Cortex(R)-M 处理器内核优化的库。要使用 CMSIS-NN 优化内核代替参考内核，请在 make 命令行中添加 `OPTIMIZED_KERNEL_DIR=cmsis_nn`。请参见以下示例。

有关优化的更多信息，请查看 [CMSIS-NN 文档](https://github.com/ARM-software/CMSIS-NN/blob/main/README.md)。

# 指定 CMSIS-NN 路径

默认情况下，CMSIS-NN 由下载到 TFLM 树的代码构建。也可以通过指定 CMSIS_PATH=<../path> 和 CMSIS_NN_PATH=<../path> 从外部路径构建 CMSIS-NN 代码。请注意，需要同时指定 CMSIS_PATH 和 CMSIS_NN_PATH，因为 CMSIS-NN 依赖于 CMSIS-Core。作为第三种选择，CMSIS-NN 可以作为外部库手动提供。以下示例将说明这一点。

# 指定 Cortex_DFP 路径

使用的 Cortex_DFP 路径可以使用附加标志 `CORTEX_DFP_PATH=<path/to>cmsis/Cortex_DFP` 指定。默认是下载的 CMSIS 版本中包含的 Cortex_DFP。

## 示例 - 基于 Arm Corstone-300 软件的 FVP。
在此示例中，构建了内核卷积单元测试。有关此特定目标的更多信息，请查看 [Corstone-300 readme](https://github.com/tensorflow/tflite-micro/tree/main/tensorflow/lite/micro/cortex_m_corstone_300/README.md)。

构建下载的 CMSIS-NN 代码：
```
make -f tensorflow/lite/micro/tools/make/Makefile OPTIMIZED_KERNEL_DIR=cmsis_nn TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 kernel_conv_test
```

构建外部 CMSIS-NN 代码：
```
make -f tensorflow/lite/micro/tools/make/Makefile OPTIMIZED_KERNEL_DIR=cmsis_nn CMSIS_PATH=<external/path/to/cmsis/> CMSIS_NN_PATH=<external/path/to/cmsis-nn/>  TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 kernel_conv_test
```

链接外部 CMSIS-NN 库：
```
make -f tensorflow/lite/micro/tools/make/Makefile OPTIMIZED_KERNEL_DIR=cmsis_nn CMSIS_NN_LIBS=<path/to/cmsis-nn.a> CMSIS_PATH=<path/to/cmsis/> TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 kernel_conv_test
```

请注意，使用外部 CMSIS-NN 库时，性能和/或大小可能会受到影响，因为可能使用了不同的编译器选项。

另请注意，如果指定 CMSIS_NN_LIBS 但未指定 CMSIS_PATH 和/或 CMSIS_NN_PATH，将使用默认下载路径的 CMSIS 中的头文件和系统/启动代码。因此 CMSIS_NN_LIBS、CMSIS_NN_PATH 和 CMSIS_PATH 应具有相同的基本路径，否则将出现构建错误。

# 为速度或大小构建
可以为速度或大小构建。对于内存有限的嵌入式系统上的大型模型，可能需要大小选项。在适用的情况下，为大小构建将导致更高的延迟和较小的暂存缓冲区，而为速度构建将导致较低的延迟和较大的暂存缓冲区。目前仅转置卷积支持此功能。请参见以下示例。

## 示例 - 使用 CMSIS-NN 优化内核构建静态库
有关此示例中使用的目标的更多信息：https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/cortex_m_generic/README.md

为速度构建（默认）：
请注意，速度是默认值，因此如果完全省略 OPTIMIZE_KERNELS_FOR，那将是默认值。
```
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_generic TARGET_ARCH=cortex-m55 OPTIMIZED_KERNEL_DIR=cmsis_nn OPTIMIZE_KERNELS_FOR=KERNELS_OPTIMIZED_FOR_SPEED microlite

```

为大小构建：
```
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=cortex_m_generic TARGET_ARCH=cortex-m55 OPTIMIZED_KERNEL_DIR=cmsis_nn OPTIMIZE_KERNELS_FOR=KERNELS_OPTIMIZED_FOR_SIZE microlite

```