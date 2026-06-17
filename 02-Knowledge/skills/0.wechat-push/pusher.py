"""
微信推送模块 — Server酱 Turbo 版
"""
import requests
from datetime import datetime


class WeChatPusher:
    """Server酱微信推送"""

    def __init__(self, send_key):
        self.send_key = send_key
        self.api_url = f"https://sctapi.ftqq.com/{send_key}.send"
        self.timeout = 15

    def push_tweets(self, tweets):
        """推送推文汇总到微信"""
        if not tweets:
            return self._push_simple("📭 X推文推送", "本次没有获取到新推文。")

        # 构建 Markdown 格式消息
        title = f"📡 X推文速递 ({len(tweets)}条)"
        body = self._build_markdown(tweets)

        return self._push_markdown(title, body)

    def _build_markdown(self, tweets):
        """构建推文汇总 Markdown"""
        lines = []
        lines.append(f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**关注用户**: 马斯克 | CZ | 特朗普")
        lines.append("")
        lines.append("---")
        lines.append("")

        for i, tweet in enumerate(tweets, 1):
            display = tweet.get("display_name", tweet.get("username", ""))
            username = tweet.get("username", "")
            content = tweet.get("content", "")
            translated = tweet.get("translated", "")
            url = tweet.get("url", "")
            analysis = tweet.get("analysis", {})
            published = tweet.get("published_at", "")

            # 格式化时间
            time_str = ""
            if published:
                try:
                    dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    time_str = dt.strftime("%m-%d %H:%M")
                except (ValueError, TypeError):
                    pass

            # 推文卡片
            lines.append(f"### {i}. {display} (@{username})")
            if time_str:
                lines.append(f"`{time_str}`")
            lines.append("")

            # 原文
            lines.append(f"> {content}")
            lines.append("")

            # 翻译
            if translated:
                lines.append(f"🔤 **翻译**: {translated}")
                lines.append("")

            # 链接
            if url:
                lines.append(f"🔗 [查看原文]({url})")
                lines.append("")

            # 分析建议
            if analysis:
                lines.append("---")
                lines.append("#### 📊 AI分析建议")
                lines.append("")

                if analysis.get("investment"):
                    lines.append(analysis["investment"])
                    lines.append("")

                if analysis.get("career"):
                    lines.append(analysis["career"])
                    lines.append("")

                if analysis.get("life"):
                    lines.append(analysis["life"])
                    lines.append("")

                if analysis.get("family"):
                    lines.append(analysis["family"])
                    lines.append("")

            lines.append("---")
            lines.append("")

        # 页脚
        lines.append("---")
        lines.append(f"🤖 自动推送 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("关注: 马斯克 · CZ · 特朗普")

        return "\n".join(lines)

    def _push_markdown(self, title, body):
        """推送 Markdown 格式消息"""
        try:
            # 截断过长内容（Server酱限制）
            max_len = 30000
            if len(body) > max_len:
                body = body[:max_len - 100] + "\n\n... (内容过长已截断)"

            data = {
                "title": title,
                "desp": body,
            }
            resp = requests.post(self.api_url, data=data, timeout=self.timeout)

            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 0:
                    print(f"[OK] 微信推送成功: {title}")
                    return True
                else:
                    print(f"[ERROR] Server酱返回错误: {result}")
                    return False
            else:
                print(f"[ERROR] Server酱请求失败: {resp.status_code}")
                return False

        except Exception as e:
            print(f"[ERROR] 推送异常: {e}")
            return False

    def _push_simple(self, title, content):
        """推送简单文本消息"""
        try:
            data = {
                "title": title,
                "desp": content,
            }
            resp = requests.post(self.api_url, data=data, timeout=self.timeout)
            return resp.status_code == 200
        except Exception as e:
            print(f"[ERROR] 推送异常: {e}")
            return False


def push_to_wechat(tweets, send_key):
    """推送推文到微信（Server酱方案）"""
    pusher = WeChatPusher(send_key)
    return pusher.push_tweets(tweets)


def build_wechat_text(tweets):
    """构建微信纯文本推送消息（用于WeChat MCP等直接推送方案）"""
    lines = []
    lines.append("📡 X推文速递 ({})".format(len(tweets)))
    lines.append("更新时间: {}".format(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')))
    lines.append("关注: 马斯克 | CZ | 特朗普")
    lines.append("=" * 30)

    for i, tweet in enumerate(tweets, 1):
        display = tweet.get("display_name", tweet.get("username", ""))
        username = tweet.get("username", "")
        content = tweet.get("content", "")
        translated = tweet.get("translated", "")
        published = tweet.get("published_at", "")
        analysis = tweet.get("analysis", {})

        lines.append("")
        lines.append("--- {}. {} (@{}) ---".format(i, display, username))
        if published:
            lines.append("时间: {}".format(published))
        lines.append("原文: {}".format(content[:300]))
        if translated:
            lines.append("翻译: {}".format(translated[:300]))
        
        if analysis:
            lines.append("")
            lines.append("📊 AI分析:")
            if analysis.get("investment"):
                lines.append(analysis["investment"])
            if analysis.get("career"):
                lines.append(analysis["career"])
            if analysis.get("life"):
                lines.append(analysis["life"])
            if analysis.get("family"):
                lines.append(analysis["family"])

    lines.append("")
    lines.append("=" * 30)
    lines.append("🤖 自动推送 | {}".format(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    return "\n".join(lines)
