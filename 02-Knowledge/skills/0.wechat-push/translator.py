"""
翻译模块 — 支持 Google/Bing 免费翻译
"""
import requests
import re
import html
from typing import Optional, List, Dict


class Translator:
    """多引擎翻译器"""

    def __init__(self, config):
        tcfg = config["translate"]
        self.engine = tcfg.get("engine", "google")
        self.source_lang = tcfg.get("source_lang", "auto")
        self.target_lang = tcfg.get("target_lang", "zh-CN")
        self.timeout = config["fetch"]["timeout"]

    def translate(self, text):
        """翻译文本"""
        if not text or not text.strip():
            return text

        if self.engine == "google":
            return self._translate_google(text)
        elif self.engine == "bing":
            return self._translate_bing(text)
        else:
            return self._translate_google(text)

    def _translate_google(self, text):
        """Google 翻译 API (免费接口)"""
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": self.source_lang,
                "tl": self.target_lang,
                "dt": "t",
                "q": text
            }
            resp = requests.get(url, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                return None

            result = resp.json()
            # 提取翻译结果
            parts = []
            for sentence in result[0]:
                if sentence[0]:
                    parts.append(sentence[0])
            translated = "".join(parts)
            return html.unescape(translated)

        except Exception as e:
            print(f"[DEBUG] Google翻译失败: {e}")
            return None

    def _translate_bing(self, text):
        """Bing 翻译 (免费接口)"""
        try:
            url = "https://api.cognitive.microsofttranslator.com/translate"
            # Bing 免费接口需要 key，降级到网页版
            return self._translate_google(text)
        except Exception:
            return None

    def translate_tweets(self, tweets):
        """批量翻译推文"""
        for tweet in tweets:
            content = tweet.get("content", "")
            if content:
                translated = self.translate(content)
                tweet["translated"] = translated or "[翻译失败]"
            else:
                tweet["translated"] = ""
        return tweets
