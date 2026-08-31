"""更新 GitHub 仓库的 fetch_tweets.py 以使用新的 Syndication API 端点"""
import requests, json, base64, subprocess, os

def get_github_token():
    try:
        result = subprocess.run(
            ["git", "credential", "fill"],
            input="url=https://github.com\n\n",
            capture_output=True, text=True, encoding="utf-8", timeout=5,
        )
        for line in result.stdout.split("\n"):
            if line.startswith("password="):
                return line.replace("password=", "")
    except Exception:
        pass
    return os.environ.get("GH_TOKEN") or ""

token = get_github_token()
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {token}',
}

# Current fetch_via_syndication function
old_func = '''
def fetch_via_syndication(user):
    try:
        url = "https://cdn.syndication.twimg.com/timeline/profile"
        params = {
            "screen_name": user["username"],
            "count": str(TWEETS_PER_USER),
        }
        log(f"  [syndication] Trying {user['username']}...")
        resp = SESSION.get(url, params=params, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Accept": "application/json",
            "Origin": "https://platform.twitter.com",
        })
        if resp.status_code == 200:
            data = resp.json()
            body = data.get("body", "")
            if body and isinstance(body, str) and "<li class=" in body:
                tweets = _parse_syndication_html(body, user)
            elif isinstance(data, list):
                tweets = _parse_syndication_json(data, user)
            elif "tweets" in data:
                tweets = _parse_syndication_json(data["tweets"], user)
            else:
                log(f"  [syndication] Unexpected response format")
                return []
            if tweets:
                log(f"  [syndication] Got {len(tweets)} tweets")
                return tweets
            else:
                log(f"  [syndication] Got response but no tweets parsed")
        elif resp.status_code == 404:
            log(f"  [syndication] User not found")
        else:
            log(f"  [syndication] HTTP {resp.status_code}")
    except requests.exceptions.Timeout:
        log(f"  [syndication] Timeout")
    except Exception as e:
        log(f"  [syndication] Error: {str(e)[:80]}")
    return []
'''

# New function to replace
new_func = '''
def fetch_via_syndication(user):
    """Use syndication.twitter.com embed endpoint (the one that powers tweet embeds on blogs).
    Returns HTML page with __NEXT_DATA__ script tag containing JSON with user's timeline.
    This endpoint is more durable than the old cdn.syndication.twimg.com one."""
    try:
        url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{user['username']}"
        log(f"  [syndication] Trying {user['username']}...")
        resp = SESSION.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        if resp.status_code == 200:
            import re
            match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                tweets = _parse_syndication_nextdata(data, user)
                if tweets:
                    log(f"  [syndication] Got {len(tweets)} tweets from __NEXT_DATA__")
                    return tweets
            # Fallback: try old HTML parsing
            tweets = _parse_syndication_html(resp.text, user)
            if tweets:
                log(f"  [syndication] Got {len(tweets)} tweets from HTML fallback")
                return tweets
            log(f"  [syndication] No tweets parsed from response")
        elif resp.status_code == 404:
            log(f"  [syndication] User not found (404)")
        else:
            log(f"  [syndication] HTTP {resp.status_code}")
    except requests.exceptions.Timeout:
        log(f"  [syndication] Timeout")
    except Exception as e:
        log(f"  [syndication] Error: {str(e)[:80]}")
    return []


def _parse_syndication_nextdata(data, user):
    """Parse the __NEXT_DATA__ JSON from syndication.twitter.com response.
    The JSON structure contains timeline entries with tweet data."""
    tweets = []
    try:
        # Navigate the __NEXT_DATA__ structure to find timeline entries
        props = data.get("props", {})
        page_props = props.get("pageProps", {})
        timeline = page_props.get("timeline", [])
        if not timeline and "entries" in page_props:
            timeline = page_props.get("entries", [])
        if not timeline and "data" in page_props:
            timeline = page_props.get("data", [])
        # Try alternate path: pageProps -> timeline -> entries
        if not timeline:
            for key in page_props:
                val = page_props[key]
                if isinstance(val, dict) and "entries" in val:
                    timeline = val["entries"]
                    break
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    if "content" in val[0] or "tweet" in val[0] or "text" in val[0]:
                        timeline = val
                        break

        # Process timeline entries
        count = 0
        for entry in timeline:
            if count >= TWEETS_PER_USER:
                break
            # Try different paths to find tweet content
            content = None
            tweet_id = None
            created_at = None

            # Direct fields
            if isinstance(entry, dict):
                content = entry.get("text") or entry.get("full_text") or entry.get("content")
                tweet_id = entry.get("id_str") or entry.get("id") or ""
                if isinstance(content, dict):
                    content = content.get("text", "")

                # Nested in tweet object
                if not content and "tweet" in entry:
                    tweet = entry["tweet"]
                    content = tweet.get("text") or tweet.get("full_text")
                    tweet_id = tweet.get("id_str") or tweet.get("id") or ""
                    created_at = tweet.get("created_at")

                # Nested in content->tweet
                if not content:
                    ec = entry.get("content", {})
                    if isinstance(ec, dict):
                        tweet = ec.get("tweet") or ec
                        content = tweet.get("text") or tweet.get("full_text")
                        tweet_id = tweet.get("id_str") or tweet.get("id") or ""
                        created_at = tweet.get("created_at")

                # Nested under itemContent->tweet_results->result
                if not content:
                    ic = entry.get("itemContent", {})
                    tweet = ic.get("tweet_results", {}).get("result", {})
                    if not tweet:
                        tweet = ic.get("tweet", {})
                    if not tweet:
                        tweet = ic
                    content = tweet.get("text") or tweet.get("full_text") or tweet.get("legacy", {}).get("full_text", "")
                    tweet_id = tweet.get("id_str") or tweet.get("rest_id") or tweet.get("id") or ""
                    legacy = tweet.get("legacy", {})
                    created_at = legacy.get("created_at") or tweet.get("created_at")

                if content and tweet_id:
                    if isinstance(content, str) and len(content) > 5:
                        tweets.append({
                            "id": f"tweet_{user['username']}_{tweet_id}",
                            "username": user["username"],
                            "display_name": user["display_name"],
                            "published_at": created_at or entry.get("created_at", ""),
                            "content": content,
                            "url": f"https://x.com/{user['username']}/status/{tweet_id}",
                            "tweet_id": tweet_id,
                        })
                        count += 1
    except Exception as e:
        log(f"  [syndication:nextdata] Error: {str(e)[:60]}")

    return tweets
'''

