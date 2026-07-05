"""
端侧/嵌入式 AI 学习日报 — 每日推送脚本
追踪平台：Kickstarter / GitHub Trending / 智次方+量子位 / ST+NXP / AidLux / Hugging Face
每日输出：飞书 interactive 卡片 + 本地 Markdown 文件
"""

import json
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from push_lark import send_interactive_card, load_secrets

# ==================== 路径 ====================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESEARCH_DIR = r"E:\ProjectGroup\AI\ContextStack\01-Projects\family-investment\embedded-ai-research"
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y年%m月%d日")
DATE_FILE = TODAY.strftime("%Y-%m-%d")
WEEKDAY = ["周一","周二","周三","周四","周五","周六","周日"][TODAY.weekday()]

# ==================== 数据采集（Web Search 模拟 - 由 TRAE 调用时替换） ====================
# 注意：本脚本在 TRAE Schedule 执行时由 TRAE Agent 负责搜索并替换 NEWS_ITEMS 内容
# 预留给 TRAE 执行的占位结构

NEWS_ITEMS = {
    "kickstarter": [
        {
            "title": "PongBot Aura - AI多球类运动训练机器人，首日筹150万美元",
            "summary": "庞伯特推出的AI多球类运动训练机器人，支持网球/匹克球/板式网球一机多用。120fps双摄AI视觉模块实时追踪球速轨迹，大模型语音控制。基础版499美元，顶配版849美元，远低于传统发球机1500-2000美元价格带。",
            "source": "Kickstarter / 163.com / 头条",
        },
        {
            "title": "StackChan M5 - 开源AI桌面机器人，ESP32-S3芯片，筹得46万美元",
            "summary": "M5Stack推出基于ESP32-S3的开源桌面机器人，双核240MHz，2寸IPS屏，双麦克风阵列，30万像素摄像头。100%开源（Apache 2.0），支持接入ChatGPT等大模型语音交互。早鸟价65-69美元，获4142位支持者。",
            "source": "Kickstarter / 163.com / 雪球",
        },
        {
            "title": "CardputerZero - 口袋Linux开发工具/创客电脑，24小时破100万美元",
            "summary": "M5Stack携手Gadget Labs推出的口袋Linux计算机，将屏幕/键盘/计算核心/开发接口整合进超轻巧形态。可作为便携式边缘计算终端，适用于TinyML模型部署、嵌入式开发、IoT原型验证。",
            "source": "Kickstarter / 头条",
        },
    ],
    "github": [
        {
            "title": "microsoft/onnxruntime v1.27.0 - 跨平台ML推理引擎，Star 21k",
            "summary": "微软出品的高性能跨平台ML推理引擎，支持PyTorch/TF/Keras等模型，CPU/GPU/WebGPU多硬件运行。最新v1.27.0（2026.6.19发布），INT8/FP16量化，图优化与算子融合。C++ 83.5%，被91.2k项目依赖，本月活跃开发中。",
            "source": "github.com/microsoft/onnxruntime",
        },
        {
            "title": "NVIDIA/TensorRT-LLM - LLM推理加速框架，Star 14k",
            "summary": "英伟达LLM推理加速框架，支持Blackwell架构GPU，集成MoE/FP8/INT4量化/paged attention等SOTA技术。LLaMA 70B吞吐量提升3.5倍以上，适用于Jetson等边缘GPU推理。2026.7.5仍有提交，开发极度活跃。",
            "source": "github.com/NVIDIA/TensorRT-LLM",
        },
        {
            "title": "tensorflow/tflite-micro - MCU端ML部署框架，Star 3k",
            "summary": "TFLite Micro专注DSP和MCU等资源受限设备的ML模型部署框架。配合TensorRT 10.16.1（即将发布11.0全面转向强类型网络），是边缘AI推理的核心工具链之一，支持INT4/FP8量化。",
            "source": "github.com/tensorflow/tflite-micro",
        },
    ],
    "industry": [
        {
            "title": "全球首个端侧流式多模态模型VLX发布，0.6B参数跑进手机/机器人",
            "summary": "杭州Om AI团队发布VLX系列：VLX-Flow实时流式感知（0.06秒处理单路视频）、VLX-Seek精准定位（Region Token替代坐标）、VLX-Go行动决策（0.6B参数实时运动规划）。采用Day 1端侧原生架构，可跑进手机/无人机/机器人等端侧设备。",
            "source": "量子位 qbitai.com 2026-06-27",
        },
        {
            "title": "爱芯元智AXera Edge-Day：构筑物理AI算力底座，打通边缘AI商业闭环",
            "summary": "爱芯元智推出爱芯通元原生AI处理器（10倍AI能效提升），覆盖智驾/座舱/具身全场景。AX8910超低功耗双目感知、AX8850 24TOPS精准匹配运控。平台模型库突破200+，Pulsar 2 6.0工具链适配全系列芯片。",
            "source": "雷锋网 leiphone.com 2026-06-30",
        },
        {
            "title": "工业智能体崛起：边缘计算+AI Agents重构产业未来",
            "summary": "研华科技与智次方深度对话，AI Agent从被动执行走向主动进化。Gartner预测2026年50%全球边缘部署将包含AI。研华董事长提出\"垂类模型必然崛起\"判断，从工业电脑向Edge AI引领者转型。",
            "source": "智次方 iot101.com",
        },
    ],
    "st_nxp": [
        {
            "title": "STM32Cube.AI v10.0发布，首次支持STM32N6 Neural-ART NPU（600 GOPS）",
            "summary": "ST发布v10.0重大更新：首次支持STM32N6内置Neural-ART NPU（Arm Cortex-M55 @800MHz + NPU @1GHz，600 GOPS，3 TOPS/W），AI推理性能提升600倍。AI Model Zoo已提供60+预训练模型并新增PyTorch原生支持。",
            "source": "st.com/stm32cubeai",
        },
        {
            "title": "NXP发布eIQ Agentic AI框架 + eIQ Neutron SDK 3.1.3（2026.6）",
            "summary": "业界首批边缘端AI Agent框架，支持边缘设备自主实时决策，内置硬件感知型模型优化和智能调度引擎（CPU/NPU/加速器）。Neutron SDK已迭代到v3.1.3，新增i.MX 937（四核A55+Neutron NPU）和i.MX RT700（5核，AI加速172倍）。",
            "source": "nxp.com/eiq / eepw.com.cn",
        },
        {
            "title": "2026年NPU成为MCU标配：TI推出<$1的TinyEngine NPU MCU",
            "summary": "TI发布MSPM0G5187（Cortex-M0+ @80MHz + TinyEngine NPU，批量价<$1），加速卷积/池化6-7倍。ST STM32N6、NXP i.MX RT700、瑞萨RA8P1（Ethos-U55 256 GOPS）、英飞凌PSoC Edge系列均已量产。AI MCU进入默认配置时代。",
            "source": "CSDN / eepw.com.cn",
        },
    ],
    "aidlux": [
        {
            "title": "阿加犀成功将OpenClaw全链路迁移到端侧，推理速度达829.79 Tokens/s",
            "summary": "将OpenClaw执行框架完整下沉至端侧芯片，彻底脱离云端依赖。采用NanoBot轻量方案，高通8550/9075平台运行Qwen3 8B模型，推理速度最快829.79 Tokens/s，原生支持32K上下文，零额外成本、数据不出设备。",
            "source": "forum.aidlux.com",
        },
        {
            "title": "工业质检实战：多核异构架构CPU占用从90%降至30%，延迟60ms→20ms",
            "summary": "产线视觉检测实战案例：常规工控机方案CPU飙到90%+。采用三核M85 MCU异构架构（采集/推理/UI各跑一核），CPU占用降至30-40%，推理延迟从60ms降至20ms以内，满足100fps产线节拍，24小时压力测试稳定。",
            "source": "forum.aidlux.com",
        },
        {
            "title": "高通QCS8550部署YOLOv11全教程：NPU INT8模式下503 FPS",
            "summary": "完整部署教程：pt→onnx→AIMO转换→aidlite-qnn231推理。性能数据：YOLO11n NPU INT8达503 FPS、FP16 219 FPS；YOLO11s NPU INT8达345 FPS；YOLO11x NPU INT8达75 FPS。AidLux 2.1.1已于7月1日发布。",
            "source": "forum.aidlux.com / aimo.aidlux.com",
        },
    ],
    "huggingface": [
        {
            "title": "Gemma 3n E4B/E2B - Google端侧多模态模型，2GB内存即可运行",
            "summary": "Google DeepMind发布，E4B 8B参/4B有效，E2B 5B参/2B有效。MatFormer嵌套架构内存仅传统模型1/2。支持文本+图像+音频三模态，2-3GB内存即可运行，手机/智能手表/边缘设备可部署，2026年4月发布。",
            "source": "huggingface.co/google/gemma-3n-e4b-it",
        },
        {
            "title": "SmolVLM-256M-Instruct - 最小视觉语言模型，<1GB显存手机可跑",
            "summary": "HuggingFaceTB发布，仅2.56亿参数，<1GB显存，普通智能手机可运行。OCR/VQA/文档理解性能超越上一代大模型，支持ONNX/TFLite导出。2026年1月发布，持续在Hugging Face排行榜保持热度。",
            "source": "huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct",
        },
        {
            "title": "Qwen3-ASR-0.6B - 阿里轻量语音识别，52种语言+22种方言，超越Whisper",
            "summary": "约0.9B参数，RTX 3060可运行。Clean WER 5.76%超越Whisper-large-v3（7.44%）。支持52种语言+22种中文方言（开源ASR最强），流式/离线统一模式。Apache 2.0可免费商用，已有Rust移植/OpenVINO加速生态。",
            "source": "huggingface.co/Qwen/Qwen3-ASR-0.6B",
        },
    ],
}

