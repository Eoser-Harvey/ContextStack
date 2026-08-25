import subprocess, os
os.chdir(r'e:\ProjectGroup\AI\ContextStack')

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('$', cmd)
    if r.stdout: print(r.stdout.strip())
    if r.stderr: print('ERR:', r.stderr.strip())
    return r.returncode

run('git add -A')
run('git commit -m "session: 天机学习方法 2026-08-25，同步inbox/sessions/MEMORY索引"')
run('git push origin master')
# 自删
if os.path.exists(__file__):
    os.remove(__file__)
    print('self-removed')
