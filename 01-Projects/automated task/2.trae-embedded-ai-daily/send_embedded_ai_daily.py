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
RESEARCH_DIR = r"E:\ProjectGroup\AI\ContextStack\01-Projects\family-hub\embedded-ai-research"
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
            "title": "ESP32-CAM宠物监控DIY方案：50元搞定实时直播+PIR运动检测+红外夜视+微信告警",
            "summary": "基于AI-Thinker ESP32-CAM模组(OV2640 200万像素+硬件JPEG编码+MJPEG流式传输)打造的家庭宠物监控系统。手机/PC浏览器直接观看延迟<500ms，支持PIR运动检测触发+红外夜视+微信消息推送告警。基于esp32-camera驱动库开发，支持深度睡眠模式。全套物料<50元，是家庭宠物监控、老人看护、楼道安防的零门槛方案。",
            "source": "CSDN / 头条 2026-05",
        },
        {
            "title": "开源ESP32-S3 EDA-Robot小智AI机器狗(85元)：语音对话+MCP运动控制+DeepSeek",
            "summary": "基于乐鑫ESP32-S3R8N16模组构建的开源AI机器狗，集成INMP441数字麦克风+MAX98357音频功放。通过MCP协议实现语音对话控制机器狗运动(向前走/向后走等)，无需手机App直接唤醒操控。对接DeepSeek大模型实现语音对话。总成本仅85元(ESP32+S3开发板+舵机+传感器全套BOM)。适合儿童陪伴、宠物互动、入门机器人学习的消费级产品。",
            "source": "CSDN / GitHub / 头条 2026-06",
        },
        {
            "title": "ESP-SparkBot：ESP32-S3开源AI桌面机器人，支持DeepSeek/豆包，成本仅150元",
            "summary": "基于乐鑫ESP32-S3构建的开源大模型AI桌面机器人，集成语音交互、图像识别、远程遥控与多媒体功能。支持DeepSeek/OpenAI/通义千问等多模型对话，内置加速度传感器。可变身遥控小车、玩AI骰子游戏。全部开源(Apache 2.0)，复刻物料成本仅150元。适用场景：智能家居控制中枢、儿童AI陪伴、桌面AI助手、轻量安防监控。社区全套教程和3D打印文件已开源。",
            "source": "sparkbot.com.cn / CSDN / 网易 2026-06",
        },
    ],
    "github": [
        {
            "title": "espressif/esp-claw - 乐鑫新开源AI Agent框架：把智能体塞进ESP32，Chat Coding聊天造物",
            "summary": "乐鑫2026重磅开源框架ESP-Claw，运行在ESP32芯片上的AI智能体框架，核心理念Chat Coding(聊天造物)。支持对话定义设备行为、自然语言编程ESP32、记住用户偏好、主动推送消息(微信对话即控制)。四大核心能力：对话定义功能、Agent决策引擎、记忆与个性化、多模态感知交互。把ESP32变成一只能听懂人话、会自己写代码、能记住偏好的AI宠物。社区火爆讨论中。",
            "source": "github.com/espressif/esp-claw",
        },
        {
            "title": "78/xiaozhi-esp32 - 小智AI聊天机器人(Star 20k+)：MCU AI固件第一热门项目",
            "summary": "基于ESP32的MCP语音AI聊天机器人固件(GitHub 20k+ Star)，接入Qwen/DeepSeek大模型，支持语音唤醒、流式ASR、TTS合成、MCP硬件控制。C++开发，MIT协议，ESP32/ESP32-S3双平台持续周更。社区已衍生出机器狗、智能音箱、桌面机器人等多种硬件形态。2026年6月有开发者发表深度源码分析，可打板至4层PCB实现量产。是国内MCU AI应用最火爆的开源项目。",
            "source": "github.com/78/xiaozhi-esp32",
        },
        {
            "title": "espressif/esp-dl - 乐鑫官方深度学习推理库：ESP32全系列AI视觉引擎(1k+ Star)",
            "summary": "乐鑫官方深度学习推理引擎，支持ESP32/S2/S3/C3全系列芯片。深度优化INT8量化推理，ESP32-S3 PIE向量指令7.2倍加速。内置人脸识别、手势检测等模型模板，支持YOLO/MobileNet等常见模型转换。ESP-WHO视觉框架集成ESP-DL，形成完整MCU端AI视觉开发链。适合宠物/人脸识别门禁、手势控制智能家居等消费产品场景。",
            "source": "github.com/espressif/esp-dl",
        },
    ],
    "industry": [
        {
            "title": "2026慕尼黑上海电子展全纪实：TI<$1 AI MCU量产，ST灵巧手芯片<100元，端侧AI赛道爆发",
            "summary": "7月1-3日慕尼黑上海电子展(electronica Shanghai)12万平米、超2000家展商。TI展出MSPM0G5187(TinyEngine NPU 2.56GOPS，批量价<$1)，AI编程工具需求到代码自动闭环。ST主推STM32N6(0.6 TOPS自研Neural-ART NPU)现场演示六自由度灵巧手(芯片成本<100元)。兆易创新展出4套机器人MCU方案，极海半导体电机控制芯片仅3元/颗。英飞凌/NXP/安森美同步展示TinyML端侧AI方案，MCU+NPU全面标配化。",
            "source": "半导体产业纵横 / 科创板日报 / 头条 2026-07-03",
        },
        {
            "title": "乐鑫ESP-Claw开源引爆社区：微信发条指令让ESP32自动写代码执行，硬件开发进入聊天时代",
            "summary": "乐鑫正式开源ESP-Claw框架——在ESP32芯片上运行AI Agent，核心是Chat Coding(聊天造物)。开发者/普通用户通过微信对话即可定义设备行为：\"帮我写一个每隔5分钟检测温度并微信通知的程序\"，ESP32自动编写代码并执行。一切在芯片本地完成，无需PC。Agent引擎+记忆系统+多模感知，让物联网设备从'能联网'进化到'能思考决策'。极端低成本让每个家庭都能拥有AI硬件。",
            "source": "头条 / 搜狐 2026-07",
        },
        {
            "title": "ESP32-S3 + 端侧小模型小型AI产品实战全景分析：十几元芯片支撑四大产品方向",
            "summary": "深度技术分析文章指出，ESP32-S3作为成本仅十几元、集成AI加速指令集的MCU，正成为端侧AI产品化最热平台。四大产品方向：AI语音交互设备(智能音箱/机器人/陪伴)、AI视觉设备(宠物监控/安防/门禁)、AI传感器设备(环境监测/健康/工业异常)、AI综合设备(机器狗/桌面机器人)。关键词识别比ESP32快2-3倍，功耗降低40%。2026年消费端侧AI产品已到批量落地临界点。",
            "source": "头条 / CSDN 2026-07",
        },
    ],
    "st_nxp": [
        {
            "title": "STM32Cube AI Studio正式发布：七年沉淀，全面替代X-CUBE-AI，一站式模型量化/优化/部署",
            "summary": "意法半导体2026年5月正式推出STM32Cube AI Studio独立桌面工具，全面替代X-CUBE-AI。支持模型导入→真实数据量化→优化选项调优→目标硬件基准测试(延迟/内存/精度)→一键生成C代码。搭载ST Edge AI Core引擎，支持脚本运行和工作流自动化。界面由NanoEdge AI Studio团队设计，学习成本低。已开放Windows和Ubuntu版本下载。支持STM32N6/MP2全系AI MCU。",
            "source": "st.com / CSDN 2026-05",
        },
        {
            "title": "NXP i.MX RT700跨界MCU：首款eIQ Neutron NPU，5核异构AI加速172倍，7.5MB SRAM",
            "summary": "NXP i.MX RT700是首款搭载eIQ Neutron NPU的跨界MCU：5核异构(Cortex-M33@325MHz×2+HiFi4 DSP+NPU+Prism GPU)，7.5MB片上SRAM，NPU加速AI推理172倍。已展示实时LLM聊天方案(上位机LLM→端侧推理→TTS播放)。eIQ Neutron SDK 3.0.0(2026年2月发布)支持CNN/RNN/Transformer等全类型网络。eIQ Toolkit提供端到端模型开发和部署。目标可穿戴/消费医疗/智能家居/HMI。",
            "source": "nxp.com / 电子发烧友 2026-06",
        },
        {
            "title": "STM32CubeIDE 2.1.0发布：全新AI MCU项目模板，STM32N6无缝集成Cube.AI",
            "summary": "ST发布STM32CubeIDE 2.1.0版本，新增STM32N6系列AI MCU项目模板，支持直接在IDE中调用STM32Cube AI Studio生成的推理代码。内置STM32N6 Neural-ART NPU配置向导，一键使能AI加速。新版本还增强了FreeRTOS调试视图和功耗分析工具。配合STM32CubeMX 7.0+使用，形成从配置→模型导入→代码生成→调试的完整AI MCU开发闭环。",
            "source": "st.com / CSDN 2026-06",
        },
    ],
    "aidlux": [
        {
            "title": "ESP32-S3 TinyML实战三连：关键词唤醒(80KB/19ms)＋异常检测(35KB/7ms)＋手势识别(220KB/7FPS)",
            "summary": "基于ESP32-S3的3个渐进式TinyML项目全开源。(1)关键词唤醒：INMP441+DS-CNN INT8量化仅80KB，推理19ms，ESP32-S3 PIE向量指令7.2倍加速，双核分工(Core0采集/Core1推理)；(2)振动异常检测：MPU6050+1D卷积自编码器35KB，推理7ms<5%CPU占用，无需异常样本即可训练；(3)实时手势识别：OV2640+ESP-DL+MobileNetV1 220KB，7FPS，MQTT控制智能家居。硬件总成本<100元。",
            "source": "CSDN / 头条 2026-06",
        },
        {
            "title": "ESP32-CAM智能猫眼DIY方案(百元级)：微信小程序+局域网视频监控，零外部依赖",
            "summary": "基于ESP32-CAM+微信小程序的智能猫眼/家庭监控方案，实现局域网视频监控，零外部云服务器依赖。OV2640摄像头实时推流，微信小程序直接拉流观看。支持PIR触发拍照+微信推送+红外夜视。整套硬件成本<100元，可替代市面300-500元智能猫眼产品。适合家庭门口监控、老人看护、宠物活动监测等大众消费场景。",
            "source": "CSDN / 头条 2026-06",
        },
        {
            "title": "ESP32智能环境监测站：LoRa 2.5km传输+休眠20μA+太阳能325天续航，成本<100元",
            "summary": "ESP32-WROOM-32E+FreeRTOS+DHT22+MQ-135+LoRa SX1278+太阳能方案。FreeRTOS Queue实现传感器采集与LoRa发送解耦，RTC定时唤醒+深度休眠仅20μA@3.3V。MQ-135经温湿度补偿(误差≤±12%)，2000mAh锂电+太阳能理论续航325天。已落地智慧农业温湿度监测、小区空气质量网格化监测、工业VOC预警。完整开源固件和PCB文件，材料成本不到100元。",
            "source": "CSDN / 电子发烧友 2026-06",
        },
    ],
    "huggingface": [
        {
            "title": "ARM官方DS-CNN Large INT8全量化(504KB)：MCU端关键词识别首选，Cortex-M4推理<5ms",
            "summary": "ARM官方出品的MCU端关键词识别模型，500K参数，INT8全量化仅504KB。12类关键词(Yes/No/Up/Down等)识别，准确率94.52%。Cortex-M4@96MHz单次推理<5ms，带Ethos-U55 NPU仅<1ms。Apache 2.0协议，原生支持TFLite Micro。可直接部署到ESP32-S3实现语音唤醒功能(AI智能音箱/机器人/桌面助手等的第一步)。",
            "source": "huggingface.co/JahnaviBhansali/DSCNN",
        },
        {
            "title": "MobileNetV3-Small INT8量化(2.55M参数/0.8MB)：ESP32-S3推理150-300ms，HuggingFace 2600万+下载",
            "summary": "2.55M参数轻量图像分类模型，INT8全量化后约0.8MB，HuggingFace 2600万+下载量。ESP32-S3 INT8推理150-300ms(取决于PSRAM/输入尺寸)，Cortex-M7@480MHz约80-150ms。支持TFLite/ONNX格式导出。适合ESP32端侧垃圾分类识别、宠物品种检测、手势分类等轻量视觉应用。搭配ESP-DL进一步优化后可部署到ESP32-CAM类硬件产品。",
            "source": "huggingface.co/timm/mobilenetv3_small_100.lamb_in1k",
        },
        {
            "title": "Hugging Face发布硬件筛选功能(2026.6.30)：按MCU/GPU/NPU过滤模型，TinyML模型可发现性大增",
            "summary": "2026年6月30日Hugging Face重大更新，新增按硬件(MCU/GPU/NPU等)筛选模型功能，开发者可直接筛选出适配ESP32/STM32/Cortex-M等MCU的TinyML模型。同日斯坦福研究显示71.3%的ChatGPT类推理可在端侧完成。HF Hub已托管超90万个模型、20万个数据集。此次更新推动TinyML模型选型效率质的飞跃，端侧AI部署门槛进一步降低。",
            "source": "huggingface.co / 头条 2026-07",
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