<!-- 翻译：AI助手，于 2026年5月13日 -->
<!-- 格式：中英文对照，便于学习 -->

# 从模型生成 Micro Mutable Op Resolver
# Generate Micro Mutable Op Resolver from a model

MicroMutableOpResolver 包括源代码中明确指定的算子。这通常需要手动通过可视化工具找出模型中使用的算子，在某些情况下可能不切实际。此脚本将自动为给定模型或一组模型生成仅包含使用算子的 MicroMutableOpResolver。
The MicroMutableOpResolver includes the operators explictly specified in source code.
This generally requires manually finding out which operators are used in the model through the use of a visualization tool, which may be impractical in some cases.
This script will automatically generate a MicroMutableOpResolver with only the used operators for a given model or set of models.

注意：检查 ci/Dockerfile.micro 以获取支持的 Python 版本。
Note: Check ci/Dockerfile.micro for supported python version.

## 如何运行
## How to run

```bash
bazel run tensorflow/lite/micro/tools/gen_micro_mutable_op_resolver:generate_micro_mutable_op_resolver_from_model -- \
             --common_tflite_path=<path to tflite file> \
             --input_tflite_files=<name of tflite file(s)> --output_dir=<output directory>
```

请注意，如果只有一个 tflite 作为输入，最终输出目录将是 <output directory>/<base name of model>。
Note that if having only one tflite as input, the final output directory will be <output directory>/<base name of model>.

示例：
Example:

```bash
bazel run tensorflow/lite/micro/tools/gen_micro_mutable_op_resolver:generate_micro_mutable_op_resolver_from_model -- \
             --common_tflite_path=/tmp/model_dir \
             --input_tflite_files=person_detect.tflite --output_dir=/tmp/gen_dir
```

一个名为 gen_micro_mutable_op_resolver.h 的头文件将在 /tmp/gen_dir/person_detect 中创建。
A header file called, gen_micro_mutable_op_resolver.h will be created in /tmp/gen_dir/person_detect.

示例：
Example:

```bash
bazel run tensorflow/lite/micro/tools/gen_micro_mutable_op_resolver:generate_micro_mutable_op_resolver_from_model -- \
             --common_tflite_path=/tmp/model_dir \
             --input_tflite_files=person_detect.tflite,keyword_scrambled.tflite --output_dir=/tmp/gen_dir
```

一个名为 gen_micro_mutable_op_resolver.h 的头文件将在 /tmp/gen_dir 中创建。
A header file called, gen_micro_mutable_op_resolver.h will be created in /tmp/gen_dir.

请注意，对于多个 tflite 文件作为输入，文件必须放置在同一公共目录中。
Note that with multiple tflite files as input, the files must be placed in the same common directory.

然后可以在应用程序中包含生成的头文件，并按如下方式使用：
The generated header file can then be included in the application and used like below:

```cpp
tflite::MicroMutableOpResolver<kNumberOperators> op_resolver = get_resolver();
```

## 验证生成的头文件内容
## Verifying the content of the generated header file

这只是为了测试为给定模型生成微可变算子解析器头的实际脚本。以便算子列表对应于给定模型，并且头的语法正确。
This is just to test the actual script that generates the micro mutable ops resolver header for a given model.
So that the actual list of operators corresponds to a given model and that the syntax of the header is correct.

为此，可以使用另一个脚本来验证生成的头文件：
For this another script can be used to verify the generated header file:

```bash
bazel run tensorflow/lite/micro/tools/gen_micro_mutable_op_resolver:generate_micro_mutable_op_resolver_from_model_test -- \
             --input_tflite_file=<path to tflite file> --output_dir=<output directory>
```

此脚本一次验证一个模型。它将生成一个使用生成的头文件的小型推理测试应用程序，然后可以作为最后一步执行和测试。
This script verifies a single model at a time. It will generate a small inference testing app that is using the generated header file, which can then be executed and tested as a final step.

因此，指定的输出路径将附加模型名称，以便生成的测试以模型命名。
Because of this the specified output path will be appended with the name of the model so that the generated test is named after the model.

换句话说，最终输出目录将是 <output directory>/<base name of model>。
In other words the final output directory will be <output directory>/<base name of model>.

本质上是，实际的头脚本和实际的测试脚本需要指定不同的输出路径。
The essence of this is that different output paths need to be specified for the actual header script and the actual test script.

因此将有 3 个步骤：
So there will be 3 steps,

1) 生成微可变算子解析器，指定输出路径，例如 gen_dir/<base_name_of_model>
1) Generate the micro mutable specifying e.g. output path gen_dir/<base_name_of_model>
2) 生成微可变算子解析器，指定输出路径，例如 gen_dir
2) Generate the micro mutable specifying e.g. output path gen_dir
3) 运行生成的测试
3) Run the generated test

示例假设 /tmp/my_model.tflite 存在：
Example assuming /tmp/my_model.tflite exists:

```bash
# 步骤 1：生成头文件到 gen_dir/my_model
# Step 1 generates header to gen_dir/my_model
bazel run tensorflow/lite/micro/tools/gen_micro_mutable_op_resolver:generate_micro_mutable_op_resolver_from_model -- \
             --common_tflite_path=/tmp/ \
             --input_tflite_files=my_model.tflite --output_dir=$(realpath gen_dir/my_model)

# 步骤 2：使用步骤 1 的头文件生成测试应用程序到 gen_dir/my_model，因为 my_model 被附加
# Step 2 generates test app using header from step 1 to gen_dir/my_model since my my_model is appended
bazel run tensorflow/lite/micro/tools/gen_micro_mutable_op_resolver:generate_micro_mutable_op_resolver_from_model_test -- \
             --input_tflite_file=/tmp/my_model.tflite --output_dir=$(realpath gen_dir) --verify_output=1

# 步骤 3：运行生成的 my_model 测试
# Step 3 runs the generated my_model test
bazel run gen_dir/my_model:micro_mutable_op_resolver_test
```

注意1：Bazel 期望绝对路径。
Note1: Bazel expects absolute paths.

注意2：默认情况下，推理模型测试将在没有任何生成输入或验证输出的情况下运行。验证输出可以使用 --verify_output=1 完成，如上例所示。
Note2: By default the inference model test will run without any generated input or verifying the output. Verifying output can be done with --verify_output=1, which is done in the example above.

注意3：根据模型的大小，可能需要增加竞技场大小。可以使用 --arena_size=<size> 设置竞技场大小。
Note3: Depending on the size of the model the arena size may need to be increased. Arena size can be set with --arena_size=<size>.