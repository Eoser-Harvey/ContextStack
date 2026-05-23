# DTLN 示例

DTLN 示例是在 HiFi DSP 上运行 DTLN 网络进行语音噪声抑制的演示。
它使用 feature_data 作为输入，并提供噪声抑制后的语音作为输出。
它基于论文(https://github.com/breizhn/DTLN)。
虽然论文提出了两部分，一部分用于噪声抑制，另一部分用于语音增强，
但此处展示的示例仅遵循噪声抑制部分。
该模型由 Cadence 使用 DNS 挑战数据 (https://github.com/microsoft/DNS-Challenge) 重新训练，
并且噪声抑制部分进行了 8 位量化。
此示例不应用于评估网络质量或噪声抑制质量，仅作为上述所述的演示。

## 在开发机器上运行测试

```
make -f tensorflow/lite/micro/tools/make/Makefile third_party_downloads
make -f tensorflow/lite/micro/tools/make/Makefile test_dtln_test
```

您应该看到一系列文件被编译，然后是一些测试的日志输出，最后应以 `~~~ALL TESTS PASSED~~~` 结束。如果您看到此消息，这意味着已构建并运行了一个小型程序，该程序加载了经过训练的 TensorFlow 模型，使用特征数据运行，并获得了预期的输出。此特定测试使用特征数据作为输入运行，并与黄金参考输出验证输出。