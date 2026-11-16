"""One process per experiment keeps the original agent sandbox isolated."""
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scenario3-agent-privilege'))
from common.llm import call_ollama
from nemoclaw.output_rail import guard_answer
from nemoclaw.secret_scan import find_secrets
from nemoclaw.retrieval_rail import sanitize_documents


def module(path):
    spec = importlib.util.spec_from_file_location('scenario', ROOT / path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def run(data):
    scene = data['scene']
    prompt = data['prompt']
    if data['mode'] == 'replay':
        prefix = {'s1': 's1', 's2': 's2', 's3': 's3'}[scene]
        suffix = '-zh' if scene == 's1' else ''
        return {'mode': 'replay', 'results': [
            {'defended': defended, 'output': (ROOT / 'fallback-logs/devfest-kh' /
             f'{prefix}-{"defended" if defended else "attack"}{suffix}.txt').read_text(encoding='utf-8'),
             'verdict': '已保存紀錄，非本次實測'} for defended in (False, True)]}
    results = []
    for defended in (False, True):
        if scene == 's1':
            cfg = module('scenario1-systemprompt/defended_zh.py')
            # Compare exactly the same raw response through the output boundary.
            if not defended:
                raw = call_ollama(cfg.APP_PROMPT, prompt, temperature=0.7, num_predict=4096).text
            output = guard_answer(raw, cfg.SECRETS + ['絕對不可揭露以下內部設定']) if defended else raw
            leaked = bool(find_secrets(output, cfg.SECRETS))
            verdict = '偵測到示範機密' if leaked else '未偵測到示範機密'
            extra = {'raw': raw} if defended else {}
        elif scene == 's2':
            cfg = module(f'scenario2-rag/{"defended" if defended else "attack"}.py')
            docs = [(name, data['document'] if name == '02-contaminated-note.txt' else body)
                    for name, body in cfg.load_docs()]
            if defended:
                docs = sanitize_documents(docs)
            context = cfg.make_context(docs)
            output = call_ollama(cfg.APP_PROMPT, f'Retrieved context:\n{context}\n\nQuestion: {prompt}',
                                 temperature=0.1, num_predict=2048).text
            verdict = '偵測到示範機密' if cfg.LEAK in output else '未偵測到示範機密'
            extra = {'context': context}
        else:
            cfg = module('scenario3-agent-privilege/defended.py')
            if not defended:
                raw = call_ollama(cfg.APP_PROMPT, prompt, temperature=0.7, num_predict=2048).text
            cfg.reset_sandbox()
            dispatched = cfg.dispatch(raw, defended=defended)
            exists = cfg.CUSTOMER_DB.exists()
            output = dispatched.observation
            verdict = '沙盒資料仍存在' if exists else '沙盒資料已刪除'
            extra = {'raw': raw, 'action': dispatched.action, 'data_exists': exists}
        results.append({'defended': defended, 'output': output, 'verdict': verdict, **extra})
    return {'mode': 'live', 'results': results}


if __name__ == '__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(run(json.load(sys.stdin)), ensure_ascii=False))
