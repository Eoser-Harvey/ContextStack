# 用于特征生成的音频"前端"库

一个特征生成库（也称为前端），接收原始音频输入，并产生滤波器组（值向量）。

原始音频输入应为 16 位 PCM 特征，具有可配置的采样率。更具体地说，音频信号通过预加重滤波器（可选）；然后被切片成（可能重叠的）帧，并对每个帧应用窗口函数；之后，我们对每帧进行傅里叶变换（或更具体地说是短时傅里叶变换）并计算功率谱；随后计算滤波器组。

默认情况下，库配置有一组默认值来执行不同的处理任务。这通过 frontend_util.c 函数完成：

```c++
void FrontendFillConfigWithDefaults(struct FrontendConfig* config)
```

单个调用如下所示：

```c++
struct FrontendConfig frontend_config;
FrontendFillConfigWithDefaults(&frontend_config);
int sample_rate = 16000;
FrontendPopulateState(&frontend_config, &frontend_state, sample_rate);
int16_t* audio_data = ;  // 16KHz 的 PCM 音频样本。
size_t audio_size = ;  // 音频样本数。
size_t num_samples_read;  // 处理了多少样本。
struct FrontendOutput output =
    FrontendProcessSamples(
        &frontend_state, audio_data, audio_size, &num_samples_read);
for (i = 0; i < output.size; ++i) {
  printf("%d ", output.values[i]);  // 打印特征向量。
}
```

上述示例中需要注意的一点是，前端从音频数据中消耗尽可能多的样本来生成单个特征向量（根据前端配置）。如果没有足够的样本来生成特征向量，返回的大小将为 0，值指针将为 `NULL`。

frontend_main.cc 及其二进制文件 frontend_main 提供了一个如何使用前端的示例。此示例期望一个包含 `int16` PCM 特征（采样率为 16KHz）的文件路径，并在执行时根据前端默认配置打印出系数。

## 额外功能
此前端库的额外功能包括噪声抑制模块以及增益控制模块。

**噪声消除**。使用低通滤波器从信号的每个通道中去除平稳噪声。

**增益控制**。一种基于动态压缩的新型自动增益控制，以取代广泛使用的静态（如对数或根）压缩。默认禁用。

## 内存映射
二进制文件 frontend_memmap_main 展示了如何在应用程序中避免所有初始化代码的示例用法，首先运行 "frontend_generate_memmap" 创建一个使用烘焙前端状态的头文件/源文件。此命令可以作为构建过程的一部分自动化，或者您可以直接使用输出。