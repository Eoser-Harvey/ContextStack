"""
个人画像加载模块 — 从 profile_archive 自动加载最新档案
重用小时推送项目的 profile_loader 实现，避免代码重复
"""
import os
import sys
import importlib.util


def _import_hour_profile_loader():
    """用 importlib 加载小时项目的 profile_loader，避免自身循环导入"""
    hour_dir = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "0.trae-feishu-push-hour"))
    module_path = os.path.join(hour_dir, "profile_loader.py")

    if not os.path.isfile(module_path):
        raise ImportError(f"profile_loader.py not found: {module_path}")

    spec = importlib.util.spec_from_file_location("hour_profile_loader", module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["hour_profile_loader"] = mod
    spec.loader.exec_module(mod)
    return mod


_hour_mod = _import_hour_profile_loader()

load_latest_profile = _hour_mod.load_latest_profile
load_latest_profile_or_exit = _hour_mod.load_latest_profile_or_exit


if __name__ == "__main__":
    profile = load_latest_profile()
    if profile:
        import json
        print(json.dumps(profile, ensure_ascii=False, indent=2))
    else:
        print("[ERROR] 加载失败")