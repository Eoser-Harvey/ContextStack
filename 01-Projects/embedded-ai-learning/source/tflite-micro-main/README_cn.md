<!--ts-->
<!-- 翻译：AI助手，于 2026年5月13日 -->
<!-- 格式：中英文对照，便于学习 -->
<!--te-->

# TensorFlow Lite for Microcontrollers (TFLM) 微控制器版
# TensorFlow Lite for Microcontrollers

TensorFlow Lite for Microcontrollers 是 TensorFlow Lite 的一个移植版本，专为在 DSP、微控制器和其他内存有限的设备上运行机器学习模型而设计。
TensorFlow Lite for Microcontrollers is a port of TensorFlow Lite designed to
run machine learning models on DSPs, microcontrollers and other devices with
limited memory.

附加链接：
Additional Links:
 * [TensorFlow GitHub 仓库](https://github.com/tensorflow/tensorflow/)
 * [Tensorflow github repository](https://github.com/tensorflow/tensorflow/)
 * [TFLM 在 tensorflow.org 上的页面](https://www.tensorflow.org/lite/microcontrollers)
 * [TFLM at tensorflow.org](https://www.tensorflow.org/lite/microcontrollers)

# 构建状态
# Build Status

## CI 状态
## CI Status

| 组 | 状态 |
| :--- | :--- |
| 核心 | [![CI](https://github.com/tensorflow/tflite-micro/actions/workflows/run_core.yml/badge.svg)](https://github.com/tensorflow/tflite-micro/actions/workflows/run_core.yml) [![CI](https://github.com/tensorflow/tflite-micro/actions/workflows/run_windows.yml/badge.svg)](https://github.com/tensorflow/tflite-micro/actions/workflows/run_windows.yml)  [![同步](https://github.com/tensorflow/tflite-micro/actions/workflows/sync.yml/badge.svg)](https://github.com/tensorflow/tflite-micro/actions/workflows/sync.yml) |
| 目标平台 | [![Cortex-M](https://github.com/tensorflow/tflite-micro/actions/workflows/run_cortex_m.yml/badge.svg)](https://github.com/tensorflow/tflite-micro/actions/workflows/run_cortex_m.yml) [![RISC-V](https://github.com/tensorflow/tflite-micro/actions/workflows/run_riscv.yml/badge.svg)](https://github.com/tensorflow/tflite-micro/actions/workflows/run_riscv.yml) [![Hexagon](https://github.com/tensorflow/tflite-micro/actions/workflows/run_hexagon.yml/badge.svg)](https://github.com/tensorflow/tflite-micro/actions/workflows/run_hexagon.yml) [![Xtensa](https://github.com/tensorflow/tflite-micro/actions/workflows/run_xtensa.yml/badge.svg)](https://github.com/tensorflow/tflite-micro/actions/workflows/run_xtensa.yml) |
| 其他 | [![生成集成测试](https://github.com/tensorflow/tflite-micro/actions/workflows/generate_integration_tests.yml/badge.svg)](https://github.com/tensorflow/tflite-micro/actions/workflows/generate_integration_tests.yml) |

## 社区支持的 TFLM 示例
## Community Supported TFLM Examples

此表格记录了 TFLM 已移植到的平台。请参阅[新平台支持](tensorflow/lite/micro/docs/new_platform_support.md)获取更多文档。
This table captures platforms that TFLM has been ported to. Please see
[New Platform Support](tensorflow/lite/micro/docs/new_platform_support.md) for
additional documentation.

| 平台 | 状态 |
|-----------|--------------|
| Arduino | [![Arduino](https://github.com/tensorflow/tflite-micro-arduino-examples/actions/workflows/ci.yml/badge.svg)](https://github.com/tensorflow/tflite-micro-arduino-examples/actions/workflows/ci.yml) [![Antmicro](https://github.com/antmicro/tensorflow-arduino-examples/actions/workflows/test_examples.yml/badge.svg)](https://github.com/antmicro/tensorflow-arduino-examples/actions/workflows/test_examples.yml) |
| [Coral Dev Board Micro](https://coral.ai/products/dev-board-micro) | [Coral Dev Board Micro 的 TFLM + EdgeTPU 示例](https://github.com/google-coral/coralmicro) |
| Espressif Systems 开发板 | [![ESP 开发板](https://github.com/espressif/tflite-micro-esp-examples/actions/workflows/ci.yml/badge.svg)](https://github.com/espressif/tflite-micro-esp-examples/actions/workflows/ci.yml) |
| Ingenic MIPS 开发板 | [![Ingenic MIPS 开发板](https://github.com/yinzara/ingenic-tflite-micro/actions/workflows/ci.yml/badge.svg)](https://github.com/yinzara/ingenic-tflite-micro/tree/main/examples/hello_world) |
| Renesas 开发板 | [Renesas 开发板的 TFLM 示例](https://github.com/renesas/tflite-micro-renesas) |
| Silicon Labs 开发套件 | [Silicon Labs 开发套件的 TFLM 示例](https://github.com/SiliconLabs/tflite-micro-efr32-examples) |
| Sparkfun Edge | [![Sparkfun Edge](https://github.com/advaitjain/tflite-micro-sparkfun-edge-examples/actions/workflows/ci.yml/badge.svg?event=schedule)](https://github.com/advaitjain/tflite-micro-sparkfun-edge-examples/actions/workflows/ci.yml) |
| Texas Instruments 开发板 | [![Texas Instruments 开发板](https://github.com/TexasInstruments/tensorflow-lite-micro-examples/actions/workflows/ci.yml/badge.svg?event=status)](https://github.com/TexasInstruments/tensorflow-lite-micro-examples/actions/workflows/ci.yml) |

# 贡献指南
# Contributing

请参阅我们的[贡献文档](CONTRIBUTING.md)。
See our [contribution documentation](CONTRIBUTING.md).

# 获取帮助
# Getting Help

[GitHub issue](https://github.com/tensorflow/tflite-micro/issues/new/choose) 应该是联系 TensorFlow Lite Micro (TFLM) 团队的主要方式。
A [Github issue](https://github.com/tensorflow/tflite-micro/issues/new/choose)
should be the primary method of getting in touch with the TensorFlow Lite Micro
(TFLM) team.

以下资源也可能有用：
The following resources may also be useful:

1. SIG Micro [电子邮件组](https://groups.google.com/a/tensorflow.org/g/micro) 和 [月度会议](http://doc/1YHq9rmhrOUdcZnrEnVCWvd87s2wQbq4z17HbeRl-DBc)。
1.  SIG Micro [email group](https://groups.google.com/a/tensorflow.org/g/micro)
    and
    [monthly meetings](http://doc/1YHq9rmhrOUdcZnrEnVCWvd87s2wQbq4z17HbeRl-DBc).

2. SIG Micro [gitter 聊天室](https://gitter.im/tensorflow/sig-micro)。
1.  SIG Micro [gitter chat room](https://gitter.im/tensorflow/sig-micro).

3. 对于不特定于 TFLM 的问题，请咨询更广泛的 TensorFlow 项目，例如：
1. For questions that are not specific to TFLM, please consult the broader TensorFlow project, e.g.:
   * 在 [TensorFlow Discourse 论坛](https://discuss.tensorflow.org) 上创建主题
   * Create a topic on the [TensorFlow Discourse forum](https://discuss.tensorflow.org)
   * 发送电子邮件到 [TensorFlow Lite 邮件列表](https://groups.google.com/a/tensorflow.org/g/tflite)
   * Send an email to the [TensorFlow Lite mailing list](https://groups.google.com/a/tensorflow.org/g/tflite)
   * 创建 [TensorFlow issue](https://github.com/tensorflow/tensorflow/issues/new/choose)
   * Create a [TensorFlow issue](https://github.com/tensorflow/tensorflow/issues/new/choose)
   * 创建 [模型优化工具包](https://github.com/tensorflow/model-optimization) issue
   * Create a [Model Optimization Toolkit](https://github.com/tensorflow/model-optimization) issue

# 附加文档
# Additional Documentation

 * [持续集成](docs/continuous_integration.md)
 * [Continuous Integration](docs/continuous_integration.md)
 * [基准测试](tensorflow/lite/micro/benchmarks/README.md)
 * [Benchmarks](tensorflow/lite/micro/benchmarks/README.md)
 * [性能分析](tensorflow/lite/micro/docs/profiling.md)
 * [Profiling](tensorflow/lite/micro/docs/profiling.md)
 * [内存管理](tensorflow/lite/micro/docs/memory_management.md)
 * [Memory Management](tensorflow/lite/micro/docs/memory_management.md)
 * [日志记录](tensorflow/lite/micro/docs/logging.md)
 * [Logging](tensorflow/lite/micro/docs/logging.md)
 * [从 TfLite 移植参考内核到 TFLM](tensorflow/lite/micro/docs/porting_reference_ops.md)
 * [Porting Reference Kernels from TfLite to TFLM](tensorflow/lite/micro/docs/porting_reference_ops.md)
 * [优化内核实现](tensorflow/lite/micro/docs/optimized_kernel_implementations.md)
 * [Optimized Kernel Implementations](tensorflow/lite/micro/docs/optimized_kernel_implementations.md)
 * [新平台支持](tensorflow/lite/micro/docs/new_platform_support.md)
 * [New Platform Support](tensorflow/lite/micro/docs/new_platform_support.md)
 * 平台/IP 支持
 * Platform/IP support
   * [Arm IP 支持](tensorflow/lite/micro/docs/arm.md)
   * [Arm IP support](tensorflow/lite/micro/docs/arm.md)
 * [使用 Renode 进行软件仿真](tensorflow/lite/micro/docs/renode.md)
 * [Software Emulation with Renode](tensorflow/lite/micro/docs/renode.md)
 * [使用 QEMU 进行软件仿真](tensorflow/lite/micro/docs/qemu.md)
 * [Software Emulation with QEMU](tensorflow/lite/micro/docs/qemu.md)
 * [压缩](tensorflow/lite/micro/docs/compression.md)
 * [Compression](tensorflow/lite/micro/docs/compression.md)
   * [MNIST 压缩教程](tensorflow/lite/micro/compression/mnist_compression_tutorial.ipynb)
   * [MNIST Compression Tutorial](tensorflow/lite/micro/compression/mnist_compression_tutorial.ipynb)
 * [Python 开发指南](docs/python.md)
 * [Python Dev Guide](docs/python.md)
 * [自动生成的文件](docs/automatically_generated_files.md)
 * [Automatically Generated Files](docs/automatically_generated_files.md)
 * [Python 解释器指南](python/tflite_micro/README.md)
 * [Python Interpreter Guide](python/tflite_micro/README.md)

# RFC 文档
# RFCs

1. [预分配张量](tensorflow/lite/micro/docs/rfc/001_preallocated_tensors.md)
1. [Pre-allocated tensors](tensorflow/lite/micro/docs/rfc/001_preallocated_tensors.md)
2. [TensorFlow Lite for Microcontrollers 的 16x8 量化算子移植](tensorflow/lite/micro/docs/rfc/002_16x8_quantization_port.md)
1. [TensorFlow Lite for Microcontrollers Port of 16x8 Quantized Operators](tensorflow/lite/micro/docs/rfc/002_16x8_quantization_port.md)