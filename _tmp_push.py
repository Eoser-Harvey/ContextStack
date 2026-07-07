import subprocess, os
os.chdir(r'e:\ProjectGroup\AI\ContextStack')
env = dict(os.environ)
env['GIT_TERMINAL_PROMPT'] = '0'
subprocess.run(['git', 'add', '-A'], check=True, env=env)
out = subprocess.run(['git', 'status', '--porcelain', '-uall'],
                     capture_output=True, text=True, encoding='utf-8').stdout
lines = [l for l in out.splitlines() if l.strip()]
paths = [l[3:].strip().strip(chr(34)) for l in lines]
fc = len(paths)
dirset, extset = set(), set()
for p in paths:
    if '/' in p:
        dirset.add(p.split('/')[0])
    else:
        dirset.add('(root)')
    extset.add('.' + p.rsplit('.', 1)[1] if '.' in p else '(no-ext)')
ds = ', '.join(sorted(dirset))
es = ' '.join(sorted(extset))
msg = 'auto: [%d files] %s (%s)' % (fc, ds, es)
print('MESSAGE:', msg)
r = subprocess.run(['git', 'commit', '-m', msg], capture_output=True,
                   text=True, encoding='utf-8', env=env)
print('COMMIT:', (r.stdout or r.stderr).strip()[:300])
p = subprocess.run(['git', 'push', 'origin', 'master'], capture_output=True,
                   text=True, encoding='utf-8', env=env)
print('PUSH ec=', p.returncode)
print((p.stdout or p.stderr).strip()[:500])
