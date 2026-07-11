# 个人网站 · 部署全流程方案

> 最后更新：2026-07-11

---

## 一、总体架构

```
你的域名 (如 hanwei.dev)
      │
      ▼
Cloudflare DNS (免费CDN + DDoS防护 + HTTPS)
      │
      ▼
Cloudflare Pages (免费托管，无限带宽)
      │
      ▼
GitHub 仓库 (源码管理 + 自动部署)
```

**为什么选这个方案？**
- 总成本：**$0/年**（域名除外，约$10/年）
- 免备案：域名在Cloudflare注册 + 托管在Cloudflare Pages = 无需ICP备案
- 全球CDN加速，国内访问速度尚可
- 自动化CI/CD：改代码 → git push → 自动部署

---

## 二、域名注册方案对比

<details>
<summary><b>点击展开：10家注册商完整对比数据（2026年5月）</b></summary>

| 注册商 | .com首年 | .com续费 | WHOIS隐私 | 5年总成本 | 推荐度 |
|--------|---------|---------|----------|----------|--------|
| **Cloudflare** | $10.44 | $10.44 | ✅ 免费 | **$52.20** | ⭐⭐⭐⭐⭐ |
| **Dynadot** | $10.86 | $10.86 | ✅ 免费 | $54.30 | ⭐⭐⭐⭐ |
| **Porkbun** | $11.06 | $11.06 | ✅ 免费 | $55.30 | ⭐⭐⭐⭐ |
| **NameSilo** | $11.05 | $11.05 | ✅ 免费 | $55.25 | ⭐⭐⭐⭐ |
| **Spaceship** | $9.98 | $12.18 | ✅ 免费 | $58.70 | ⭐⭐⭐ |
| **Namecheap** | $9.98 | $16.98 | ✅ 免费 | $77.90 | ⭐⭐⭐ |
| **GoDaddy** | $0.01 | $21.99 | ❌ $9.99/年 | $137.92 | ⭐ |

</details>

### 🥇 推荐方案：Cloudflare Registrar

**为什么是Cloudflare？**
1. **成本价注册** — $10.44/年（.com），无加价，首年=续费
2. **WHOIS隐私免费** — 不用额外付费隐藏个人信息
3. **与Pages/CND无缝集成** — 一个平台搞定域名+DNS+托管
4. **安全性顶级** — 全球最大CDN厂商，DDoS防护免费用
5. **续费不涨价** — 不像GoDaddy/Namecheap首年9.98续费16.98

**缺点：**
- 必须使用Cloudflare DNS（不能自定义NS记录）
- 界面偏技术向，新手学习曲线稍高
- 不支持支付宝（需Visa/MasterCard）

### 🥈 备选：Porkbun

**优势：**
- 界面友好，比Cloudflare更易上手
- 免费SSL证书 + 邮件转发
- 支持支付宝（适合没有外币卡的用户）
- 500+后缀可选

**缺点：**
- $11.06/年，比Cloudflare略贵$0.62
- 需额外配置DNS指向Cloudflare Pages

### 🥉 国内备选：NameSilo

**优势：**
- 支持支付宝/微信支付
- 批量操作API好
- WHOIS隐私免费

**缺点：**
- 管理界面英文，新手不友好
- 同Porkbun一样需额外配DNS

### ❌ 不推荐：GoDaddy

理由：首年$0.01陷阱 → 续费$21.99/年 + 隐私费$9.99/年 = 5年$138，是Cloudflare的2.6倍。且追加销售骚扰多。

### 💡 推荐域名后缀建议

| 后缀 | 首年价格 | 适用场景 | 推荐度 |
|------|---------|---------|--------|
| `.com` | ~$10 | 最通用、最权威（建议首选） | ⭐⭐⭐⭐⭐ |
| `.dev` | ~$12 | 开发者个人品牌 | ⭐⭐⭐⭐ |
| `.me` | ~$15 | 个人品牌，简短 | ⭐⭐⭐ |
| `.cn` | ~¥38 | 国内访问+需备案 | ⭐⭐ |

**建议**：`hanwei.dev` 或 `harvey-dev.com`，简洁、专业、好记。

---

