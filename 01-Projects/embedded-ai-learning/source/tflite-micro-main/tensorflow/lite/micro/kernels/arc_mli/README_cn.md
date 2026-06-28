# 基于 EmbARC MLI 库的 TensorFlow Lite Micro 内核优化，适用于 ARC 平台。

## 维护者

*   [dzakhar](https://github.com/dzakhar)
*   [JaccovG](https://github.com/JaccovG)
*   [gerbauz](https://github.com/gerbauz)

## 简介

此文件夹包含使用优化的 [embARC MLI 库](https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_mli) 的内核实现。它允许加速使用 int8（非对称量化）的推理操作。

## 用法

embARC MLI 库用于加速一些非对称量化层的内核执行，可以通过选项 `OPTIMIZED_KERNEL_DIR=arc_mli` 应用。这意味着为 ARC 特定目标生成通常的库意味着使用 embARC MLI。

例如：

```
make -f tensorflow/lite/micro/tools/make/Makefile clean
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=arc_emsdp \
OPTIMIZED_KERNEL_DIR=arc_mli TARGET_ARCH=arc \
microlite
```

如果无法使用 MLI 实现，此文件夹中的内核将回退到 TFLM 参考实现。对于可能无法从 MLI 库受益的应用程序，可以通过**删除**命令行中的 `OPTIMIZED_KERNEL_DIR=arc_mli` 来生成不包含这些实现的 TF Lite Micro 库，这可以减少整体代码大小：

```
make -f tensorflow/lite/micro/tools/make/Makefile clean
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=arc_emsdp \
TARGET_ARCH=arc \
microlite
```
---
### 可选（实验性功能）：

TFLM 可以使用 [embARC MLI 库 2.0](https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_mli/tree/Release_2.0_EA) 作为实验性功能构建。要使用 embARC MLI 库 2.0 构建 TFLM，请将以下标签添加到命令中：
```
ARC_TAGS=mli20_experimental
```
在这种情况下，生成的项目将位于 <tcf_file_basename>_mli20_arc_default 文件夹中。

某些配置可能需要使用 BUILD_LIB_DIR 选项指定的自定义运行时库。请查看 MLI 库 2.0 [文档](https://github.com/foss-for-synopsys-dwc-arc-processors/embarc_mli/tree/Release_2.0_EA#build-configuration-options) 获取更多详细信息。可以添加以下选项：
```
BUILD_LIB_DIR=<path_to_buildlib>
```
## 限制

目前，MLI 库仅针对以下内核的 int8（非对称）版本提供优化实现：
1. 卷积 2D – 仅每轴量化，`dilation_ratio==1`
2. 深度可分离卷积 2D – 仅每轴量化，`dilation_ratio==1`
3. 平均池化
4. 最大池化
5. 全连接

## 暂存缓冲区和切片

以下信息仅适用于 ARC EM SDP、VPX 和其他具有 XY 或 VCCM 内存的目标。embARC MLI 使用特定的优化，假设节点操作数位于 XY、VCCM 内存和/或 DCCM（数据紧密耦合内存）中。由于操作数可能相当大，可能无法适应可用的 XY 或 VCCM 内存，因此应用了特殊的切片逻辑，允许将内核计算拆分为多个部分。为此，在这些 X、Y、VCCM 和 DCCM 内存库中分配了内部静态缓冲区，并用于执行子计算。

所有这些都是自动执行的，对用户不可见。一半的 DCCM 内存库和完整的 XY 库或 3/4 的 VCCM 库被用于 MLI 特定需求。如果用户需要 XY 或 VCCM 内存中的空间用于其他任务，可以通过设置特定大小来减少这些数组。为此，将以下选项添加到构建命令中，将 **<size[a|b|c]>** 替换为所需值：

**对于 EM：**
```
EXT_CFLAGS="-DSCRATCH_MEM_Z_SIZE=<size_a> -DSCRATCH_MEM_X_SIZE=<size_b> -DSCRATCH_MEM_Y_SIZE=<size_c>"
```
**对于 VPX：**
```
EXT_CFLAGS="-DSCRATCH_MEM_VEC_SIZE=<size_a>"
```

例如，要将放置在 DCCM 和 XCCM 中的数组大小分别减少到 32k 和 8k，使用以下命令：

```
make -f tensorflow/lite/micro/tools/make/Makefile <...> \
EXT_CFLAGS="-DSCRATCH_MEM_Z_SIZE=32*1024 -DSCRATCH_MEM_X_SIZE=8*1024" \
microlite
```

## 许可证

TensorFlow 的代码由存储库中包含的 Apache2 许可证覆盖，第三方依赖项由其各自的许可证覆盖，位于此包的 third_party 文件夹中。