# Read current fetch_tweets.py from repo
url = 'https://api.github.com/repos/Eoser-Harvey/twitter-feed-fetcher/contents/fetch_tweets.py'
resp = requests.get(url, timeout=15, headers=headers)
if resp.status_code != 200:
    print(f"Failed to read fetch_tweets.py: {resp.status_code}")
    exit(1)

data = resp.json()
current_content = base64.b64decode(data['content']).decode('utf-8')
sha = data['sha']
print(f"Read fetch_tweets.py ({len(current_content)} bytes, sha: {sha[:10]}...)")

# Check if the old endpoint is still in use
if 'cdn.syndication.twimg.com/timeline/profile' in current_content:
    print("Found old Syndication API endpoint. Need to update.")
else:
    print("Old endpoint not found, may already be updated.")
    # Check if new endpoint exists
    if 'syndication.twitter.com/srv/timeline-profile' in current_content:
        print("New endpoint already present. No update needed.")
        exit(0)

# Update the syndication fetch function
# Replace the old fetch_via_syndication function
old_start = 'def fetch_via_syndication(user):'
old_end = "    return []"

# Find the old function
idx_start = current_content.find(old_start)
if idx_start == -1:
    print("Could not find fetch_via_syndication function")
    exit(1)

# Find the end of the function (next function definition or end of file)
idx_func_end = current_content.find('\n\ndef ', idx_start + 1)
if idx_func_end == -1:
    idx_func_end = len(current_content)

old_func_full = current_content[idx_start:idx_func_end]

