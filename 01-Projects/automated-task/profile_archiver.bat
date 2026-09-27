@echo off
chcp 65001 >nul
:: 每日 0 点个人画像归档 — 统一入口
:: 调用 profile_archiver.py 生成两份归档到 hour/day 的 profile_archive/
:: 静默执行，日志写入 profile_archiver.log
"%~dp0profile_archiver.py"