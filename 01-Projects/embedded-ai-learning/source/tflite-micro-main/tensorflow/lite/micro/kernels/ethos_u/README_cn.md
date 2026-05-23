<!-- mdformat off(b/169948621#comment2) -->

# 信息
Arm(R) Ethos(TM)-U 是一类新的机器学习处理器，称为 microNPU，专门设计用于在面积受限的嵌入式和 IoT 设备中加速 ML 推理。此 readme 简要描述了如何将 Ethos-U 相关的硬件和软件集成到 TFLM 中。另请参阅 [Ethos-U ML 评估套件示例](https://gitlab.arm.com/artificial-intelligence/ethos-u/ml-embedded-evaluation-kit)。

要启用 Ethos-U 软件栈，请在 make 命令中添加 `CO_PROCESSOR=ethos_u`。使用 ETHOSU_ARCH 指定架构。请参见以下示例。

## 要求：
- Armclang 6.14 或更高版本
- GCC 10.2.1 或更高版本

## Ethos-U 自定义算子
当 TFLM 运行时在 tflite 文件中遇到 Ethos-U 自定义算子时，它将把工作负载分派给 Ethos-U。请参见下面的 ASCII 艺术示例。
Ethos-U 自定义算子由名为 Ethos-U Vela 的工具添加，并包含 Ethos-U 硬件执行工作负载所需的信息。更多信息请参阅 [Vela 仓库](https://gitlab.arm.com/artificial-intelligence/ethos-u/ethos-u-vela)。

```
     | tensor0
     |
     v
+------------+
| ethos-u    |
| custom op  |
+------------+
     +
     |
     | tensor1
     |
     v
+-----------+
| transpose |
|           |
+----|------+
     |
     | tensor2
     |
     v
```

请注意，需要在启动时调用 Ethos-U 驱动程序的 `ethousu_init()` API，然后再调用 TFLM API。更多信息请参阅 [Ethos-U 驱动程序仓库](https://gitlab.arm.com/artificial-intelligence/ethos-u/ethos-u-core-driver)。

有关 Vela 和 Ethos-U 的更多信息，请查看 [Ethos-U 登录页面](https://gitlab.arm.com/artificial-intelligence/ethos-u/ethos-u/-/tree/main)。

# 一些编译二进制文件并使用 Ethos-U 支持运行网络的示例。
为了运行启用 Ethos-U55 的测试，需要具有相应硬件支持的平台。其中一个平台是基于 Arm Corstone-300 软件的固定虚拟平台 (FVP)。有关更多信息，请参阅 [Corstone-300 readme](https://github.com/tensorflow/tflite-micro/tree/main/tensorflow/lite/micro/cortex_m_corstone_300/README.md)。

此外，需要根据上述"Ethos-U 自定义算子"子章节修改 .tflite 模型。

可以在构建命令中设置 Ethos-U 驱动程序的日志级别。例如：ETHOSU_LOG_SEVERITY=ETHOSU_LOG_INFO。

## 使用网络测试器的示例
有关更多信息，请参阅 tensorflow/lite/micro/examples/network_tester/README.md。

```
make -f tensorflow/lite/micro/tools/make/Makefile network_tester_test CO_PROCESSOR=ethos_u ETHOSU_ARCH=u55 TARGET=cortex_m_generic TARGET_ARCH=cortex-m55 microlite
```

对于 Arm Corstone-300 目标，ETHOSU_ARCH 在 cortex_m_corstone_300_makefile.inc 中定义，因此无需在命令行上定义。

```
make -f tensorflow/lite/micro/tools/make/Makefile network_tester_test CO_PROCESSOR=ethos_u TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 test_network_tester_test NETWORK_MODEL=path/to/network_model.h INPUT_DATA=path/to/input_data.h OUTPUT_DATA=path/to/expected_output_data.h

make -f tensorflow/lite/micro/tools/make/Makefile network_tester_test CO_PROCESSOR=ethos_u TARGET=cortex_m_corstone_300 TARGET_ARCH=cortex-m55 test_network_tester_test
```