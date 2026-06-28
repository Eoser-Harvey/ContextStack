<!-- 翻译：AI助手，于 2026年5月13日 -->
<!-- 格式：中英文对照，便于学习 -->

# TFLite for Microcontrollers 基准测试
# TFLite for Microcontrollers Benchmarks

这些基准测试用于测量关键模型和工作负载的性能。它们旨在作为给定平台模型优化过程的一部分。
These benchmarks are for measuring the performance of key models and workloads.
They are meant to be used as part of the model optimization process for a given
platform.

## 目录
## Table of contents

-   [关键词基准测试](#keyword-benchmark)
-   [Keyword Benchmark](#keyword-benchmark)
-   [人员检测基准测试](#person-detection-benchmark)
-   [Person Detection Benchmark](#person-detection-benchmark)
-   [在 x86 上运行](#run-on-x86)
-   [Run on x86](#run-on-x86)
-   [在 Xtensa XPG 模拟器上运行](#run-on-xtensa-xpg-simulator)
-   [Run on Xtensa XPG Simulator](#run-on-xtensa-xpg-simulator)
-   [在 Sparkfun Edge 上运行](#run-on-sparkfun-edge)
-   [Run on Sparkfun Edge](#run-on-sparkfun-edge)
-   [在基于 Arm Corstone-300 软件的 FVP 上运行](#run-on-fvp-based-on-arm-corstone-300-software)
-   [Run on FVP based on Arm Corstone-300 software](#run-on-fvp-based-on-arm-corstone-300-software)

## 关键词基准测试
## Keyword benchmark

关键词基准测试包含一个带有加扰权重和偏置的关键词检测模型。该模型仅用于测试平台性能。由于权重被加扰，输出是无意义的。为了验证优化内核的准确性，请运行内核测试。
The keyword benchmark contains a model for keyword detection with scrambled
weights and biases.  This model is meant to test performance on a platform only.
Since the weights are scrambled, the output is meaningless. In order to validate
the accuracy of optimized kernels, please run the kernel tests.

## 人员检测基准测试
## Person detection benchmark

关键词基准测试提供了一种评估 250KB 视觉唤醒词模型性能的方法。
The keyword benchmark provides a way to evaluate the performance of the 250KB
visual wakewords model.

## 在 x86 上运行
## Run on x86

要在 x86 上运行关键词基准测试，请运行：
To run the keyword benchmark on x86, run

```
make -f tensorflow/lite/micro/tools/make/Makefile run_keyword_benchmark
```

要在 x86 上运行人员检测基准测试，请运行：
To run the person detection benchmark on x86, run

```
make -f tensorflow/lite/micro/tools/make/Makefile run_person_detection_benchmark
```

## 在 Xtensa XPG 模拟器上运行
## Run on Xtensa XPG Simulator

要在 Xtensa XPG 模拟器上运行关键词基准测试，您需要有效的 Xtensa 工具链和许可证。设置完成后，运行：
To run the keyword benchmark on the Xtensa XPG simulator, you will need a valid
Xtensa toolchain and license.  With these set up, run:

```
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=xtensa OPTIMIZED_KERNEL_DIR=xtensa TARGET_ARCH=<target architecture> XTENSA_CORE=<xtensa core> run_keyword_benchmark -j18
```

## 在 Sparkfun Edge 上运行
## Run on Sparkfun Edge

以下说明将帮助您在 [SparkFun Edge 开发板](https://sparkfun.com/products/15170) 上构建和部署此基准测试。
The following instructions will help you build and deploy this benchmark on the
[SparkFun Edge development board](https://sparkfun.com/products/15170).

如果您是第一次使用此开发板，我们建议您逐步完成 [在微控制器上使用 TensorFlow Lite 和 SparkFun Edge 进行 AI](https://codelabs.developers.google.com/codelabs/sparkfun-tensorflow) 代码实验室，以了解工作流程。
If you're new to using this board, we recommend walking through the
[AI on a microcontroller with TensorFlow Lite and SparkFun Edge](https://codelabs.developers.google.com/codelabs/sparkfun-tensorflow)
codelab to get an understanding of the workflow.

使用以下命令构建二进制文件：
Build binary using

```
make -f tensorflow/lite/micro/tools/make/Makefile TARGET=sparkfun_edge person_detection_benchmark_bin
```

请参考 [人员检测示例](https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/examples/person_detection/README.md#running-on-sparkfun-edge) 中的烧录说明。
Refer to flashing instructions in the [Person Detection Example](https://github.com/tensorflow/tflite-micro/blob/main/tensorflow/lite/micro/examples/person_detection/README.md#running-on-sparkfun-edge).

## 在基于 Arm Corstone-300 软件的 FVP 上运行
## Run on FVP based on Arm Corstone-300 software

有关 Corstone-300 软件的更多信息，请参阅：
For more info about the Corstone-300 software see:
[tensorflow/lite/micro/cortex_m_corstone_300/README.md](../cortex_m_corstone_300/README.md).

免责声明：FVP 不能用于测量 CPU 性能。结果不可靠，甚至对于相对测量也是如此。然而，当在 NPU 上运行时，FVP 可用于性能测量，并且只能使用 NPU PMU 数字。NPU 模型在约 +-10% 范围内是周期精确的。
Disclaimer: The FVP can not be used to measure CPU performance.
The results are not reliable, not even for relative measurements.
FVP may however be used for performance measurements when running on NPU and only NPU PMU numbers can be used. The NPU model is cycle accurate within approximately +-10%.

例如，下载的人员检测模型将针对 Ethos-U 进行优化。更多信息请参阅：
As an example, the person detect downloaded model will be optimized for Ethos-U. For more info see:
[tensorflow/lite/micro/kernels/ethos_u/README.md](../kernels/ethos_u/README.md).
由于只有在 NPU 上测量性能才有意义，因此只应运行人员检测基准测试，并且仅在启用 Ethos-U 时运行。另请参阅网络测试器示例，其中在启用 Ethos-U 时以相同方式使用人员检测模型：
And since it only makes sense to measure performance on the NPU, only the person detection benchmark should be run and only with Ethos-U enabled.
See also network tester example, where person detect model is used in the same way when Ethos-U is enabled: