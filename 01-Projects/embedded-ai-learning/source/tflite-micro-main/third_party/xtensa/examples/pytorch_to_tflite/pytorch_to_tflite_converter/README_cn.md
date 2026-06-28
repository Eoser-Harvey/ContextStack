<!--ts-->
<!-- 翻译：AI助手，于 2026年5月12日 -->
<!--te-->

## 使用 TinyNN 工具通过 Google Colaboratory 将模型从 pytorch(mobilenet_v2) 转换为 tflite(int8 量化)。
## Convert model from pytorch(mobilenet_v2) to tflite(int8 quantized) with TinyNN tool using Google Colaboratory.

<table class="tfo-notebook-buttons" align="left">
  <td>
    <a target="_blank" href="https://colab.research.google.com/github/nyadla-sys/tflite-micro/blob/pytorch_to_tflite_conversion/third_party/xtensa/examples/pytorch_to_tflite/pytorch_to_tflite_converter/tinynn_pytorch_to_tflite_int8.ipynb"><img src="https://www.tensorflow.org/images/colab_logo_32px.png" />Google Colaboratory</a>
  </td>
</table>
*预计转换时间：约 3 分钟。*
*Estimated Conversion Time: ~3 Mins.*

## 使用 Google Colaboratory 将模型从 pytorch 转换为 onnx 再转换为 tflite(int8 量化)。
## Convert the model from pytorch to onnx to tflite(int8 quantized) using Google Colaboratory.

<table class="tfo-notebook-buttons" align="left">
  <td>
    <a target="_blank" href="https://colab.research.google.com/github/nyadla-sys/tflite-micro/blob/pytorch_to_tflite_conversion/third_party/xtensa/examples/pytorch_to_tflite/pytorch_to_tflite_converter/pytorch_to_onnx_to_tflite_int8.ipynb"><img src="https://www.tensorflow.org/images/colab_logo_32px.png" />Google Colaboratory</a>
  </td>
</table>
*预计转换时间：约 5 分钟。*
*Estimated Conversion Time: ~5 Mins.*

## Mobilenet_v2(int8 量化) 模型架构
## Mobilenet_v2(int8 quantized) Model Architecture

这是一个 mobilenet v2 模型。
This is a mobilenet v2 model.

![mobilenet_v2_quantized_model](../images/qat_model.png)