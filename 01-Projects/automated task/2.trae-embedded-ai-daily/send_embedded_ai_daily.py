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
            "title": "StackChan M5 - ESP32-S3开源AI桌面机器人，众筹46万美元",
            "summary": "M5Stack推出基于ESP32-S3的AI桌面陪伴机器人，双核240MHz，2寸IPS触屏，双麦克风，30万像素摄像头，NFC模块。支持大模型语音对话、腾讯云接入、MCP协议。100%开源(Apache 2.0)，早鸟价47美元。获Kickstarter官方推荐，4142位支持者。适用场景：智能家居控制中枢、儿童陪伴、桌面AI助手、轻量安防监控。",
            "source": "Kickstarter / M5Stack / 雪球",
        },
        {
            "title": "ESP32-CAM宠物监控系统 - 50元打造家庭宠物监控方案",
            "summary": "基于ESP32-CAM(AI-Thinker)，OV2640 200万像素摄像头，硬件JPEG编码不占CPU。MJPEG流式传输，浏览器直接观看，延迟<500ms。支持PIR运动检测、红外夜视、微信推送告警。ESP32的低功耗特性支持电池供电，全套物料成本不到50元。CSDN社区1k+阅读，27收藏。",
            "source": "CSDN / Espressif官方",
        },
        {
            "title": "ESP32智能环境监测站 - FreeRTOS+LoRa双模，休眠仅20μA",
            "summary": "基于ESP32-WROOM-32E+DHT22+MQ-135，FreeRTOS多任务架构。LoRa SX1278传输距离2.5km(空旷)，RTC定时唤醒+深度睡眠功耗仅20μA@3.3V。MQ-135经温湿度补偿校准，误差≤±12%。2000mAh锂电+太阳能充电，理论续航超325天。已落地智慧农业、工业VOC监测、城市网格化监测。",
            "source": "CSDN / 头条",
        },
    ],
    "github": [
        {
            "title": "78/xiaozhi-esp32 - 小智AI聊天机器人，Star 18.3k，MCU AI第一热门",
            "summary": "基于ESP32的MCP语音AI聊天机器人，接入Qwen/DeepSeek大模型，支持语音唤醒、流式ASR、TTS合成、硬件控制。C++开发，MIT协议，ESP32/ESP32-S3双平台。是国内MCU AI应用领域最火爆的开源项目，18.3k Star。",
            "source": "github.com/78/xiaozhi-esp32",
        },
        {
            "title": "tensorflow/tflite-micro - Google官方MCU推理框架，Star 3k",
            "summary": "Google官方MCU端AI推理框架，支持ARM Cortex-M/ESP32/RISC-V/DSP。INT8量化推理、CMSIS-NN加速、静态内存分配。支持Conv2D/DepthwiseConv/FC/Softmax等核心算子，可运行图像分类、语音识别、姿态检测。模型固件仅几十KB，适合Flash受限MCU。",
            "source": "github.com/tensorflow/tflite-micro",
        },
        {
            "title": "espressif/esp-dl - 乐鑫官方深度学习库，Star 1k+，ESP32专属",
            "summary": "乐鑫官方深度学习推理引擎，支持ESP32/S2/S3/C3全系列。深度优化INT8量化推理，ESP32-S3 PIE向量指令7.2倍加速。支持YOLO11n/MobileNet等模型，工具链支持TFLite→ESP-DL格式转换。是ESP32平台上AI推理的首选方案。",
            "source": "github.com/espressif/esp-dl",
        },
    ],
    "industry": [
        {
            "title": "2026慕尼黑上海电子展：TI发布<$1 AI MCU，ST展灵巧手，MCU + AI成为焦点",
            "summary": "TI展出MSPM0G5187(TinyEngine NPU 2.56GOPS，批量价<$1)，AI辅助编程工具链实现提需求到自动编码闭环。ST主推STM32N6(0.6 TOPS自研NPU)，现场演示六自由度灵巧手(芯片成本<100元)。兆易创新展出4套机器人MCU方案，极海半导体电机控制芯片仅3元/颗。多家厂商共识：边缘AI MCU从零点几TOPS出发，已足撬动智能家居、康养、工业检测等细分场景。",
            "source": "半导体产业纵横 / 钛媒体 2026-07",
        },
        {
            "title": "ESP32-S31重构全屋智能网关：单芯片WiFi 6+BT5.4+Zigbee+Thread+Matter",
            "summary": "乐鑫ESP32-S31-WROOM-3模组在一颗芯片上集成WiFi 6+Bluetooth 5.4+Zigbee 3.0+Thread 1.4+Matter全协议栈，终结传统多模组堆叠方案。WiFi 6 OFDMA/MU-MIMO支持几十台设备同时在线，54路GPIO扩展，兼容HomeKit等生态。面向AI智能交互场景，从DIY到量产均可直接使用。",
            "source": "电子发烧友 elecfans.com 2026-07-01",
        },
        {
            "title": "中微半导MCU+AI战略：全栈工具链+白电AI方案覆盖空调/冰箱/洗衣机",
            "summary": "中微半导在2026慕尼黑上海电子展展出80余款方案，智能语音方案将主控/触控/变频/AI集成一体，覆盖空调/冰箱/洗衣机等白电品类。CMS32F407系列(Cortex-M4@200MHz，1024K Flash+192K SRAM)覆盖消费到工控。FOC灵巧手驱动方案在超小尺寸内集成主控/预驱/MOSFET/LDO。",
            "source": "OFweek / 维科网 2026-07-03",
        },
    ],
    "st_nxp": [
        {
            "title": "STM32Cube.AI v10.0发布：首次支持STM32N6 Neural-ART NPU(600 GOPS)",
            "summary": "ST发布v10.0重大更新，首次支持STM32N6内置Neural-ART NPU(Cortex-M55@800MHz+NPU@1GHz，600 GOPS，3 TOPS/W)。支持TF/PyTorch/ONNX/Scikit-Learn四大框架，推理速度提升70%，Flash/RAM节省75%(vs TFLite Micro)。AI Model Zoo提供60+预训练模型，新增PyTorch原生支持。覆盖全系列STM32(F/L/H/G/N/MP2)。",
            "source": "st.com/stm32cubeai",
        },
        {
            "title": "NXP eIQ Neutron SDK 3.1.3(2026.6.18)+i.MX RT700：5核MCU跑LLM",
            "summary": "NXP eIQ Neutron SDK更新至3.1.3(2026.6.18)，i.MX RT700是首款搭载eIQ Neutron NPU的跨界MCU：5核异构(Cortex-M33@325MHz+HiFi 4 DSP+NPU)，7.5MB SRAM，AI加速172倍。已展示本地LLM聊天方案，证明MCU级别可跑LLM推理。目标可穿戴/医疗/智能家居。",
            "source": "nxp.com/eiq / eepw.com.cn",
        },
        {
            "title": "2026年AI MCU标配时代：TI<$1→ST 600GOPS→NXP 172x→瑞萨256GOPS",
            "summary": "全主流MCU厂商均已量产AI MCU：TI MSPM0G5187(<$1, TinyEngine NPU)、ST STM32N6(600 GOPS)、NXP i.MX RT700(172倍加速)、瑞萨RA8P1(Ethos-U55 256 GOPS)、英飞凌PSoC Edge。MCU+NPU成为新标配，端侧AI推理成本降至1美元级，适合智能家居/康养/可穿戴。",
            "source": "CSDN / 电子产品世界",
        },
    ],
    "aidlux": [
        {
            "title": "AidLux家庭AI安防告警系统：YOLOv5端侧推理+微信实时推送",
            "summary": "AidLux官方社区项目，YOLOv5目标检测(仅检测person类)在Android手机端侧推理，异常图片自动上传七牛云并生成外链，通过喵提醒公众号实时推送告警到微信。aidlite_gpu SDK加速推理，开发效率高，七牛云提供30天免费额度，整体方案成本极低。",
            "source": "forum.aidlux.com",
        },
        {
            "title": "ESP32-CAM宠物监控全流程：MJPEG流+硬件JPEG编码+红外夜视",
            "summary": "CSDN社区1k+阅读的实战项目。OV2640摄像头采集→ESP32硬件JPEG编码→MJPEG流式传输→手机浏览器实时观看，延迟<500ms。支持PIR运动检测、微信告警。全套物料<50元，VGA分辨率流畅运行，是ESP32端侧AI最接地气的消费级产品。",
            "source": "CSDN / forum.aidlux.com",
        },
        {
            "title": "ESP32智能环境监测站：LoRa 2.5km+休眠20μA+太阳能，续航325天",
            "summary": "ESP32+FreeRTOS+DHT22+MQ-135+LoRa SX1278。传感器采集任务与LoRa发送任务通过Queue通信，RTC定时唤醒+深度睡眠(20μA@3.3V)。MQ-135经温湿度补偿校准(误差≤±12%)，2000mAh锂电+太阳能续航超325天。已落地智慧农业、工业VOC监测、城市网格化监测。",
            "source": "CSDN / 电子发烧友",
        },
    ],
    "huggingface": [
        {
            "title": "DS-CNN Large(INT8全量化) - 关键字识别，504KB，Cortex-M4推理<5ms",
            "summary": "Arm官方出品，500K参数，模型文件仅504KB(INT8全量化)。12类关键词识别，准确率94.52%。Cortex-M4@96MHz单次推理<5ms，Ethos-U55仅<1ms。Apache 2.0协议，原生支持Cortex-M MCU，是MCU端关键字识别的首选方案。",
            "source": "huggingface.co/JahnaviBhansali/DSCNN",
        },
        {
            "title": "MobileNetV3-Small(INT8量化~0.8MB) - 图像分类，ESP32-S3可跑",
            "summary": "2.55M参数，INT8量化后约0.8MB，HuggingFace 2600万+下载量。ESP32-S3上INT8推理约150-300ms，Cortex-M7@480MHz约80-150ms，带Ethos-U NPU仅<10ms。支持TFLite/ONNX导出，适合MCU端图像分类(垃圾分类/手势识别/宠物检测)。",
            "source": "huggingface.co/timm/mobilenetv3_small_100.lamb_in1k",
        },
        {
            "title": "YOLOX-Nano LiteRT(0.9M参数) - 目标检测，手机端实时>30fps",
            "summary": "Google LiteRT官方社区维护，2026年7月2日最新发布。0.9M参数，模型仅2.2MB(FP16)，INT8可压缩至~1.1MB。Pixel 8a GPU实时>30fps。GPU原生编译(Focus层折叠为6x6卷积)，零CPU fallback。适合手机端或带GPU的嵌入式Linux设备实时目标检测。",
            "source": "huggingface.co/litert-community/yolox-nano-litert",
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