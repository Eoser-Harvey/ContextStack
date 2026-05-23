# 网络测试器

此应用程序的目的是提供一种快速测试不同网络的方法。

它包含一个测试用例和一个默认的网络模型 (network_model.h)、默认的输入数据 (input_data.h) 和默认的预期输出数据 (expected_output_data.h)。头文件是使用 `xxd` 命令创建的。

默认模型是一个 int8 DepthwiseConv2D 算子，输入形状为 {1, 8, 8, 16}、{1, 2, 2, 16} 和 {16}，输出形状为 {1, 4, 4, 16}。

当为 Ethos-U 构建 FVP 目标 (CO_PROCESSOR=ethos_u) 时，使用人员检测 int8 模型代替。下载的模型使用 Ethos-U Vela 针对 Ethos-U 进行了优化。有关更多信息，请参阅以下 readme 文件：
tensorflow/lite/micro/kernels/ethos_u/README.md
tensorflow/lite/micro/cortex_m_corstone_300/README.md
tensorflow/lite/micro/examples/person_detection/README.md 使用了以下 Vela 配置，该配置与 FVP 构建目标 (TARGET=cortex_m_corstone_300) 兼容。

```
vela --accelerator-config=ethos-u55-256
```

为了使用另一个模型、输入数据或预期输出数据，只需在运行 make 时指定新头文件的路径，如下所示。

指定头文件中的变量（数组和数组长度）需要与默认头文件中的变量具有相同的名称和类型。包含保护符也需要相同。当更换网络模型时，解释器分配的内存可能需要增加以适应新模型。这是通过在运行 `make` 时使用 `ARENA_SIZE` 选项来完成的。

```
make -f tensorflow/lite/micro/tools/make/Makefile network_tester_test \
                  NETWORK_MODEL=path/to/network_model.h \
                  INPUT_DATA=path/to/input_data.h \
                  OUTPUT_DATA=path/to/expected_output_data.h \
                  ARENA_SIZE=<tensor arena size in bytes> \
                  NUM_BYTES_TO_PRINT=<number of bytes to print> \
                  COMPARE_OUTPUT_DATA=no
```

`NETWORK_MODEL`：网络模型头的路径。\
`INPUT_DATA`：输入数据的路径。\
`OUTPUT_DATA`：预期输出数据的路径。\
`ARENA_SIZE`：解释器要分配的内存大小（以字节为单位）。\
`NUM_BYTES_TO_PRINT`：要打印的输出数据的字节数。\
如果设置为 0，则打印输出的所有字节。\
`COMPARE_OUTPUT_DATA`：如果设置为 "no"，则输出数据不与预期输出数据进行比较。这可能很有用，例如，如果需要最小化执行时间，或者没有预期输出数据。如果省略，则输出数据与预期输出进行比较。`NUM_INFERENCES`：定义进行多少次推理。默认为 1。\

输出使用 printf 以 JSON 格式打印：`num_of_outputs: 1
output_begin [ { "dims": [4,1,2,2,1], "data_address": "0x000000",
"data":"0x06,0x08,0x0e,0x10" }] output_end`

如果有多个输出张量，输出将如下所示：
`num_of_outputs: 2 output_begin [ { "dims": [4,1,2,2,1], "data_address":
"0x000000", "data":"0x06,0x08,0x0e,0x10" }, { "dims": [4,1,2,2,1],
"data_address": "0x111111", "data":"0x06,0x08,0x0e,0x10" }] output_end`