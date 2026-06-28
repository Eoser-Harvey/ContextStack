<!--ts-->
<!-- 翻译：AI助手，于 2026年5月12日 -->
<!--te-->

# 设置 Xtensa 工具
# Setup Xtensa Tools

```bash
$ set path = ( ~/xtensa/XtDevTools/install/tools/RI-2020.5-linux/XtensaTools/bin $path )
$ set path = ( ~/xtensa/XtDevTools/install/tools/RI-2020.5-linux/XtensaTools/Tools/bin $path )
$ setenv XTENSA_SYSTEM ~xtensa/XtDevTools/install/tools/RI-2020.5-linux/XtensaTools/config
$ setenv XTENSA_CORE AE_HiFi5_LE5_AO_FP_XC
$ setenv XTENSA_TOOLS_VERSION RI-2020.5-linux
$ setenv XTENSA_BASE ~/xtensa/XtDevTools/install/
```

# 清理并在 TFLM 上构建 mobilenet_v2 模型
# Clean and build mobilenet_v2 model on TFLM

```bash
$ make -f tensorflow/lite/micro/tools/make/Makefile clean
$ make -f tensorflow/lite/micro/tools/make/Makefile TARGET=xtensa OPTIMIZED_KERNEL_DIR=xtensa TARGET=xtensa TARGET_ARCH=hifi5 test_pytorch_to_tflite_test -j
```