## 三、静态网站托管方案对比

| 维度 | **Cloudflare Pages** | **GitHub Pages** | **Vercel** | **Netlify** |
|------|---------------------|------------------|------------|-------------|
| **免费带宽** | **不限量** 🥇 | 100GB/月 | 100GB/月 | 100GB/月 |
| **构建次数** | 500次/月 | GitHub Actions免费 | 6000分钟/月 | 300分钟/月 |
| **自定义域名** | ✅ | ✅ | ✅ | ✅ |
| **自动HTTPS** | ✅ | ✅ | ✅ | ✅ |
| **国内访问** | **较快**（有中国节点）🥇 | 较慢（部分被墙） | 一般 | 一般 |
| **表单功能** | 需Workers | ❌ | ❌ | ✅ |
| **并发构建** | 1 | N/A | 1 | 1 |
| **免费SSL** | ✅ | ✅ | ✅ | ✅ |
| **商业使用** | ✅ 允许 | ✅ 允许 | ❌ Hobby禁止 | 有限制 |

### 🥇 推荐：Cloudflare Pages

**最适合你的理由：**
1. **无限带宽** — 即使网站火了也不怕超限
2. **国内访问快** — Cloudflare有中国边缘节点，比其他平台更适合中文读者
3. **与域名托管同一平台** — Cloudflare买域名 → 一键指向Cloudflare Pages
4. **500次构建/月** — 个人网站完全够用
5. **自动Git部署** — GitHub仓库push → 自动构建部署

### 🥈 备选：GitHub Pages

**优势**：完全免费无限制、与GitHub无缝集成
**劣势**：国内访问慢（可能被干扰）、带宽限制100GB

---

## 四、完整部署步骤（Cloudflare方案）

### Step 1：注册域名（10分钟）

1. 访问 https://dash.cloudflare.com/sign-up
2. 注册账号（用Gmail或Outlook邮箱）
3. Domain Registration → Register Domains
4. 搜索你想要的域名（建议 `.dev` 或 `.com`）
5. 添加到购物车 → 支付（$10-12/年）
6. **自动配置**：Cloudflare会自动帮你设置DNS、开启CDN、配置HTTPS

### Step 2：代码推送GitHub（5分钟）

```bash
cd "e:\ProjectGroup\AI\ContextStack\01-Projects\personal-website"
git init
git add .
git commit -m "Initial commit: personal website"
git remote add origin https://github.com/YOUR_USERNAME/personal-website.git
git push -u origin main
```

### Step 3：部署到Cloudflare Pages（5分钟）

1. 访问 https://dash.cloudflare.com/
2. 左侧导航 → **Workers & Pages** → **Create application** → **Pages**
3. 连接GitHub → 选择 `personal-website` 仓库
4. 构建设置：
   - **Production branch**: `main`
   - **Build command**: 留空（纯静态HTML）
   - **Build output directory**: `/`（根目录）
5. 点击 **Save and Deploy**

1-3分钟后，网站部署完成，获得 `xxx.pages.dev` 子域名。

### Step 4：绑定自定义域名（5分钟）

1. Cloudflare Pages → 你的项目 → **Custom domains**
2. 输入你的域名 → **Continue**
3. Cloudflare自动配置DNS并签发SSL证书
4. 等待1-5分钟生效

### Step 5：验证（2分钟）

- 访问你的域名，检查HTTPS是否正常
- 用手机/同事电脑测试访问
- 检查各平台社交分享预览（Open Graph生效）

---

## 五、国内访问优化（进阶）

### 5.1 备案方案（推荐长期使用）

如果未来国内读者多了，可以：
1. 阿里云/腾讯云购买国内服务器
2. 提交ICP备案（个人网站，约15-20工作日）
3. 域名解析到国内IP
4. **注意**：备案后域名必须解析到备案服务商的服务器

### 5.2 免备案方案（推荐当前使用）

使用 Cloudflare + 国外域名，无需备案即可访问。
- ✅ 合规（服务器在境外，不触发备案要求）
- ✅ 免去15-20天的备案等待
- ⚠️ 部分网络环境下访问较慢
- ⚠️ 微信内置浏览器可能拦截部分国外域名

