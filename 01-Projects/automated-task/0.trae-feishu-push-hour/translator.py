"""
翻译模块 — 优先从 translation_cache.json 读取AI预翻译，在线翻译作为备选
"""
import json
import os
import requests
import re
import html
from typing import Optional, List, Dict


class Translator:
    """多引擎翻译器，支持本地缓存优先"""

    def __init__(self, config):
        tcfg = config["translate"]
        self.engine = tcfg.get("engine", "google")
        self.source_lang = tcfg.get("source_lang", "auto")
        self.target_lang = tcfg.get("target_lang", "zh-CN")
        self.timeout = config["fetch"]["timeout"]

        # 加载翻译缓存
        self.cache_dir = os.path.dirname(os.path.abspath(__file__))
        self.cache_path = os.path.join(self.cache_dir, "translation_cache.json")
        self.cache = self._load_cache()

    def _load_cache(self):
        """加载翻译缓存"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (ValueError, FileNotFoundError):
                pass
        return {}

    def _save_cache(self):
        """保存翻译缓存"""
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[DEBUG] 保存翻译缓存失败: {e}")

    def translate(self, text, tweet_id=None):
        """翻译文本，优先使用缓存"""
        if not text or not text.strip():
            return text

        # 优先从缓存读取
        if tweet_id and tweet_id in self.cache:
            cached = self.cache[tweet_id]
            if cached and cached.strip():
                return cached

        # 在线翻译作为备选
        if self.engine == "google":
            result = self._translate_google(text)
        elif self.engine == "bing":
            result = self._translate_bing(text)
        else:
            result = self._translate_google(text)

        # 如果在线翻译成功，写入缓存
        if result and tweet_id:
            self.cache[tweet_id] = result
            self._save_cache()

        return result

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
            return self._translate_google(text)
        except Exception:
            return None

    @staticmethod
    def _is_chinese(text):
        """检测文本是否主要是中文（跳过翻译）"""
        if not text:
            return False
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]', text))
        total_chars = len(text.strip())
        if total_chars == 0:
            return False
        return chinese_chars / total_chars >= 0.3

    def translate_tweets(self, tweets):
        """批量翻译推文，优先使用缓存"""
        cache_hits = 0
        pre_translated = 0
        skipped_chinese = 0
        for tweet in tweets:
            content = tweet.get("content", "")
            tweet_id = tweet.get("id", "")

            # 检测中文原文 → 跳过翻译
            if self._is_chinese(content):
                skipped_chinese += 1
                tweet["translated"] = content  # 直接用原文作为"翻译"
                continue

            # 优先使用 GitHub Actions 预翻译数据
            if tweet.get("translated") and tweet["translated"].strip() and tweet["translated"] != "[翻译失败]":
                pre_translated += 1
                continue

            if content:
                translated = self.translate(content, tweet_id)
                if tweet_id and tweet_id in self.cache:
                    cache_hits += 1
                tweet["translated"] = translated or "[翻译失败]"
            else:
                tweet["translated"] = ""
        print(f"[INFO] 翻译完成: GitHub预翻译 {pre_translated} 条, 中文原文跳过 {skipped_chinese} 条, 缓存命中 {cache_hits}/{len(tweets)} 条")
        return tweets