# ==================== 构建卡片 ====================
CATEGORY_CONFIG = [
    ("kickstarter", "众筹新品", "\U0001f4b0", "Kickstarter 端侧AI硬件众筹新品"),
    ("github", "开源项目", "\U0001f680", "GitHub Trending TinyML/Edge AI"),
    ("industry", "产业资讯", "\U0001f4f0", "智次方/量子位 端侧AI产业动态"),
    ("st_nxp", "原厂工具", "\U0001f527", "ST NXP 原厂工具链更新"),
    ("aidlux", "社区项目", "\U0001f465", "AidLux 社区实战案例"),
    ("huggingface", "轻量模型", "\U0001f9e0", "Hugging Face 端侧可部署模型"),
]

def build_card_json():
    elements = []

    for key, label, emoji, desc in CATEGORY_CONFIG:
        items = NEWS_ITEMS.get(key, [])
        if not items:
            continue
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"**{emoji} {label}** — {desc}",
            },
        })
        for i, item in enumerate(items[:3], 1):
            src = f"\n\U0001f4ce 来源：{item['source']}" if item.get("source") else ""
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{i}. {item['title']}**\n{item['summary']}{src}",
                },
            })

    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"Trae端侧AI学习日报 | {DATE_STR} {WEEKDAY} | 覆盖6大平台：Kickstarter/GitHub/智次方&量子位/ST&NXP/AidLux/HuggingFace",
            }
        ],
    })

    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"端侧AI学习日报 | {DATE_STR}",
            },
            "template": "indigo",
        },
        "elements": elements,
    }
    return card


