import json, urllib.request

token = "6b280503d6df417f87556a366bc4ba61"
data = json.dumps({
    "token": token,
    "title": "测试推送",
    "content": "这是一条年费提醒系统的测试消息，如果你收到这条推送，说明微信通知配置成功！",
    "template": "txt",
}).encode()

req = urllib.request.Request(
    "http://www.pushplus.plus/send",
    data=data,
    headers={"Content-Type": "application/json"}
)
resp = urllib.request.urlopen(req)
result = json.loads(resp.read().decode())
print(f"返回码: {result.get('code')}")
print(f"消息: {result.get('msg')}")
if result.get("code") == 200:
    print("✅ 推送成功！请检查微信是否收到 PushPlus 公众号的消息")
else:
    print("❌ 推送失败，请检查 token 是否正确")
print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")