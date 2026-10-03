import re
from pathlib import Path
root=Path(r'C:\k230_deploy\.venv_deploy\Lib\site-packages')
need=('NNCASE_SIMULATOR','simulator','SIMULATOR_PATH','NNCASE_PLUGIN')
for p in list(root.glob('*.dll'))+list(root.glob('*.pyd'))+list(root.glob('nncase/*.dll')):
    try: data=p.read_bytes()
    except Exception: continue
    vals=[]
    for m in re.finditer(rb'[\x20-\x7e]{4,}',data):
        s=m.group().decode('latin1')
        if any(k.lower() in s.lower() for k in need): vals.append(s)
    if vals:
        print('\n'+str(p))
        print('\n'.join(sorted(set(vals))[:80]))
