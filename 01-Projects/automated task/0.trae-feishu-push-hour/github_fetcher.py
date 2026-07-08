"""
GitHub Actions 推文数据拉取模块
从 Eoser-Harvey/twitter-feed-fetcher 仓库拉取 GitHub Actions 抓取的推文数据，
转换为 fetched_tweets.json 格式，供 run_auto.py 使用。

原理：
  国内网络无法访问 X.com，但 GitHub Actions 运行在海外节点。
  每隔 2 小时，GitHub Actions 自动抓取推文并提交到仓库。
  本地脚本通过 GitHub API 读取最新推文数据。
"""
import json
import os
import requests

GITHUB_REPO = "Eoser-Harvey/twitter-feed-fetcher"
TWEETS_FILE = "tweets.json"
RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{TWEETS_FILE}"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{TWEETS_FILE}"

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "fetched_tweets.json")


def fetch_from_github_raw():
    """通过 raw.githubusercontent.com 直接获取（最简单但可能被墙）"""
    try:
        resp = requests.get(RAW_URL, timeout=15, headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/vnd.github.raw",
        })
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        pass
    return None


def fetch_from_github_api():
    """通过 GitHub API 获取（需要 token，但更可靠）"""
    token = _get_github_token()
    if not token:
        return None

    try:
        resp = requests.get(API_URL, timeout=15, headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        })
        if resp.status_code == 200:
            data = resp.json()
            import base64
            content = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(content)
    except Exception as e:
        pass
    return None


def _get_github_token():
    """从 git credential helper 获取 GitHub token"""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "credential", "fill"],
            input="url=https://github.com\n\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=5,
        )
        for line in result.stdout.split("\n"):
            if line.startswith("password="):
                return line.replace("password=", "")
    except Exception:
        pass
    return None


def convert_to_fetched_format(github_data):
    """
    将 GitHub Actions 抓取的推文转换为 fetched_tweets.json 格式
    
    输入格式 (tweets.json):
    {
        "fetched_at": "2026-06-21T01:53:44Z",
        "total": 12,
        "tweets": [
            {
                "id": "tweet_elonmusk_2068499534431264988",
                "username": "elonmusk",
                "display_name": "马斯克",
                "published_at": "Sun, 21 Jun 2026 01:01:34 GMT",
                "content": "Yes",
                "url": "https://x.com/elonmusk/status/2068499534431264988#m",
                "tweet_id": "2068499534431264988"
            }
        ]
    }
    """
    tweets = github_data.get("tweets", [])
    result = []

    for t in tweets:
        # Clean URL and tweet_id (remove #m suffix from Nitter RSS)
        url = t.get("url", "")
        if "#m" in url:
            url = url.split("#m")[0]

        tweet_id = t.get("id", f"tweet_{t['username']}_{t.get('tweet_id', 'unknown')}")
        if "#m" in tweet_id:
            tweet_id = tweet_id.replace("#m", "")

        result.append({
            "id": tweet_id,
            "username": t.get("username", ""),
            "display_name": t.get("display_name", ""),
            "published_at": t.get("published_at", ""),
            "content": t.get("content", ""),
            "url": url,
            "translated": t.get("translated", ""),  # GitHub Actions 预翻译
            "source_note": f"GitHub Actions: {github_data.get('fetched_at', 'unknown')}",
        })

    return result


def pull_tweets_from_github():
    """
    从 GitHub 仓库拉取最新推文数据
    
    返回推文列表（fetched_tweets.json 格式），失败返回空列表
    """
    github_data = fetch_from_github_raw()
    if not github_data:
        github_data = fetch_from_github_api()

    if not github_data:
        return []

    tweets = github_data.get("tweets", [])
    if not tweets:
        return []

    fetched_at = github_data.get("fetched_at", "unknown")
    print(f"[GitHub] 拉取到 {len(tweets)} 条推文 (抓取时间: {fetched_at})")

    result = convert_to_fetched_format(github_data)

    # 保存到 fetched_tweets.json
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[GitHub] 已保存到 {OUTPUT_FILE}")
    except Exception as e:
        print(f"[GitHub] 保存失败: {e}")

    return result


if __name__ == "__main__":
    tweets = pull_tweets_from_github()
    if tweets:
        print(f"\n成功拉取 {len(tweets)} 条推文:")
        for t in tweets:
            print(f"  [{t['display_name']}] {t['content'][:60]}...")
    else:
        print("\n拉取失败，请检查网络连接或 GitHub 仓库状态")