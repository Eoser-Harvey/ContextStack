import subprocess, os
os.chdir(r'e:\ProjectGroup\AI\ContextStack')

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('$', cmd)
    if r.stdout: print(r.stdout.strip())
    if r.stderr: print('ERR:', r.stderr.strip())
    return r.returncode

# 删除临时脚本并提交移除
if os.path.exists('_tmp_push.py'):
    os.remove('_tmp_push.py')
    print('removed _tmp_push.py')
run('git add -A')
run('git commit -m "chore: 移除临时推送脚本 _tmp_push.py"')
run('git push origin master')
