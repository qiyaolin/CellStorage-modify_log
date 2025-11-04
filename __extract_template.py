import json
from pathlib import Path
path = Path(r'C:/Users/qiyao/.codex/sessions/2025/09/23/rollout-2025-09-23T13-31-58-019977a1-d636-7840-912e-4d69ccc22246.jsonl')
output_path = Path('restored_cryovial_inventory.html')
with path.open(encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('type') == 'response_item' and obj['payload'].get('type') == 'function_call_output':
            out = obj['payload']['output']
            if isinstance(out, str):
                try:
                    out = json.loads(out)
                except Exception:
                    out = {'output': out}
            if isinstance(out, dict):
                text = out.get('output', '')
            else:
                text = str(out)
            if 'cryovial-search-form' in text and 'extends "base.html"' in text:
                output_path.write_text(text, encoding='utf-8')
                break
