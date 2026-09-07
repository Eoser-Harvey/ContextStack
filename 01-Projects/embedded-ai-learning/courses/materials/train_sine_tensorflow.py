# -*- coding: utf-8 -*-
"""
使用 CSV 数据集训练正弦波 TensorFlow 模型，并导出为 TFLite
数据集要求：CSV 至少包含两列：x, y
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf


# =========================
# 1. 路径配置
# =========================
CSV_PATH = "sine_raw - Copy.csv"   # 改成你的 CSV 路径
OUT_DIR = Path("sine_tf_output")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# 2. 固定随机种子，保证结果可复现
# =========================
SEED = 42
np.random.seed(SEED)
tf.random.set_seed(SEED)


# =========================
# 3. 读取数据
# =========================
df = pd.read_csv(CSV_PATH)

required_cols = {"x", "y"}
if not required_cols.issubset(df.columns):
    raise ValueError(f"CSV 文件必须包含列: {required_cols}，当前列为: {df.columns.tolist()}")

if df[["x", "y"]].isna().any().any():
    raise ValueError("CSV 中存在缺失值，请先清理数据。")

# 转成 float32，方便后续训练和部署
x = df["x"].to_numpy(dtype=np.float32)
y = df["y"].to_numpy(dtype=np.float32)

# 形状改成 [N, 1]
x = x.reshape(-1, 1)
y = y.reshape(-1, 1)

print("样本数量:", len(x))
print("x shape:", x.shape)
print("y shape:", y.shape)
print("x 范围:", float(x.min()), "->", float(x.max()))
print("y 范围:", float(y.min()), "->", float(y.max()))


# =========================
# 4. 训练 / 验证 / 测试集划分
#    70% / 15% / 15%
# =========================
indices = np.arange(len(x))
np.random.shuffle(indices)

x = x[indices]
y = y[indices]

n_total = len(x)
n_train = int(n_total * 0.70)
n_val = int(n_total * 0.15)

x_train = x[:n_train]
y_train = y[:n_train]

x_val = x[n_train:n_train + n_val]
y_val = y[n_train:n_train + n_val]

x_test = x[n_train + n_val:]
y_test = y[n_train + n_val:]

print("训练集:", x_train.shape, y_train.shape)
print("验证集:", x_val.shape, y_val.shape)
print("测试集:", x_test.shape, y_test.shape)


# =========================
# 5. 输入归一化
#    对 MCU 部署非常重要
# =========================
x_min = x_train.min()
x_max = x_train.max()

def normalize_x(x_input: np.ndarray) -> np.ndarray:
    return (x_input - x_min) / (x_max - x_min)

x_train_norm = normalize_x(x_train).astype(np.float32)
x_val_norm = normalize_x(x_val).astype(np.float32)
x_test_norm = normalize_x(x_test).astype(np.float32)

norm_params = {
    "x_min": float(x_min),
    "x_max": float(x_max),
    "formula": "x_norm = (x - x_min) / (x_max - x_min)"
}
with open(OUT_DIR / "normalization.json", "w", encoding="utf-8") as f:
    json.dump(norm_params, f, ensure_ascii=False, indent=2)


# =========================
# 6. 构建模型
#    这是一个很小的回归网络
# =========================
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(1,), name="input_x"),
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dense(1, name="output_y")
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.01),
    loss="mse",
    metrics=["mae"]
)

model.summary()


# =========================
# 7. 训练模型
# =========================
callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=30,
        restore_best_weights=True
    )
]

history = model.fit(
    x_train_norm,
    y_train,
    validation_data=(x_val_norm, y_val),
    epochs=300,
    batch_size=32,
    verbose=1,
    callbacks=callbacks
)


# =========================
# 8. 模型评估
# =========================
test_loss, test_mae = model.evaluate(x_test_norm, y_test, verbose=0)
print(f"测试集 MSE: {test_loss:.8f}")
print(f"测试集 MAE: {test_mae:.8f}")


# =========================
# 9. 保存 Keras 模型
# =========================
model.save(OUT_DIR / "sine_model.keras")


# =========================
# 10. 导出 float32 TFLite
# =========================
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

float_tflite_path = OUT_DIR / "sine_model_float32.tflite"
with open(float_tflite_path, "wb") as f:
    f.write(tflite_model)

print("已导出:", float_tflite_path)


# =========================
# 11. 导出 int8 TFLite
#     这个版本更适合 MCU
# =========================
def representative_dataset():
    for i in range(min(200, len(x_train_norm))):
        yield [x_train_norm[i:i+1]]

converter_int8 = tf.lite.TFLiteConverter.from_keras_model(model)
converter_int8.optimizations = [tf.lite.Optimize.DEFAULT]
converter_int8.representative_dataset = representative_dataset
converter_int8.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
converter_int8.inference_input_type = tf.int8
converter_int8.inference_output_type = tf.int8

tflite_model_int8 = converter_int8.convert()

int8_tflite_path = OUT_DIR / "sine_model_int8.tflite"
with open(int8_tflite_path, "wb") as f:
    f.write(tflite_model_int8)

print("已导出:", int8_tflite_path)


# =========================
# 12. 使用 Keras 模型做可视化验证
# =========================
x_plot = np.linspace(float(x.min()), float(x.max()), 500, dtype=np.float32).reshape(-1, 1)
x_plot_norm = normalize_x(x_plot).astype(np.float32)
y_pred = model.predict(x_plot_norm, verbose=0)

plt.figure(figsize=(10, 6))
plt.scatter(df["x"], df["y"], s=10, alpha=0.4, label="dataset")
plt.plot(x_plot, np.sin(x_plot), label="ideal sin(x)")
plt.plot(x_plot, y_pred, label="model prediction")
plt.xlabel("x")
plt.ylabel("y")
plt.title("Sine Model Training Result")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(OUT_DIR / "prediction_curve.png", dpi=150)
plt.close()

print("已保存预测曲线图:", OUT_DIR / "prediction_curve.png")


# =========================
# 13. 训练过程曲线
# =========================
plt.figure(figsize=(10, 6))
plt.plot(history.history["loss"], label="train_loss")
plt.plot(history.history["val_loss"], label="val_loss")
plt.xlabel("epoch")
plt.ylabel("loss")
plt.title("Training History")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig(OUT_DIR / "training_history.png", dpi=150)
plt.close()

print("已保存训练曲线图:", OUT_DIR / "training_history.png")


# =========================
# 14. 输出 TFLite 输入输出信息
# =========================
interpreter = tf.lite.Interpreter(model_path=str(int8_tflite_path))
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

print("\nINT8 TFLite 输入信息:")
print(input_details)

print("\nINT8 TFLite 输出信息:")
print(output_details)


# =========================
# 15. 将 tflite 转成 C 数组
# =========================
def convert_tflite_to_c_array(tflite_path: Path, output_header_path: Path, array_name: str):
    data = tflite_path.read_bytes()
    with open(output_header_path, "w", encoding="utf-8") as f:
        f.write("#ifndef SINE_MODEL_DATA_H\n")
        f.write("#define SINE_MODEL_DATA_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write(f"const unsigned char {array_name}[] = {{\n")
        for i, b in enumerate(data):
            if i % 12 == 0:
                f.write("    ")
            f.write(f"0x{b:02x}, ")
            if i % 12 == 11:
                f.write("\n")
        f.write("\n};\n\n")
        f.write(f"const unsigned int {array_name}_len = {len(data)};\n\n")
        f.write("#endif\n")

convert_tflite_to_c_array(
    int8_tflite_path,
    OUT_DIR / "sine_model_data.h",
    "g_sine_model_data"
)

print("已生成 C 数组头文件:", OUT_DIR / "sine_model_data.h")


print("\n全部完成。输出目录:", OUT_DIR.resolve())
