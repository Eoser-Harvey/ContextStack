@echo off
chcp 65001 >nul
python "E:\ProjectGroup\AI\ContextStack\01-Projects\automated-task\0.trae-feishu-push-hour\sync_profile_archive.py" >> "E:\ProjectGroup\AI\ContextStack\01-Projects\automated-task\0.trae-feishu-push-hour\archive_sync_schtask.log" 2>&1