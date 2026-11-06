import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('src/retailmind/ui/i18n.py', 'r', encoding='utf-8') as f:
    text = f.read()

rules = re.findall(r'([^{]+)\{([^}]+)\}', text)
for sel, body in rules:
    if any(k in sel for k in ['stSidebar', 'stHeader', 'stToolbar', 'stApp', 'display: none', 'visibility']):
        print('SELECTOR:', sel.strip().replace('\n', ' '))
        for line in body.splitlines():
            if any(k in line for k in ['display', 'visibility', 'width', 'transform', 'overflow', 'position', 'z-index']):
                print('   ', line.strip())
