<!-- 翻译：AI助手，于 2026年5月13日 -->
<!-- 格式：中英文对照，便于学习 -->

# 人员检测示例
# Person detection example

此示例展示如何使用 Tensorflow Lite 运行一个 250 千字节的神经网络来识别图像中的人员。
This example shows how you can use Tensorflow Lite to run a 250 kilobyte neural
network to recognize people in images.

## 目录
## Table of contents

-   [在开发机器上运行测试](#run-the-tests-on-a-development-machine)
-   [Run the tests on a development machine](#run-the-tests-on-a-development-machine)
-   [训练自己的模型](#training-your-own-model)
-   [Training your own model](#training-your-own-model)
-   [附加 makefile 目标](#additional-makefile-targets)
-   [Additional makefile targets](#additional-makefile-targets)

## 在开发机器上运行测试
## Run the tests on a development machine

```
make -f tensorflow/lite/micro/tools/make/Makefile third_party_downloads
make -f tensorflow/lite/micro/tools/make/Makefile test_person_detection_test
```

您应该看到一系列文件被编译，然后是一些测试的日志输出，最后应以 `~~~ALL TESTS PASSED~~~` 结束。如果您看到此消息，这意味着已构建并运行了一个小型程序，该程序加载了经过训练的 TensorFlow 模型，通过它运行了一些示例图像，并获得了预期的输出。此特定测试运行包含人员和不包含人员的图像，并检查网络是否正确识别它们。
You should see a series of files get compiled, followed by some logging output
from a test, which should conclude with `~~~ALL TESTS PASSED~~~`. If you see
this, it means that a small program has been built and run that loads a trained
TensorFlow model, runs some example images through it, and got the expected
outputs. This particular test runs images with a and without a person in them,
and checks that the network correctly identifies them.

要了解 TensorFlow Lite 如何做到这一点，您可以查看 [person_detection_test.cc](person_detection_test.cc)。
To understand how TensorFlow Lite does this, you can look at
[person_detection_test.cc](person_detection_test.cc).

## 附加 makefile 目标
## Additional makefile targets

```
make -f tensorflow/lite/micro/tools/make/Makefile person_detection
make -f tensorflow/lite/micro/tools/make/Makefile person_detection_bin
make -f tensorflow/lite/micro/tools/make/Makefile run_person_detection
```

`run_person_detection` 目标将产生类似于以下内容的连续输出：
The `run_person_detection` target will produce continuous output similar
to the following:

```
person score:-72 no person score 72
```

## 训练自己的模型
## Training your own model

您可以使用一些易于使用的脚本来训练自己的模型。有关说明，请参阅 [training_a_model.md](training_a_model.md)。
You can train your own model with some easy-to-use scripts. See
[training_a_model.md](training_a_model.md) for instructions.