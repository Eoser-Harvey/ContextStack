"""
X推文推送 — Automation 执行脚本
当本地网络受限时，推文数据从 fetcher_web.py 获取
完整流程: 加载数据 → 翻译 → 分析 → 推送到飞书群
"""
import json
import os
import sys
import yaml
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from translator import Translator
# from analyzer import analyze_tweets  # 已屏蔽
from fetcher_web import build_tweets_from_fetch
from push_lark import push_to_lark
# from profile_loader import load_latest_profile_or_exit  # 已屏蔽


def load_history(history_path):
    """加载已推送的推文ID"""
    if not os.path.exists(history_path):
        return []
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (ValueError, FileNotFoundError):
        return []


def save_history(history_path, tweet_ids, max_history):
    """保存已推送的推文ID"""
    os.makedirs(os.path.dirname(history_path) if os.path.dirname(history_path) else ".", exist_ok=True)
    tweet_ids = tweet_ids[-max_history:]
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(tweet_ids, f, ensure_ascii=False, indent=2)


def maybe_cleanup_history(history_path, current_batch_ids):
    """推送成功后执行：每周清理历史缓存，仅保留本周最新批次"""
    marker_path = os.path.join(os.path.dirname(history_path) or ".", ".last_cleanup_week")
    now = datetime.now()
    current_week_key = f"{now.isocalendar()[0]}-W{now.isocalendar()[1]:02d}"

    if os.path.exists(marker_path):
        with open(marker_path, "r", encoding="utf-8") as f:
            if f.read().strip() == current_week_key:
                return  # 本周已清理过

    # 重置历史：仅保留本周批次
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(current_batch_ids, f, ensure_ascii=False, indent=2)

    with open(marker_path, "w", encoding="utf-8") as f:
        f.write(current_week_key)
    print(f"[CLEANUP] 🗑️ 本周({current_week_key})推送完成，历史缓存已重置（仅保留本周{len(current_batch_ids)}条）")


def filter_new_tweets(tweets, history_ids):
    """过滤出未推送过的新推文（同时去重批次内重复）"""
    new_tweets = []
    seen_in_batch = set()
    for tweet in tweets:
        tid = tweet.get("id", "")
        if not tid:
            continue
        if tid in history_ids:
            print(f"[DEDUP] 跳过历史推文: {tid[:50]}...")
            continue
        if tid in seen_in_batch:
            print(f"[DEDUP] 跳过批次内重复: {tid[:50]}...")
            continue
        new_tweets.append(tweet)
        seen_in_batch.add(tid)
    return new_tweets


def main():
    print("=" * 60)
    print("X推文推送系统启动 — {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    print("推送目标: 飞书群 (CodeBuddy推文推送①)")
    print("=" * 60)

    # 1. 加载配置
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    output_cfg = config["output"]
    history_path = os.path.join(os.path.dirname(__file__), output_cfg["history_file"])

    # 2. 加载历史
    history_ids = load_history(history_path)
    print("[INFO] 历史记录: {} 条已推送推文".format(len(history_ids)))

    # 3. 获取推文数据
    print("[INFO] 加载推文数据...")
    all_tweets = build_tweets_from_fetch()
    print("[INFO] 共获取 {} 条推文".format(len(all_tweets)))

    if not all_tweets:
        print("[INFO] 未获取到推文，退出")
        return

    # 4. 过滤新推文
    new_tweets = filter_new_tweets(all_tweets, history_ids)
    print("[INFO] 新推文: {} 条".format(len(new_tweets)))

    if not new_tweets:
        print("[INFO] 没有新推文，无需推送")
        return

    # 5. 翻译
    print("[INFO] 开始翻译...")
    translator = Translator(config)
    new_tweets = translator.translate_tweets(new_tweets)

    # 6. AI分析 (已屏蔽 — 不加载个人画像，不生成个性化评论)
    # profile = load_latest_profile_or_exit()
    # new_tweets = analyze_tweets(new_tweets, profile)
    # 为每条推文添加空分析字段，兼容后续推送流程
    for t in new_tweets:
        t["analysis"] = {}

    # 7. 保存结果到本地文件
    result_path = os.path.join(os.path.dirname(__file__), "latest_tweets.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(new_tweets, f, ensure_ascii=False, indent=2)
    print("[OK] 分析结果已保存到 latest_tweets.json")

    # 8. 推送到飞书群
    print("[INFO] 推送到飞书群...")
    success = push_to_lark(new_tweets)

    if success:
        new_ids = [t.get("id", "") for t in new_tweets if t.get("id")]
        all_ids = history_ids + new_ids
        save_history(history_path, all_ids, output_cfg["max_history"])
        maybe_cleanup_history(history_path, all_ids)  # 推送成功后清理历史缓存
        print("[OK] 完成! 推送 {} 条新推文到飞书群".format(len(new_tweets)))
    else:
        print("[ERROR] 推送失败，历史未更新，下次将重试")

    # 9. 打印摘要
    print("")
    print("=" * 60)
    print("推文摘要:")
    print("=" * 60)
    for i, t in enumerate(new_tweets, 1):
        print("")
        print("--- {}. {} (@{}) ---".format(i, t.get('display_name'), t.get('username')))
        print("时间: {}".format(t.get('published_at')))
        print("原文: {}".format(t.get('content', '')[:150]))
        if t.get('translated'):
            print("翻译: {}".format(t.get('translated', '')[:150]))
        analysis = t.get('analysis', {})
        if analysis.get('investment'):
            print("投资: {}".format(analysis['investment'].replace('\n', ' ')[:200]))

    print("")
    print("=" * 60)


if __name__ == "__main__":
    main()