---

## 六、成本总览

| 项目 | 方案 | 年成本 |
|------|------|--------|
| 域名 | Cloudflare (.com/.dev) | **~$10** (约¥72) |
| 托管 | Cloudflare Pages | **$0** |
| CDN | Cloudflare | **$0** |
| HTTPS | Cloudflare | **$0** |
| DNS | Cloudflare | **$0** |
| **总计** | | **~$10/年 (约¥72/年)** |

**不到一杯咖啡的月均成本。**

---

## 七、安全与维护

### 自动化检查清单

- [ ] 每年域名续费提醒（Cloudflare自动续费）
- [ ] 每季度检查Cloudflare Pages部署状态
- [ ] 发布新文章后运行 `test_website.py` 验证
- [ ] 每半年更新个人简介和链接
- [ ] 监控网站访问量（Cloudflare Analytics免费）

### Git提交规范

```bash
# 每次修改后
git add .
git commit -m "feat: add new article about xxx"
git push

# Cloudflare Pages会在5分钟内自动重新部署
```

### 回滚方案

Cloudflare Pages保留最近10次部署版本：
1. Pages → Deployments → 选择历史版本 → Rollback
2. 30秒内回滚到之前版本

---

## 七、文章发布流程（无需手动重新部署）

### 核心机制：Git自动部署

```
你运行 publish.bat
      │
      ▼
add_article.py 生成文章页面 + 更新首页文章列表
      │
      ▼
git add + commit + push → GitHub仓库
      │
      ▼
Cloudflare Pages 检测到push → 自动构建部署（1-3分钟）
      │
      ▼
读者刷新你的域名 → 看到新文章 ✅
```

**你不需要手动重新部署**。Cloudflare Pages在检测到GitHub仓库有新push后，会自动重新构建和部署。整个过程1-3分钟，全自动。

### 一键发布

```bash
# 方法1：双击bat文件（Windows）
publish.bat "D:\Downloads\微信公众号文章.html" "article-slug"

# 方法2：命令行
python add_article.py "文章.html" "article-slug"
git add -A
git commit -m "publish: article-slug"
git push
```

**slug命名规范**：英文+连字符，如 `investment-review-2026-07`、`embedded-ai-week1`

### 发布后验证

1. 等1-3分钟（Cloudflare Pages自动部署）
2. 访问你的域名，检查"最新文章"区块是否出现新文章
3. 点击文章链接，检查页面显示是否正常
4. 用手机测试移动端显示

### 文章来源

从微信公众号同步：
1. 在浏览器打开微信公众号文章
2. 右键→另存为→网页(HTML)
3. 运行 `publish.bat "保存的文件.html" "article-slug"`

从Markdown同步：
1. 用Markdown写文章
2. 运行 `publish.bat article.md "article-slug"`

### 注意事项

- 文章中的图片如果是微信公众号的图片链接，可能会失效（微信公众号有防盗链）
- 建议把重要图片下载到 `articles/images/` 目录，手动替换链接
- 文章slug一旦发布不要改（会影响SEO和已分享的链接）

---

## 八、常见问题

**Q：Cloudflare Pages能放中文网站吗？**
A：完全可以。Cloudflare是全球服务，支持所有语言，无内容限制。

**Q：网站被微信浏览器打开会拦截吗？**
A：不会被拦截。但如果是新域名或国外域名，微信可能提示"非微信官方网页"，需要手动点"继续访问"。信誉积累后会消失。

**Q：能放Google Analytics等跟踪代码吗？**
A：可以。Cloudflare Pages是纯静态托管，可以添加任何你需要的<script>标签。

**Q：如果网站访问量大了会收费吗？**
A：Cloudflare Pages免费计划**不限带宽/请求数**，不会因流量大而收费。只有企业级功能才收费。

**Q：阿里云/腾讯云注册的域名能用Cloudflare Pages吗？**
A：可以。只需把域名DNS服务器改为Cloudflare的（免费），之后就和在Cloudflare注册的使用体验完全一样。

---

> 📌 以上价格数据采集于2026年5-7月，具体可能随时间调整。以各平台官网最新价格为准。
