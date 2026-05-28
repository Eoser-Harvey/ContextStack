# AI/Agent 开源仓库资源合集

> 来源: [ai-agent-repos-analysis](https://github.com/Eoser-Harvey/ai-agent-repos-analysis) (Forked from 0xsatoshis)
> 整理时间: 2026-05-28
> 共收录 165 个 GitHub 仓库，覆盖 7 大分类

---

## 快速结论

| 目标 | 优先看 | 原因 |
|---|---|---|
| 本地图片生成工作流 | ComfyUI、Stable Diffusion WebUI、Diffusers | 生态成熟，可扩展性强 |
| 图片增强/修复 | Real-ESRGAN、GFPGAN、Segment Anything、GroundingDINO | 可作为生成前后处理模块 |
| 人脸识别/换脸 | DeepFace、FaceFusion、Deep-Live-Cam | 工具成熟，但要注意合规和授权 |
| 语音识别 | Whisper、whisper.cpp、NeMo、ESPnet | 稳定、生态广，适合本地或服务端 |
| 中文语音生成 | VoxCPM、Piper、Bark、Coqui TTS | 中文生成和本地 TTS 可组合验证 |
| 视频生成/自动化 | MoneyPrinterTurbo、Remotion、HyperFrames、MoviePy、FFmpeg | 从短视频自动化到工程化渲染都有覆盖 |
| 自媒体采集与生产 | yt-dlp、Firecrawl、Scrapling、browser-use、MoneyPrinterTurbo | 覆盖采集、清洗、浏览器自动化、生成 |
| 金融研究/回测 | OpenBB、Qlib、vn.py、Backtrader、TradingAgents | 研究和回测优先，实盘需谨慎 |
| 设计系统/组件 | shadcn-ui、Ant Design、MUI、Storybook、Tailwind CSS | 组件和工程生态强 |
| Agent 编程工作流 | Codex、OpenHands、deer-flow、OpenClaw、AutoGen、LangGraph | 覆盖 CLI、软件工程、多 Agent 编排 |
| Agent 技能资产 | anthropics/skills、superpowers、agent-skills、MiniMax-AI/skills | 适合沉淀工作流和提示资产 |
| 浏览器/桌面自动化 | agent-s、TuriX-CUA、browser-use、Playwright、Peekaboo | 要做权限隔离、日志审计和账号风控 |

---

## 一、图片生成与处理 (18个)

| 序号 | 仓库 | 描述 | Stars | 许可证 | 更新时间 | 团队/作者 | 备注 |
|------|------|------|-------|--------|----------|-----------|------|
| 1 | [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) | 节点式生成工作流 | 114.6k | GPL-3.0 | 2026-05-26 | Comfy Org | 本地图片工作流首选，生态强；部署和显存成本较高 |
| 2 | [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) | SD 网页生成界面 | 163.3k | AGPL-3.0 | 2026-03-02 | AUTOMATIC1111 | 插件和资料最多；AGPL 商业复用要谨慎 |
| 3 | [huggingface/diffusers](https://github.com/huggingface/diffusers) | 扩散模型库 | 33.7k | Apache-2.0 | 2026-05-26 | Hugging Face | 工程化调用模型更合适；需要自己搭 UI/流程 |
| 4 | [facebookresearch/segment-anything](https://github.com/facebookresearch/segment-anything) | 图像分割模型 | 54.2k | Apache-2.0 | 2024-09-18 | Meta | 抠图/分割基础能力强；模型和算力另算 |
| 5 | [lllyasviel/ControlNet](https://github.com/lllyasviel/ControlNet) | 可控图像生成 | 33.9k | Apache-2.0 | 2024-02-25 | lllyasviel | 姿态/边缘/深度控制经典方案；维护节奏偏旧 |
| 6 | [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | 图像视频超分 | 35.6k | BSD-3-Clause | 2024-08-06 | Xintao | 图片/视频增强实用；更新偏旧但仍常用 |
| 7 | [TencentARC/GFPGAN](https://github.com/TencentARC/GFPGAN) | 人脸修复增强 | 37.5k | NOASSERTION | 2024-07-26 | 腾讯 ARC Lab | 人脸修复效果好；许可证不清需核实 |
| 8 | [serengil/deepface](https://github.com/serengil/deepface) | 人脸识别分析库 | 22.8k | MIT | 2026-05-13 | Sefik Serengil | 人脸识别/分析成熟；涉及隐私合规 |
| 9 | [facefusion/facefusion](https://github.com/facefusion/facefusion) | 人脸融合工具 | 28.4k | NOASSERTION | 2026-05-26 | FaceFusion | 活跃、可落地；换脸场景需合规审查 |
| 10 | [lllyasviel/Fooocus](https://github.com/lllyasviel/Fooocus) | 轻量图像生成 | 49.0k | GPL-3.0 | 2025-12-01 | lllyasviel | 上手简单；扩展性不如 ComfyUI |
| 11 | [Stability-AI/generative-models](https://github.com/Stability-AI/generative-models) | 扩散模型代码 | 27.2k | MIT | 2025-12-16 | Stability AI | 适合研究模型本体；落地需工程封装 |
| 12 | [IDEA-Research/GroundingDINO](https://github.com/IDEA-Research/GroundingDINO) | 开放词检测 | 10.2k | Apache-2.0 | 2024-08-12 | IDEA Research | 与 SAM/自动标注组合价值高；部署成本较高 |
| 13 | [antvis/Infographic](https://github.com/antvis/Infographic) | AI 信息图生成渲染框架 | 5.1k | MIT | 2026-05-06 | 蚂蚁 AntV | AI 驱动的信息图生成渲染框架 |
| 14 | [EvoLinkAI/awesome-gpt-image-2-API-and-Prompts](https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts) | 图像 API 提示集 | 15.6k | CC0-1.0 | 2026-05-22 | EvoLinkAI | 提示词积累有价值；依赖具体模型效果 |
| 15 | [freestylefly/awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2) | 图像提示资源库 | 6.6k | MIT | 2026-05-25 | 苍何 | 适合做提示素材库；不是生产工具 |
| 16 | [YouMind-OpenLab/awesome-gpt-image-2](https://github.com/YouMind-OpenLab/awesome-gpt-image-2) | GPT 图像提示集 | 6.7k | NOASSERTION | 2026-05-26 | YouMind OpenLab | 活跃；许可证不清 |
| 17 | [YouMind-OpenLab/awesome-nano-banana-pro-prompts](https://github.com/YouMind-OpenLab/awesome-nano-banana-pro-prompts) | Gemini 图像生成提示词库 | 12.2k | NOASSERTION | 2026-05-26 | YouMind OpenLab | Google Gemini 图像生成提示词 10000+；许可证不清 |
| 18 | [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills) | 宝玉技能合集 | 19.6k | 未声明 | 2026-05-26 | 宝玉 | 技能资产可参考；复用需确认授权 |

---

## 二、语音识别与合成 (12个)

| 序号 | 仓库 | 描述 | Stars | 许可证 | 更新时间 | 团队/作者 | 备注 |
|------|------|------|-------|--------|----------|-----------|------|
| 1 | [openai/whisper](https://github.com/openai/whisper) | 通用语音识别 | 100.6k | MIT | 2026-04-15 | OpenAI | ASR 首选基线，生态广 |
| 2 | [ggml-org/whisper.cpp](https://github.com/ggml-org/whisper.cpp) | 本地 Whisper 推理 | 50.2k | MIT | 2026-05-26 | ggml | 本地低成本部署优秀；功能聚焦推理 |
| 3 | [NVIDIA-NeMo/NeMo](https://github.com/NVIDIA-NeMo/NeMo) | LLM/语音/多模态 AI 框架 | 17.3k | Apache-2.0 | 2026-05-26 | NVIDIA | 企业级 LLM/语音/多模态框架；部署较重 |
| 4 | [espnet/espnet](https://github.com/espnet/espnet) | 端到端语音套件 | 9.8k | Apache-2.0 | 2026-05-25 | ESPnet | 研究和训练能力强；上手成本高 |
| 5 | [OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM) | 多语言 TTS 与声音克隆 | 19.9k | Apache-2.0 | 2026-05-22 | 清华/面壁智能 | 多语言 TTS + 声音设计 + 声音克隆；模型资源另算 |
| 6 | [rhasspy/piper](https://github.com/rhasspy/piper) | 本地 TTS 系统 | 11.0k | MIT | 2025-08-26 | Rhasspy | 本地 TTS 轻量实用；音色质量需实测 |
| 7 | [suno-ai/bark](https://github.com/suno-ai/bark) | 生成式语音模型 | 39.1k | MIT | 2024-08-19 | Suno | 生成能力强；维护偏旧 |
| 8 | [coqui-ai/TTS](https://github.com/coqui-ai/TTS) | 开源 TTS 工具箱 | 45.4k | MPL-2.0 | 2024-08-16 | Coqui | 星标高、功能全；维护偏旧 |
| 9 | [snakers4/silero-models](https://github.com/snakers4/silero-models) | 轻量预训练 TTS 模型 | 5.9k | NOASSERTION | 2026-05-20 | Silero | 轻量模型适合边缘验证；授权需核实 |
| 10 | [microsoft/SpeechT5](https://github.com/microsoft/SpeechT5) | 语音文本预训练 | 1.4k | MIT | 2024-04-24 | 微软 | 研究参考价值高；更新偏旧 |
| 11 | [abus-aikorea/voice-pro](https://github.com/abus-aikorea/voice-pro) | TTS/语音克隆/音频处理工作台 | 10.3k | GPL-3.0 | 2025-12-05 | ABUS | 集成 TTS/声音克隆/Whisper/人声分离/翻译；需实测稳定性 |
| 12 | [mozilla/DeepSpeech](https://github.com/mozilla/DeepSpeech) | 离线语音识别 | 26.8k | MPL-2.0 | 2025-06-19 | Mozilla | 历史项目参考；新项目优先 Whisper 系 |

---

## 三、视频生成与处理 (27个)

| 序号 | 仓库 | 描述 | Stars | 许可证 | 更新时间 | 团队/作者 | 备注 |
|------|------|------|-------|--------|----------|-----------|------|
| 1 | [FFmpeg/FFmpeg](https://github.com/FFmpeg/FFmpeg) | 音视频处理核心 | 60.5k | NOASSERTION | 2026-05-26 | FFmpeg | 所有视频自动化底座；许可证细节需按组件核实 |
| 2 | [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | React 生成视频 | 48.1k | NOASSERTION | 2026-05-26 | Remotion | 工程化视频渲染强；商业授权需核实 |
| 3 | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | HTML 视频生成框架 | 21.5k | Apache-2.0 | 2026-05-26 | HeyGen | 适合代码化视频、字幕、动画 |
| 4 | [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | 一键短视频生成 | 59.8k | MIT | 2026-05-26 | Harry | 短视频自动化最值得先看；API/素材/平台成本另算 |
| 5 | [Zulko/moviepy](https://github.com/Zulko/moviepy) | Python 视频剪辑 | 14.6k | MIT | 2026-03-07 | Zulko | Python 自动剪辑实用；复杂渲染不如 Remotion |
| 6 | [mifi/lossless-cut](https://github.com/mifi/lossless-cut) | 无损视频剪切 | 40.7k | GPL-2.0 | 2026-05-23 | Mikael Finstad | 素材切割非常实用；不是生成框架 |
| 7 | [obsproject/obs-studio](https://github.com/obsproject/obs-studio) | 直播录屏软件 | 72.7k | GPL-2.0 | 2026-05-23 | OBS Project | 录制/直播基础能力强；二开成本高 |
| 8 | [hacksider/Deep-Live-Cam](https://github.com/hacksider/Deep-Live-Cam) | 实时换脸工具 | 93.4k | AGPL-3.0 | 2026-05-24 | hacksider | 社区强、活跃；换脸合规和 AGPL 风险高 |
| 9 | [AIDC-AI/Pixelle-Video](https://github.com/AIDC-AI/Pixelle-Video) | AI 全自动短视频引擎 | 20.0k | Apache-2.0 | 2026-05-18 | AIDC-AI | 全自动短视频引擎；部署成本高 |
| 10 | [MemeCalculate/moyin-creator](https://github.com/MemeCalculate/moyin-creator) | AI 影视生产级工具 | 3.7k | AGPL-3.0 | 2026-05-25 | MemeCalculate | 支持 Seedance 2.0 / 剧本到成片全流程；AGPL 商用限制 |
| 11 | [elebumm/RedditVideoMakerBot](https://github.com/elebumm/RedditVideoMakerBot) | Reddit 视频生成 | 12.3k | GPL-3.0 | 2026-05-25 | Lewis Menelaws | 自动化链路成熟；内容平台规则风险 |
| 12 | [opentoonz/opentoonz](https://github.com/opentoonz/opentoonz) | 二维动画制作 | 6.8k | NOASSERTION | 2026-05-26 | OpenToonz | 动画制作入口；不是 AI 自动化工具 |
| 13 | [zhouxiaoka/autoclip](https://github.com/zhouxiaoka/autoclip) | AI 高光提取与自动剪辑 | 5.5k | MIT | 2026-05-08 | Kris K | AI 智能高光提取与二创剪辑工具；部署较重 |
| 14 | [browser-use/video-use](https://github.com/browser-use/video-use) | AI Agent 视频剪辑工具 | 8.5k | MIT | 2026-05-15 | Browser Use | 用 AI 编程代理剪辑视频；方向新，成熟度需实测 |
| 15 | [HKUDS/ViMax](https://github.com/HKUDS/ViMax) | Agent 驱动一站式视频生成 | 7.7k | MIT | 2026-05-26 | 港大数据智能实验室 | 导演/编剧/制片/生成一体化；落地需二次工程化 |
| 16 | [facebookresearch/pytorchvideo](https://github.com/facebookresearch/pytorchvideo) | 视频理解研究库 | 3.6k | Apache-2.0 | 2026-05-05 | Meta | 视频理解研究可用；不是生成工具 |
| 17 | [PaddlePaddle/PaddleVideo](https://github.com/PaddlePaddle/PaddleVideo) | 视频理解工具箱 | 1.7k | Apache-2.0 | 2025-02-12 | 百度 PaddlePaddle | 中文生态可参考；活跃度一般 |
| 18 | [XPixelGroup/BasicSR](https://github.com/XPixelGroup/BasicSR) | 视频图像修复 | 8.3k | Apache-2.0 | 2024-07-21 | XPixelGroup | 修复/超分基础库；维护偏旧 |
| 19 | [PeterL1n/BackgroundMattingV2](https://github.com/PeterL1n/BackgroundMattingV2) | 视频背景抠像 | 7.2k | MIT | 2024-06-19 | Peter Lin | 抠像方向实用；维护偏旧 |
| 20 | [AliaksandrSiarohin/first-order-model](https://github.com/AliaksandrSiarohin/first-order-model) | 图像驱动动画 | 15.0k | MIT | 2024-11-14 | Aliaksandr Siarohin | 经典研究项目；新项目需评估替代方案 |
| 21 | [chatfire-AI/huobao-drama](https://github.com/chatfire-AI/huobao-drama) | AI 一站式短剧生成平台 | 12.5k | 未声明 | 2026-05-21 | AI 火宝 | 一句话生成完整短剧；许可证不清 |
| 22 | [alecm20/story-flicks](https://github.com/alecm20/story-flicks) | 故事视频生成 | 2.4k | 未声明 | 2025-03-12 | alecm20 | 场景可参考；许可证不清 |
| 23 | [yuanzhongqiao/deep-comedy-pro](https://github.com/yuanzhongqiao/deep-comedy-pro) | AI 短剧工厂 | 4 | 未声明 | 2026-05-10 | yuanzhongqiao | 早期项目；需验证质量 |
| 24 | [happyhorseai/happyhorse](https://github.com/happyhorseai/happyhorse) | 文本/图片转 1080p 电影视频 | 132 | 未声明 | 2026-04-08 | HappyHorse AI | 文本或图片生成电影级视频；成熟度和授权不清 |
| 25 | [ltaoo/wx_channels_download](https://github.com/ltaoo/wx_channels_download) | 视频号下载器 | 6.2k | NOASSERTION | 2026-05-24 | ltaoo | 视频号素材入口；平台规则风险 |
| 26 | [jianshuo/claude-skills](https://github.com/jianshuo/claude-skills) | 视频制作 Claude 技能集 | 62 | MIT | 2026-05-26 | 建硕 | 转录/翻译/配音/多机位/字幕/重构等视频技能集 |
| 27 | [TencentARC/VQFR](https://github.com/TencentARC/VQFR) | 人脸视频修复 | 354 | NOASSERTION | 2022-12-15 | 腾讯 ARC Lab | 可作修复参考；维护较旧 |

---

## 四、自媒体与数据采集 (17个)

| 序号 | 仓库 | 描述 | Stars | 许可证 | 更新时间 | 团队/作者 | 备注 |
|------|------|------|-------|--------|----------|-----------|------|
| 1 | [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) | 强力媒体下载器 | 165.9k | Unlicense | 2026-05-25 | yt-dlp | 素材采集首选；需遵守平台条款 |
| 2 | [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | AI 网页抓取与结构化 | 124.9k | AGPL-3.0 | 2026-05-26 | Firecrawl | 面向 AI Agent 的网页搜索、抓取和清洗；AGPL 和服务成本需注意 |
| 3 | [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) | 自适应网页抓取框架 | 54.4k | BSD-3-Clause | 2026-05-18 | Karim Shoair | 自适应抓取框架，从单请求到全站爬取；许可清晰 |
| 4 | [browser-use/browser-use](https://github.com/browser-use/browser-use) | 浏览器自动化代理 | 95.7k | MIT | 2026-05-26 | Browser Use | 可处理复杂网页流程；账号风控要重视 |
| 5 | [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | 智能体开发平台 | 137.7k | MIT | 2026-05-26 | LangChain | 内容生成和工具编排生态强；框架复杂度高 |
| 6 | [soimort/you-get](https://github.com/soimort/you-get) | 网页媒体下载 | 56.9k | NOASSERTION | 2026-04-30 | Mort Yao | 素材下载常用；授权需核实 |
| 7 | [iawia002/lux](https://github.com/iawia002/lux) | 快速视频下载 | 31.4k | MIT | 2026-03-29 | Xinzhao Xu | 简洁备选 |
| 8 | [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | 全网内容搜索阅读代理 | 20.3k | MIT | 2026-05-18 | Pnant | Twitter/Reddit/YouTube/B站/小红书全网搜索阅读；零 API 费用 |
| 9 | [yikart/AiToEarn](https://github.com/yikart/AiToEarn) | AI 赚钱导航 | 16.7k | MIT | 2026-05-21 | yikart | 适合找项目线索；不是生产框架 |
| 10 | [joeseesun/qiaomu-anything-to-notebooklm](https://github.com/joeseesun/qiaomu-anything-to-notebooklm) | 资料转 NotebookLM | 4.7k | MIT | 2026-04-28 | 向阳乔木 | 内容整理实用；依赖 NotebookLM 工作流 |
| 11 | [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) | 跨平台话题深度研究技能 | 26.6k | MIT | 2026-05-22 | Matt Van Horn | 跨 Reddit/X/YouTube/HN/Polymarket 综合研究；API 成本另算 |
| 12 | [KKKKhazix/khazix-skills](https://github.com/KKKKhazix/khazix-skills) | 内容技能合集 | 11.9k | MIT | 2026-05-08 | Khazix | 内容流程可参考；需筛选质量 |
| 13 | [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) | 中文 AI 降痕 | 8.4k | MIT | 2026-01-19 | 歸藏 | 文案处理可参考；效果需实测 |
| 14 | [huangserva/skill-prompt-generator](https://github.com/huangserva/skill-prompt-generator) | AI 人像 Prompt 生成系统 | 1.4k | 未声明 | 2026-05-10 | huangserva | 从特征库智能组合生成人像描述 Prompt；许可证不清 |
| 15 | [CheeMao/ai-content](https://github.com/CheeMao/ai-content) | AI 内容采集创作发布系统 | 247 | NOASSERTION | 2026-03-20 | CheeMao | 采集、选题、创作、小红书卡图、发布全流程；许可证不清 |
| 16 | [jackwener/xiaohongshu-cli](https://github.com/jackwener/xiaohongshu-cli) | 小红书命令行 | 2.0k | 未声明 | 2026-03-21 | jakevin | 小红书场景明确；账号和平台风控高 |
| 17 | [hekaixin66-sketch/xiaohongshuritter](https://github.com/hekaixin66-sketch/xiaohongshuritter) | 小红书多账号并发 MCP | 134 | 未声明 | 2026-04-05 | hekaixin66 | 多账号多并发 MCP 服务；授权和平台规则风险 |

---

## 五、金融研究与量化 (10个)

| 序号 | 仓库 | 描述 | Stars | 许可证 | 更新时间 | 团队/作者 | 备注 |
|------|------|------|-------|--------|----------|-----------|------|
| 1 | [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | 金融数据平台 | 68.1k | NOASSERTION | 2026-05-26 | OpenBB | 投研数据入口强；数据源可能收费 |
| 2 | [microsoft/qlib](https://github.com/microsoft/qlib) | AI 量化平台 | 43.5k | MIT | 2026-04-22 | 微软 | AI 量化研究首选之一 |
| 3 | [vnpy/vnpy](https://github.com/vnpy/vnpy) | 量化交易框架 | 41.0k | MIT | 2026-05-27 | vn.py | 量化交易框架；实盘需谨慎 |
| 4 | [backtrader/backtrader](https://github.com/backtrader/backtrader) | Python 回测框架 | 12.8k | GPL-3.0 | 2025-08-15 | backtrader | Python 回测框架；实盘需谨慎 |
| 5 | [microsoft/DeepSpeed](https://github.com/microsoft/DeepSpeed) | 深度学习训练优化 | 33.5k | MIT | 2026-05-26 | 微软 | 深度学习训练优化；不是金融专用 |
| 6 | [hummingbot/hummingbot](https://github.com/hummingbot/hummingbot) | 加密货币交易机器人 | 8.5k | Apache-2.0 | 2026-05-20 | Hummingbot | 加密货币交易机器人；实盘需谨慎 |
| 7 | [StockSharp/StockSharp](https://github.com/StockSharp/StockSharp) | 股票/加密货币交易 | 6.8k | Apache-2.0 | 2026-05-15 | StockSharp | 股票/加密货币交易；实盘需谨慎 |
| 8 | [firmai/financial-machine-learning](https://github.com/firmai/financial-machine-learning) | 金融机器学习资源 | 12.5k | MIT | 2026-04-10 | firmai | 金融机器学习资源列表 |
| 9 | [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | 深度强化学习金融 | 10.2k | MIT | 2026-05-10 | AI4Finance | 深度强化学习金融应用 |
| 10 | [tradingview/tradingview-jsapi-tutorial](https://github.com/tradingview/tradingview-jsapi-tutorial) | TradingView JS API | 2.1k | MIT | 2025-12-01 | TradingView | TradingView JS API 教程 |

---

## 六、Agent 编程与自动化 (25个)

| 序号 | 仓库 | 描述 | Stars | 许可证 | 更新时间 | 团队/作者 | 备注 |
|------|------|------|-------|--------|----------|-----------|------|
| 1 | [anthropics/claude-code](https://github.com/anthropics/claude-code) | Claude Code CLI | 8.5k | MIT | 2026-05-26 | Anthropic | Claude Code CLI 工具 |
| 2 | [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) | AI 软件开发代理 | 52.3k | MIT | 2026-05-26 | All-Hands AI | AI 软件开发代理平台 |
| 3 | [browser-use/browser-use](https://github.com/browser-use/browser-use) | 浏览器自动化代理 | 95.7k | MIT | 2026-05-26 | Browser Use | 浏览器自动化代理；已列在自媒体分类 |
| 4 | [langchain-ai/langchain](https://github.com/langchain-ai/langchain) | 智能体开发平台 | 137.7k | MIT | 2026-05-26 | LangChain | 智能体开发平台；已列在自媒体分类 |
| 5 | [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 智能体工作流编排 | 12.5k | MIT | 2026-05-20 | LangChain | 智能体工作流编排框架 |
| 6 | [microsoft/autogen](https://github.com/microsoft/autogen) | 多智能体对话框架 | 35.6k | MIT | 2026-05-26 | 微软 | 多智能体对话框架 |
| 7 | [OpenClaw/OpenClaw](https://github.com/OpenClaw/OpenClaw) | AI Agent 操作系统交互 | 5.2k | MIT | 2026-05-15 | OpenClaw | AI Agent 操作系统交互框架 |
| 8 | [mannaandpoem/OpenManus](https://github.com/mannaandpoem/OpenManus) | 开源 Manus 实现 | 42.8k | MIT | 2026-05-26 | OpenManus | 开源 Manus AI Agent 实现 |
| 9 | [camel-ai/camel](https://github.com/camel-ai/camel) | 多智能体框架 | 12.5k | Apache-2.0 | 2026-05-20 | CAMEL | 多智能体框架 |
| 10 | [TransformerOptimus/SuperAGI](https://github.com/TransformerOptimus/SuperAGI) | 自主 AI 代理框架 | 15.6k | MIT | 2026-04-15 | SuperAGI | 自主 AI 代理框架 |
| 11 | [reworkd/AgentGPT](https://github.com/reworkd/AgentGPT) | 浏览器自主 AI 代理 | 32.5k | MIT | 2026-05-10 | Reworkd | 浏览器自主 AI 代理 |
| 12 | [Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | 自主 GPT 实验 | 170.2k | MIT | 2026-05-26 | Significant Gravitas | 自主 GPT 实验项目 |
| 13 | [yoheinakajima/babyagi](https://github.com/yoheinakajima/babyagi) | 任务驱动自主代理 | 20.1k | MIT | 2025-12-01 | Yohei Nakajima | 任务驱动自主代理 POC |
| 14 | [joonspk-research/generative_agents](https://github.com/joonspk-research/generative_agents) | 生成式智能体 | 19.5k | MIT | 2025-08-15 | Joon Park | 生成式智能体研究 |
| 15 | [microsoft/promptflow](https://github.com/microsoft/promptflow) | LLM 工作流开发 | 9.8k | MIT | 2026-05-20 | 微软 | LLM 工作流开发工具 |
| 16 | [e2b-dev/E2B](https://github.com/e2b-dev/E2B) | AI 代理代码执行沙箱 | 12.3k | Apache-2.0 | 2026-05-15 | E2B | AI 代理代码执行沙箱 |
| 17 | [Aider-AI/aider](https://github.com/Aider-AI/aider) | AI 编程助手 | 28.5k | Apache-2.0 | 2026-05-26 | Aider AI | AI 编程助手，支持多文件编辑 |
| 18 | [continuedev/continue](https://github.com/continuedev/continue) | 开源 AI 代码助手 | 25.6k | Apache-2.0 | 2026-05-26 | Continue Dev | 开源 AI 代码助手 IDE 插件 |
| 19 | [voideditor/void](https://github.com/voideditor/void) | 开源 AI 编辑器 | 12.8k | Apache-2.0 | 2026-05-20 | Void Editor | 开源 AI 编辑器 |
| 20 | [codex-oss/codex](https://github.com/codex-oss/codex) | OpenAI Codex CLI | 15.2k | MIT | 2026-05-26 | OpenAI | OpenAI Codex CLI 工具 |
| 21 | [wonderwhy-er/DesktopCommanderMCP](https://github.com/wonderwhy-er/DesktopCommanderMCP) | 桌面控制 MCP | 3.5k | MIT | 2026-05-15 | wonderwhy-er | 桌面控制 MCP Server |
| 22 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | MCP 官方服务器集合 | 35.6k | MIT | 2026-05-26 | Anthropic | MCP 官方服务器集合 |
| 23 | [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | Pydantic AI Agent | 8.5k | MIT | 2026-05-20 | Pydantic | Pydantic AI Agent 框架 |
| 24 | [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 多智能体编排框架 | 26.8k | MIT | 2026-05-26 | CrewAI | 多智能体编排框架 |
| 25 | [deepset-ai/haystack](https://github.com/deepset-ai/haystack) | NLP 框架 | 15.6k | Apache-2.0 | 2026-05-20 | deepset | NLP 框架，支持 RAG |

---

## 七、设计系统与前端组件 (15个)

| 序号 | 仓库 | 描述 | Stars | 许可证 | 更新时间 | 团队/作者 | 备注 |
|------|------|------|-------|--------|----------|-----------|------|
| 1 | [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | React 组件库 | 82.5k | MIT | 2026-05-26 | shadcn | React 组件库，设计系统 |
| 2 | [ant-design/ant-design](https://github.com/ant-design/ant-design) | 企业级 UI 设计语言 | 93.2k | MIT | 2026-05-26 | Ant Design | 企业级 UI 设计语言和 React 组件库 |
| 3 | [mui/material-ui](https://github.com/mui/material-ui) | React UI 组件库 | 94.5k | MIT | 2026-05-26 | MUI | React UI 组件库 |
| 4 | [tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss) | 实用优先 CSS 框架 | 82.3k | MIT | 2026-05-26 | Tailwind Labs | 实用优先 CSS 框架 |
| 5 | [storybookjs/storybook](https://github.com/storybookjs/storybook) | UI 组件开发环境 | 85.6k | MIT | 2026-05-26 | Storybook | UI 组件开发和文档环境 |
| 6 | [radix-ui/primitives](https://github.com/radix-ui/primitives) | 无样式 UI 组件原语 | 15.6k | MIT | 2026-05-20 | Radix UI | 无样式 UI 组件原语 |
| 7 | [chadcn-ui/chadcn-ui](https://github.com/chadcn-ui/chadcn-ui) | 组件库 CLI | 12.5k | MIT | 2026-05-15 | chadcn | 组件库 CLI 工具 |
| 8 | [nextui-org/nextui](https://github.com/nextui-org/nextui) | React UI 库 | 22.5k | MIT | 2026-05-26 | NextUI | React UI 库 |
| 9 | [chakra-ui/chakra-ui](https://github.com/chakra-ui/chakra-ui) | React 组件库 | 36.8k | MIT | 2026-05-20 | Chakra UI | React 组件库 |
| 10 | [mantinedev/mantine](https://github.com/mantinedev/mantine) | React 组件库 | 25.6k | MIT | 2026-05-26 | Mantine | React 组件库 |
| 11 | [ark-ui/ark](https://github.com/ark-ui/ark) | 无头组件库 | 8.5k | MIT | 2026-05-15 | Ark UI | 无头组件库，多框架支持 |
| 12 | [primer/css](https://github.com/primer/css) | GitHub 设计系统 | 12.3k | MIT | 2026-05-10 | GitHub Primer | GitHub 设计系统 CSS 框架 |
| 13 | [carbon-design-system/carbon](https://github.com/carbon-design-system/carbon) | IBM 设计系统 | 7.8k | Apache-2.0 | 2026-05-05 | IBM Carbon | IBM 设计系统 |
| 14 | [atlassian/design-system](https://github.com/atlassian/design-system) | Atlassian 设计系统 | 5.2k | Apache-2.0 | 2026-04-20 | Atlassian | Atlassian 设计系统 |
| 15 | [salesforce-ux/design-system](https://github.com/salesforce-ux/design-system) | Salesforce 设计系统 | 3.5k | BSD-3-Clause | 2026-03-15 | Salesforce | Salesforce Lightning 设计系统 |

---

## 使用建议

### 排序逻辑说明

1. **工程可用性** — 能否直接用于生产/研究工作流，开箱即用的排前面
2. **生态成熟度** — 插件、文档、社区活跃度、周边工具链是否完善
3. **活跃度** — 最后更新时间，维护频率
4. **许可证清晰度** — MIT/Apache 等清晰许可优先，NOASSERTION/未声明的靠后
5. **落地成本和风险** — 部署复杂度、合规风险、外部依赖多少

### 重要提示

- "免费/开源"只指仓库代码本身；模型 API、云服务、交易所、数据源、GPU/Apple Silicon、本地存储、平台账号等可能另行收费
- 实盘交易、换脸、自媒体自动化等场景需特别注意合规和平台规则风险
- 许可证为 NOASSERTION 或未声明的仓库，商业复用前需核实授权

---

## 关联资源

- **Forked from**: [0xsatoshis/ai-agent-repos-analysis](https://github.com/0xsatoshis/ai-agent-repos-analysis)
- **你的 Fork**: [Eoser-Harvey/ai-agent-repos-analysis](https://github.com/Eoser-Harvey/ai-agent-repos-analysis)
- **分类标签**: AI技术、开源工具、资源合集、Agent编程、多媒体处理、金融量化
