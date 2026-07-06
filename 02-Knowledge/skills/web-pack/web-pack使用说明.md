# Web-Pack 技能使用说明

## 技能概述

**Web-Pack** 是一个AI Agent技能，用于自动化采集网页主题的完整素材包，解决知识库构建中的原始素材(Raw层)采集问题。

## 核心功能

### 1. 深度网页内容采集
- **智能递归抓取**：从入口链接展开抓取相关有价值链接
- **内容过滤**：自动跳过广告、导航栏等噪音内容
- **图片本地化**：下载所有图片到本地，避免外链失效

### 2. 结构化输出
- **标准文件夹结构**：自动生成层次分明的素材包
- **多格式文档**：生成研究简报、链接清单、图片清单、阅读地图
- **关联关系**：建立内容间的连接关系

### 3. 完整性保障
- **多层抓取策略**：常规HTTP→GitHub API→Jina Reader兜底
- **链接智能判断**：区分核心内容链接和噪音链接
- **完整性检查**：自动检查外链图片残留

## 使用方法

### 基本调用方式
直接对AI Agent说："**帮我采集这几个链接的素材**"

AI Agent会自动识别并调用web-pack技能，参数会自动设置。

### 高级参数配置
如需精细控制，可指定参数：
```
帮我采集这几个链接的素材 --max-depth 2 --max-pages 50
```

### 参数说明
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--max-depth` | 1 | 抓取深度（1=入口页+直接相关链接，2=深度挖掘） |
| `--max-pages` | 80 | 最大抓取页面数，防止无限递归 |
| `--same-domain-only` | false | 仅抓取同一域名下的内容 |
| `--output-dir` | 自动生成 | 指定输出目录路径 |
| `--skip-images` | false | 跳过图片下载（仅保存文本） |
| `--force-refresh` | false | 强制重新抓取，忽略缓存 |

## 使用场景

### 1. 技术调研
**场景**：研究一个新的技术栈（如React 18新特性）
**输入**：官方文档链接、相关博客、GitHub仓库
**输出**：完整的技术素材包，包含所有相关资源

### 2. 竞品分析
**场景**：分析竞争对手的产品
**输入**：竞品官网、文档、博客、用户评价
**输出**：结构化的竞品分析素材

### 3. 学术研究
**场景**：收集某个研究领域的文献
**输入**：论文链接、相关研究、数据集页面
**输出**：学术研究素材包，方便后续整理

### 4. 市场分析
**场景**：分析某个行业趋势
**输入**：行业报告、新闻文章、统计数据
**输出**：市场分析素材，支持深入研究

## 工作流程示例

### 示例1：React 18技术调研
```
用户：帮我采集React 18相关素材
输入链接：
- https://react.dev/blog/2023/03/16/react-18
- https://github.com/facebook/react/releases/tag/v18.0.0
- https://blog.logrocket.com/whats-new-react-18/

输出：
2026-07-06-React-18/
├── README.md
├── 00-research-brief.md
├── 01-link-inventory.md
├── 02-image-inventory.md
├── 03-reading-map.md
├── MAIN-01-react-official-blog.md
├── MAIN-02-github-release.md
├── MAIN-03-logrocket-blog.md
├── LINKED-01-concurrent-features.md
├── LINKED-02-automatic-batching.md
├── LINKED-03-transition-api.md
└── assets/
    ├── react-18-diagram.png
    ├── feature-comparison.png
    └── migration-guide.png
```

### 示例2：AI投资研究
```
用户：帮我采集AI投资相关素材
输入链接：
- https://a16z.com/ai-investing-trends/
- https://www.bvp.com/atlas/artificial-intelligence/
- https://www.sequoiacap.com/article/ai-everything/

输出：
2026-07-06-AI-Investing/
├── README.md
├── 00-research-brief.md
├── 01-link-inventory.md
├── 02-image-inventory.md
├── 03-reading-map.md
├── MAIN-01-a16z-ai-trends.md
├── MAIN-02-bvp-ai-atlas.md
├── MAIN-03-sequoia-ai-article.md
├── LINKED-01-ai-market-size.md
├── LINKED-02-investment-theses.md
└── assets/
    ├── ai-market-growth.png
    ├── investment-landscape.png
    └── startup-ecosystem.png
```

## 输出文件说明

### 1. README.md
- 素材包概览
- 采集日期和主题
- 包含的主要链接
- 文件结构说明

### 2. 00-research-brief.md
- 研究简报摘要
- 关键发现和洞察
- 建议进一步研究方向

### 3. 01-link-inventory.md
- 所有抓取链接的完整清单
- 链接分类（核心/相关/参考）
- 抓取状态和备注

### 4. 02-image-inventory.md
- 所有图片资源清单
- 图片来源和描述
- 本地存储路径

### 5. 03-reading-map.md
- 内容关联关系图
- 推荐阅读顺序
- 知识图谱可视化

### 6. MAIN-*.md
- 每个入口页面的完整内容
- 保留原始格式和结构
- 包含图片本地引用

### 7. LINKED-*.md
- 相关链接的扩展内容
- 按主题分类组织
- 建立与主内容的关联

### 8. assets/
- 所有本地化的图片资源
- 按来源分类存储
- 支持相对路径引用

## 最佳实践

### 1. 准备工作
- **明确目标**：确定采集的具体主题和范围
- **精选入口链接**：选择权威、全面的初始链接
- **预估规模**：根据主题复杂度选择合适的抓取深度

### 2. 执行采集
- **分阶段采集**：先浅层抓取，再根据需要深度挖掘
- **监控进度**：关注抓取页面数和深度
- **及时调整**：根据初步结果调整参数

### 3. 后续处理
- **内容审查**：检查采集内容的完整性和质量
- **知识编译**：使用LLM对素材进行整理和提炼
- **集成到知识库**：将结构化内容整合到个人知识库

## 注意事项

### 技术限制
1. **反爬虫机制**：部分网站可能有反爬虫措施
2. **JavaScript渲染**：动态加载的内容可能无法抓取
3. **登录限制**：需要登录的内容无法访问
4. **文件大小**：大量图片可能占用较大存储空间

### 使用建议
1. **尊重版权**：仅用于个人学习和研究
2. **控制频率**：避免对同一网站频繁请求
3. **备份重要内容**：定期备份采集的素材
4. **结合其他工具**：与Obsidian、Roam Research等工具配合使用

## 故障排除

### 常见问题
1. **抓取失败**：检查网络连接和目标网站可访问性
2. **图片下载失败**：尝试调整超时设置或跳过图片
3. **内容不完整**：增加抓取深度或手动补充重要链接
4. **内存不足**：减少最大页面数或分批采集

### 调试建议
1. **查看日志**：关注抓取过程中的提示信息
2. **测试单个链接**：先用单个链接测试功能
3. **调整参数**：根据实际情况调整抓取参数
4. **联系支持**：如有技术问题，可联系作者

## 版本历史

### v1.0 (2026-06-06)
- 初始版本发布
- 支持基本网页抓取和图片本地化
- 提供结构化输出格式

### 未来计划
- 支持更多内容类型（视频、PDF等）
- 增强智能内容识别
- 集成更多AI分析功能
- 支持云端同步和协作

---

**标签**：`#web-crawling` `#knowledge-management` `#content-collection` `#ai-agent` `#automation`

**作者**：老章（公众号：Ai学习的老章）
**原文链接**：https://mp.weixin.qq.com/s/U1nICI87xfBZ86Bh_Dj5kw
**收录日期**：2026-07-06