def save_markdown():
    """保存日报到本地 Markdown 文件"""
    out_dir = os.path.join(RESEARCH_DIR, "daily")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"daily_{DATE_FILE}.md")

    lines = [
        f"# 端侧AI学习日报 | {DATE_STR} {WEEKDAY}",
        f"",
        f"> 自动抓取自：Kickstarter / GitHub Trending / 智次方&量子位 / ST&NXP / AidLux / Hugging Face",
        f"",
    ]

    for key, label, emoji, desc in CATEGORY_CONFIG:
        items = NEWS_ITEMS.get(key, [])
        if not items:
            continue
        lines.append(f"---")
        lines.append(f"## {emoji} {label} — {desc}")
        lines.append(f"")
        for i, item in enumerate(items[:3], 1):
            src = f" — 来源：{item['source']}" if item.get("source") else ""
            lines.append(f"### {i}. {item['title']}")
            lines.append(f"")
            lines.append(f"{item['summary']}{src}")
            lines.append(f"")

    lines.append(f"---")
    lines.append(f"*Trae端侧AI学习日报 | {DATE_STR} {WEEKDAY}*")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[INFO] 本地日报已保存: {out_path}")
    return out_path


def main():
    print("=" * 60)
    print(f"  端侧AI学习日报 - {DATE_STR} ({WEEKDAY})")
    print("=" * 60)

    # 0. 加载飞书凭证
    secrets = load_secrets()
    app_id = secrets["app_id"]
    app_secret = secrets["app_secret"]
    chat_id = secrets["chat_id"]

    # 1. 保存本地 Markdown
    print(f"\n[STEP 1] 保存本地日报 ...")
    md_path = save_markdown()

    # 2. 构建卡片
    print(f"\n[STEP 2] 构建 interactive 卡片 ...")
    card = build_card_json()
    card_str = json.dumps(card, ensure_ascii=False, indent=2)
    print(f"  卡片 JSON 长度: {len(card_str)} 字符")

    # 3. 发送到飞书
    print(f"\n[STEP 3] 推送飞书群聊 {chat_id} ...")
    try:
        message_id = send_interactive_card(chat_id, card, app_id=app_id, app_secret=app_secret)
        print(f"  推送完成！message_id: {message_id}")
    except Exception as e:
        print(f"[ERROR] 推送失败: {e}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  完成！日报已保存至: {md_path}")
    print(f"  飞书 message_id: {message_id}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()