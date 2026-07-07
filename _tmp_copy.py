import os, glob, shutil

SRC = r"D:\wechatDownload\下载\老薛的晨间日记"
DST = os.path.join(SRC, "老薛财富成长精选")
os.makedirs(DST, exist_ok=True)

# 精选：跨越 0-100万 / 100-1000万 路径、守富、决策、人脉、战略级的常读常新文
keys = [
    "因为他们三个我赚到了第一个100万",
    "老薛个人财富成长的一把密钥",
    "4年5000万老薛的财富愿景",
    "低谷奋斗冲顶指引老薛这三个阶段的明灯",
    "老薛的成长史从负债近百万",
    "八月总结老薛财富之旅的三把密钥",
    "六月总结财富容积",
    "知道了赚钱的办法真的可以赚到钱么",
    "二月总结获得财富的几个关键点",
    "四月总结稳住别飘",
    "五月总结盈利10倍的复盘",
    "老薛的2021总结",
    "老薛的2022总结巅峰与谷底",
    "老薛的23年上半年总结",
    "老薛的2024什么更重要",
    "如何咬住机会结贵人",
    "选对城市职业与同伴",
    "10年10倍的思考",
    "让自己闲下来才是最难的战略",
    "近期关于投资的思考与规划",
    "过去5年最舒服的赚钱模型",
    "风险盲区",
    "魅力",
    "三亚财富之旅的收获",
    "三月总结发现机会抓住机会变现机会",
]

pdfs = glob.glob(os.path.join(SRC, "*.pdf"))
copied = []
for p in pdfs:
    name = os.path.basename(p)
    if any(k in name for k in keys):
        shutil.copy2(p, os.path.join(DST, name))
        copied.append(name)

print(f"源PDF: {len(pdfs)}  精选拷贝: {len(copied)}")
for c in sorted(copied):
    print(" +", c)