# The new code to replace
new_fetch_code = '''def fetch_via_syndication(user):
    """Use syndication.twitter.com embed endpoint (the one that powers tweet embeds on blogs).
    Returns HTML page with __NEXT_DATA__ script tag containing JSON with user's timeline.
    This endpoint is more durable than the old cdn.syndication.twimg.com one."""
    try:
        url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{user['username']}"
        log(f"  [syndication] Trying {user['username']}...")
        resp = SESSION.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        if resp.status_code == 200:
            import re
            match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                tweets = _parse_syndication_nextdata(data, user)
                if tweets:
                    log(f"  [syndication] Got {len(tweets)} tweets from __NEXT_DATA__")
                    return tweets
            # Fallback: try old HTML parsing
            tweets = _parse_syndication_html(resp.text, user)
            if tweets:
                log(f"  [syndication] Got {len(tweets)} tweets from HTML fallback")
                return tweets
            log(f"  [syndication] No tweets parsed from response")
        elif resp.status_code == 404:
            log(f"  [syndication] User not found (404)")
        else:
            log(f"  [syndication] HTTP {resp.status_code}")
    except requests.exceptions.Timeout:
        log(f"  [syndication] Timeout")
    except Exception as e:
        log(f"  [syndication] Error: {str(e)[:80]}")
    return []


def _parse_syndication_nextdata(data, user):
    """Parse the __NEXT_DATA__ JSON from syndication.twitter.com response.
    The JSON structure contains timeline entries with tweet data."""
    tweets = []
    try:
        props = data.get("props", {})
        page_props = props.get("pageProps", {})
        timeline = page_props.get("timeline", [])
        if not timeline and "entries" in page_props:
            timeline = page_props.get("entries", [])
        if not timeline and "data" in page_props:
            timeline = page_props.get("data", [])
        if not timeline:
            for key in page_props:
                val = page_props[key]
                if isinstance(val, dict) and "entries" in val:
                    timeline = val["entries"]
                    break
                if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                    if "content" in val[0] or "tweet" in val[0] or "text" in val[0]:
                        timeline = val
                        break

        count = 0
        for entry in timeline:
            if count >= TWEETS_PER_USER:
                break
            content = None
            tweet_id = None
            created_at = None

            if isinstance(entry, dict):
                content = entry.get("text") or entry.get("full_text") or entry.get("content")
                tweet_id = entry.get("id_str") or entry.get("id") or ""
                if isinstance(content, dict):
                    content = content.get("text", "")

                if not content and "tweet" in entry:
                    tweet = entry["tweet"]
                    content = tweet.get("text") or tweet.get("full_text")
                    tweet_id = tweet.get("id_str") or tweet.get("id") or ""
                    created_at = tweet.get("created_at")

                if not content:
                    ec = entry.get("content", {})
                    if isinstance(ec, dict):
                        tweet = ec.get("tweet") or ec
                        content = tweet.get("text") or tweet.get("full_text")
                        tweet_id = tweet.get("id_str") or tweet.get("id") or ""
                        created_at = tweet.get("created_at")

                if not content:
                    ic = entry.get("itemContent", {})
                    tweet = ic.get("tweet_results", {}).get("result", {})
                    if not tweet:
                        tweet = ic.get("tweet", {})
                    if not tweet:
                        tweet = ic
                    content = tweet.get("text") or tweet.get("full_text") or tweet.get("legacy", {}).get("full_text", "")
                    tweet_id = tweet.get("id_str") or tweet.get("rest_id") or tweet.get("id") or ""
                    legacy = tweet.get("legacy", {})
                    created_at = legacy.get("created_at") or tweet.get("created_at")

                if content and tweet_id:
                    if isinstance(content, str) and len(content) > 5:
                        tweets.append({
                            "id": f"tweet_{user['username']}_{tweet_id}",
                            "username": user["username"],
                            "display_name": user["display_name"],
                            "published_at": created_at or entry.get("created_at", ""),
                            "content": content,
                            "url": f"https://x.com/{user['username']}/status/{tweet_id}",
                            "tweet_id": tweet_id,
                        })
                        count += 1
    except Exception as e:
        log(f"  [syndication:nextdata] Error: {str(e)[:60]}")

    return tweets'''

new_content = current_content.replace(old_func_full, new_fetch_code)

# Remove the old _parse_syndication_json function (no longer needed if not used elsewhere)
# Actually, keep it for backward compatibility

print(f"New content length: {len(new_content)} bytes")
print("Changes made. Ready to commit.")

# Update via GitHub API
update_url = url
update_data = {
    "message": "fix: update Syndication API endpoint to syndication.twitter.com/srv/timeline-profile\n\nThe old cdn.syndication.twimg.com/timeline/profile endpoint has been deprecated.\nNew endpoint returns HTML with __NEXT_DATA__ JSON, matching the embed widget API\nthat powers tweet embeds on millions of blogs. Added _parse_syndication_nextdata().",
    "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
    "sha": sha,
}
resp2 = requests.put(update_url, headers=headers, json=update_data, timeout=15)
print(f"Update response: {resp2.status_code}")
if resp2.status_code == 200:
    print("fetch_tweets.py updated successfully!")
    print("Commit:", resp2.json()['commit']['sha'][:8])
else:
    print(f"Error: {resp2.text[:500]}")