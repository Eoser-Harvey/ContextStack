import subprocess, os
os.chdir(r'e:\ProjectGroup\AI\ContextStack')

def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    print('$', cmd)
    if r.stdout: print(r.stdout.strip())
    if r.stderr: print('ERR:', r.stderr.strip())
    return r.returncode

run('git add -A')
run('git commit -m "credit-card: 信用卡0账单方案按农行25日刷4.7万重写，档位D1=4张/D2=13张，主控表同步"')
print('=== push ===')
run('git push origin master')
