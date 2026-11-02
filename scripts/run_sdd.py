"""Repeat M0–M8 on this machine, preserving earlier evidence and every failure.

Run only after `ollama pull gemma4:e4b` succeeds. Installation and Git transport
are preparation; all model requests in the stages use the local transport.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from statistics import median
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.local_api import save_json

PY = str(ROOT / "venv/bin/python")
WARNING = "⚠ 合成測資，用於示範判定邏輯，非實測結果"


class Run:
    def __init__(self, name: str):
        self.base = ROOT / "evidence" / name
        self.base.mkdir(parents=True, exist_ok=True)
        self.status = {}
        self.commands = []
        self.started = datetime.now().astimezone().isoformat()
        self.audit_offset = len((ROOT / "audit/actions.jsonl").read_text().splitlines())

    def read(self, name: str, default=None):
        path = self.base / name
        return json.loads(path.read_text()) if path.exists() else default

    def run(self, stage: str, args: list[str], target: str, timeout=7200):
        path = self.base / target
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite {path}")
        print(f"START {stage}: {' '.join(args)}", flush=True)
        before = time.perf_counter()
        with path.open("w") as output:
            try:
                result = subprocess.run(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                        env={**os.environ, "PYTHONUNBUFFERED": "1"}, timeout=timeout)
                code = result.returncode
            except subprocess.TimeoutExpired:
                output.write(f"\nTIMEOUT: {timeout} seconds\n")
                code = 124
        row = {"stage": stage, "command": args, "returncode": code,
               "wall_seconds": time.perf_counter() - before,
               "finished_at": datetime.now().astimezone().isoformat(),
               "output": str(path.relative_to(ROOT))}
        self.commands.append(row)
        save_json(self.base / "commands.json", self.commands)
        print(f"END {stage}: exit={code}, {row['wall_seconds']:.2f}s", flush=True)
        return row

    def checkpoint(self, stage: str, detail: str, *extra: str):
        self.report()
        paths = [str(self.base.relative_to(ROOT)), "REPORT.md", *extra]
        subprocess.run(["git", "add", "--", *paths], cwd=ROOT, check=True)
        subprocess.run(["git", "-c", "user.name=Codex", "-c", "user.email=codex@openai.com",
                        "commit", "-m", f"devfest-kh: {stage} {detail}"], cwd=ROOT, check=True)

    def matrix(self, stage: str, phase: str):
        self.run(stage, [PY, "scripts/run_matrix.py", "--phase",
                        str(self.base.relative_to(ROOT / "evidence") / phase), "--repeats", "3"],
                 f"{phase}/console.txt")
        rows = self.read(f"{phase}/results.json", [])
        self.status[stage] = ("完成" if len(rows) == 24 and all(r["passed"] for r in rows)
                              else f"部分完成：已執行；{sum(r['passed'] for r in rows)}/{len(rows)} 通過")
        return rows

    def execute(self):
        # Preserve the original lock separately before replacing the current-machine lock.
        self.run("M0 version", ["ollama", "--version"], "m0/ollama-version.txt")
        self.run("M0 list", ["ollama", "list"], "m0/ollama-list.txt")
        self.run("M0 show", ["ollama", "show", "gemma4:e4b"], "m0/ollama-show.txt")
        capture = self.run("M0 capture", [PY, "scripts/check_env.py", "--capture"], "m0/capture.txt")
        if capture["returncode"]:
            raise RuntimeError("Cannot capture runtime; inspect the actual error in m0/capture.txt")
        shutil.copyfile(ROOT / "env-lock.json", self.base / "m0/env-lock.json")
        check = self.run("M0 check", [PY, "scripts/check_env.py"], "m0/check.txt")
        self.status["M0"] = "完成" if check["returncode"] == 0 else "部分完成：環境不符"
        self.checkpoint("M0", "lock actual candidate laptop and local model", "env-lock.json")

        initial = self.matrix("M1", "m1")
        self.checkpoint("M1", "record all 24 actual scenario trials including failures", "audit/actions.jsonl")
        self.run("M2", [PY, "scripts/build_timing.py", "--source", str(self.base / "m1/results.json")],
                 "m2/timing.txt")
        self.status["M2"] = "完成；與 M1 共用三次量測，沒有把備援算成實測"
        self.checkpoint("M2", "publish this laptop's measured timing and live recommendations", "timing-m2.md")

        self.run("M3", [PY, "tech-demo/a_raw_api/probe_raw.py", "--out-dir", str(self.base / "m3/out")],
                 "m3/probe.txt")
        self.status["M3"] = "完成三設定探測；HTTP 錯誤也保留" if len(self.read("m3/out/summary.json", [])) == 3 else "部分完成"
        self.checkpoint("M3", "preserve raw requests and responses for three thinking settings")

        self.run("M4 scan", [PY, "tech-demo/b_fail_open/scan_budget.py", "--extended",
                             "--out-dir", str(self.base / "m4/out")], "m4/scan.txt")
        self.run("M4 compare", [PY, "tech-demo/b_fail_open/run_compare.py", "--repeat", "5"], "m4/compare.txt")
        shutil.copyfile(ROOT / "tech-demo/b_fail_open/config.json", self.base / "m4/config.json")
        comparisons = self.read("m4/out/comparison-results.json", [])
        verified = len(comparisons) == 5 and all(r["verified_comparison"] for r in comparisons)
        self.status["M4"] = "完成：五次一致" if verified else "實驗完成：未證明五次一致，現場用備援／程式差異"
        self.checkpoint("M4", "record actual truncation scan and five comparisons", "tech-demo/b_fail_open/config.json")

        self.run("M5 relock", [PY, "scripts/check_env.py", "--capture"], "m5/capture.txt")
        self.run("M5 env", [PY, "scripts/check_env.py"], "m5/check.txt")
        tests = self.run("M5 pytest", [PY, "-m", "pytest", "-v"], "m5/pytest.txt")
        save_json(self.base / "m5/test-timing.json", tests)
        regression = self.matrix("M5", "m5-regression")
        if tests["returncode"] or tests["wall_seconds"] >= 3:
            self.status["M5"] += f"；pytest exit={tests['returncode']}，{tests['wall_seconds']:.3f} 秒"
        self.checkpoint("M5", "verify normalized scanning and repeat all scenario regressions",
                        "env-lock.json", "audit/actions.jsonl")

        harness = self.run("M6", ["sh", "tech-demo/d_harness/run_d.sh"], "m6/harness.txt")
        text = (self.base / "m6/harness.txt").read_text()
        healthy = (harness["returncode"] == 0 and text.splitlines()[0] == WARNING
                   and text.count("HARNESS INVALID") == 2 and text.count("HARNESS VALID") == 1)
        self.status["M6"] = "完成：naive 全過；strict 兩壞一好；首行警語正確" if healthy else "部分完成：檢查未通過"
        self.checkpoint("M6", "verify synthetic harness controls without any model call")

        policy_test = self.run("M7 policy", [PY, "-m", "pytest", "-v", "tests/test_policy.py",
                                             "tests/test_dispatch_policy.py", "tests/test_sandbox.py"], "m7/policy-tests.txt")
        current = (ROOT / "audit/actions.jsonl").read_text().splitlines()[self.audit_offset:]
        records = [json.loads(line) for line in current]
        (self.base / "m7/actions.jsonl").write_text("\n".join(current) + "\n")
        self.run("M7 audit display", [PY, "scripts/audit_tail.py"], "m7/tail.txt")
        defenses = [r for r in regression if r["case"] == "s3-defended"]
        self.status["M7"] = ("完成：外部政策拒絕刪除，工具呼叫有稽核" if policy_test["returncode"] == 0
                             and len(defenses) == 3 and all(r["passed"] for r in defenses)
                             and any(r["decision"] == "deny" for r in records) else "部分完成：詳見政策測試與實際工具回應")
        self.checkpoint("M7", "verify external execution policy and this run's audit records", "audit/actions.jsonl")

        self.run("M8 integrity", [PY, "scripts/verify_integrity.py"], "m8/integrity.json")
        self.delivery(initial, regression)
        self.run("M8 final env", [PY, "scripts/check_env.py"], "m8/final-env-check.txt")
        self.status["M8"] = "完成備援、十份截圖文字素材與操作表；終端機截圖受工具限制"
        self.checkpoint("M8", "deliver real current-machine fallbacks and stage runsheet",
                        "fallback-logs/devfest-kh", "screenshots", "RUNSHEET-devfest-kh.md", "env-lock.json")
        print(f"ALL STAGES EXECUTED: {self.base}", flush=True)

    def delivery(self, initial, regression):
        lock = json.loads((ROOT / "env-lock.json").read_text())
        header = f"# generated_at={datetime.now().astimezone().isoformat()} model_digest={lock['ollama']['digest']} machine={lock['machine']['chip']}\n"
        fallback = ROOT / "fallback-logs/devfest-kh"
        screenshots = ROOT / "screenshots"
        old = self.base / "previous/delivery"
        old.mkdir(parents=True, exist_ok=True)
        for folder in (fallback, screenshots):
            shutil.copytree(folder, old / folder.name, dirs_exist_ok=True)
        selected = {}
        for name in dict.fromkeys(r["case"] for r in initial):
            group = [r for r in (regression if "defended" in name else initial) if r["case"] == name]
            row = next((r for r in group if r["passed"]), group[-1])
            note = (f"source={row['stdout']}; passed={row['passed']}; exit={row['returncode']}\n"
                    + "assertions=" + json.dumps(row["assertions"], ensure_ascii=False) + "\n\n")
            if not row["passed"]:
                note += "⚠ 本次未通過，不能宣稱成功；沒有以其他機器的輸出代替。\n"
            text = header + note + (ROOT / row["stdout"]).read_text()
            (fallback / f"{name}.txt").write_text(text)
            selected[name] = (text, row)
        sources = {"b-compare.txt": "m4/compare.txt", "c-pytest.txt": "m5/pytest.txt",
                   "d-harness.txt": "m6/harness.txt", "a-raw-json.txt": "m3/probe.txt",
                   "s3-audit.jsonl": "m7/actions.jsonl"}
        for name, source in sources.items():
            (fallback / name).write_text(header + (self.base / source).read_text())
        panels = {"s06-s1-attack": ["s1-attack-zh"], "s19-s1-defended": ["s1-defended-zh"],
                  "s20-s2": ["s2-attack", "s2-defended"], "s21-s3": ["s3-defended"]}
        for panel, names in panels.items():
            text = "\n\n".join(selected[n][0] for n in names)
            if panel == "s21-s3":
                text += "\nAUDIT:\n" + (self.base / "m7/actions.jsonl").read_text()
            (screenshots / f"{panel}.txt").write_text(text)
        row = selected["s1-attack-zh"][1]
        trace = ROOT / row["raw_responses"]
        traces = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
        # Select one actual response with a closed thinking section containing a canary.
        messages = [t["response"].get("message", {}) for t in traces]
        message = next((m for m in messages if re.search(r"<thinking>.*SUPERVISOR-7788.*</thinking>",
                                                        m.get("content", ""), re.S)), messages[-1] if messages else {})
        for part in ("thinking", "answer"):
            match = re.search(fr"<{part}>(.*?)</{part}>", message.get("content", ""), re.S | re.I)
            segment = match.group(1) if match else f"未觀察到閉合的 <{part}>；保留原始 content：\n{message.get('content', '')}"
            if part == "thinking" and message.get("thinking"):
                segment += "\nmessage.thinking（獨立原生欄位）：\n" + message["thinking"]
            (screenshots / f"s07-{part}.txt").write_text(header + f"same_response_source={row['raw_responses']}\n" + segment)
        for panel, source in {"m3-raw-json": "a-raw-json.txt", "m4-compare": "b-compare.txt",
                              "m5-pytest": "c-pytest.txt", "m6-harness": "d-harness.txt"}.items():
            (screenshots / f"{panel}.txt").write_text((fallback / source).read_text())
        (screenshots / "README.md").write_text("# 本機真實輸出的截圖文字素材\n\n"
            "Computer Use 拒絕存取 com.apple.Terminal，依 SDD 改交付十份純文字素材；"
            "限制紀錄見本次 evidence 目錄的 setup/screenshot-capability.txt。"
            "請使用深色終端、至少 20pt，cat 對應文字後手動截圖。"
            "保留未通過標示、來源與 M6 合成測資警語；s07 兩份來自同一個回應。\n")
        save_json(self.base / "m8/delivery-manifest.json", {
            "model_digest": lock["ollama"]["digest"], "machine": lock["machine"],
            "selected_runs": {n: v[1] for n, v in selected.items()},
            "screenshots": "ten real-output text alternatives; manual terminal screenshots required"})
        self.runsheet(initial)

    def runsheet(self, rows):
        lines = ["# DevFest 高雄現場操作表：本次候選機", "", "開講前 10 分鐘：", "",
                 "1. 接電源、關閉大型程式，確認指定模型已下載。",
                 "2. `venv/bin/python scripts/check_env.py`；非零先排除差異。",
                 "3. `venv/bin/python scripts/warmup.py`。",
                 "4. 深色終端、至少 20pt；開啟勿擾、關閉通知。",
                 "5. `cat fallback-logs/devfest-kh/c-pytest.txt` 確認離線備援可讀。", "",
                 "以下皆在專案根目錄執行。備援是本機實測文字，未通過紀錄有明確標示。", "",
                 "| 段落 | 精確指令 | 秒數中位數 | 成功 | 建議 | 失敗切換 | 台上口徑 |",
                 "|---|---|---:|---:|---|---|---|"]
        for name in dict.fromkeys(r["case"] for r in rows):
            group = [r for r in rows if r["case"] == name]
            seconds = median(r["wall_seconds"] for r in group)
            passed = sum(r["passed"] for r in group)
            advice = "預錄" if passed != 3 or seconds > 60 else ("LIVE" if seconds <= 30 else "LIVE，備妥預錄")
            cmd = "venv/bin/python " + " ".join(group[0]["command"][1:])
            speech = ("每個生成欄位都要確認去向。" if name.startswith("s1") else
                      "檢索資料不是指令來源。" if name.startswith("s2") else "工具權限由程式端政策決定。")
            lines.append(f"| {name} | `{cmd}` | {seconds:.2f} | {passed}/3 | {advice} | `cat fallback-logs/devfest-kh/{name}.txt` | {speech} |")
        probe = self.read("m3/out/summary.json", [])
        comparisons = self.read("m4/out/comparison-results.json", [])
        config = self.read("m4/config.json", {})
        tests = self.read("m5/test-timing.json", {})
        harness = next((c for c in self.commands if c["stage"] == "M6"), {})
        compare_seconds = median(r["wall_seconds"] for r in comparisons) if comparisons else 0
        lines += ["", "預期畫面：S1 攻擊檢查 canary，defended 的 Returned to user 不含機密；"
                  "S2 攻擊檢查 ORCHID-ESCALATE-9；S3 defended 顯示 rejected 且 customer_db.json exists: True。", "",
                  "| 技術段落 | 指令 | 預期畫面／實測秒數 | 失敗切換 | 台上口徑 |", "|---|---|---|---|---|",
                  f"| A | `venv/bin/python scripts/demo.py --scene raw-api --mode live` | 三設定原始 JSON；API 合計 {sum(p['total_seconds'] for p in probe):.2f}s | `cat fallback-logs/devfest-kh/a-raw-json.txt` | 先看真實欄位再決定哪些資料能離開後端。 |",
                  f"| A curl | `sh tech-demo/a_raw_api/curl.sh false {self.base.relative_to(ROOT)}/m3/out` | 同一份已保存 request | `cat {self.base.relative_to(ROOT)}/m3/out/false.json` | 直接 HTTP 驗證 runtime。 |",
                  f"| B | `venv/bin/python tech-demo/b_fail_open/run_compare.py` | N={config.get('num_predict')}；中位 {compare_seconds:.2f}s；若 null 則未成功重現 | `cat fallback-logs/devfest-kh/b-compare.txt` | 解析失敗時回固定安全訊息。 |",
                  "| B diff | `cat tech-demo/b_fail_open/diff.patch` | naive 與 fixed 的實際差異 | 同左 | 缺少閉合標籤時 fail closed。 |",
                  f"| C | `venv/bin/python -m pytest -v` | 全綠；整個程序 {tests.get('wall_seconds', 0):.3f}s | `cat fallback-logs/devfest-kh/c-pytest.txt` | 掃描涵蓋常見包裝，語意改寫仍有限制。 |",
                  f"| D | `sh tech-demo/d_harness/run_d.sh` | 首行合成警語，strict 兩壞一好；{harness.get('wall_seconds', 0):.3f}s | `cat fallback-logs/devfest-kh/d-harness.txt` | 先驗證斷言真的執行。 |",
                  "| 稽核 | `venv/bin/python scripts/audit_tail.py` | 最近三筆決策與規則 | `tail -n 3 fallback-logs/devfest-kh/s3-audit.jsonl` | 每次工具呼叫都留下決策。 |", "",
                  "有 jq：`tail -n 3 audit/actions.jsonl | jq .`；單筆替代："
                  "`tail -n 1 audit/actions.jsonl | venv/bin/python -m json.tool`。", "",
                  "40 分鐘建議節奏：0–5 分鐘介紹；5–14 分鐘 S1 與 A；14–22 分鐘 B 與 C；"
                  "22–28 分鐘 D；28–35 分鐘 S2、S3 與稽核；35–40 分鐘限制與問答。", "",
                  "單次速度不代表穩定：參考 timing-m2.md 的三次成功率與最慢值。"
                  "未重現的段落不能說成功；M6 live 第一行有合成警語，備援檔第一行依 SDD 是時間/digest。"]
        (ROOT / "RUNSHEET-devfest-kh.md").write_text("\n".join(lines) + "\n")

    def report(self):
        lock = self.read("m0/env-lock.json", {})
        base = self.base.relative_to(ROOT)
        initial = self.read("m1/results.json", [])
        regression = self.read("m5-regression/results.json", [])
        probes = self.read("m3/out/summary.json", [])
        comparisons = self.read("m4/out/comparison-results.json", [])
        config = self.read("m4/config.json", {})
        lines = ["# DevFest 高雄 2026：候選上台機重新實測", "",
                 f"本次開始：{self.started}。本次證據：`{base}/`。舊 M2 報告與環境鎖保留在 `{base}/previous/`。",
                 "所有成功與失敗均保留，先前機器的輸出不計入本次成功率。", "", "## 1. 環境摘要", ""]
        if lock:
            lines += [f"- 實際硬體：{lock['machine']['chip']}／{lock['machine']['ram_gb']} GiB；macOS {lock['machine']['macos']}。",
                      f"- Ollama {lock['ollama']['version']}；固定模型 `{lock['ollama']['model']}`；{lock['ollama']['parameter_size']}／{lock['ollama']['quantization']}。",
                      f"- digest：`{lock['ollama']['digest']}`。",
                      f"- Python {lock['python']['version']}；requirements SHA-256 `{lock['python']['requirements_hash']}`。",
                      "- 工作分支 devfest-kh-2026；從指定遠端既有分支續作，保留原有 COSCUP 歷史；main 沒有修改。"]
        lines += ["", "## 2. 各階段結果", "", "| 階段 | 狀態 | 證據目錄 |", "|---|---|---|"]
        for n in range(9):
            stage = f"M{n}"
            lines.append(f"| {stage} | {self.status.get(stage, '待執行')} | {base}/m{n}/ |")
        lines += ["", "## 3. M2 時間與現場建議", ""]
        if "M2" in self.status:
            lines.append((ROOT / "timing-m2.md").read_text().replace("# M2 實測時間表", "### 本機三次實測", 1))
        for label, rows in (("初始", initial), ("M5 回歸", regression)):
            if rows:
                defenses = [r for r in rows if "defended" in r["case"]]
                lines.append(f"{label}：{sum(r['passed'] for r in rows)}/{len(rows)}；防禦 {sum(r['passed'] for r in defenses)}/{len(defenses)}。")
                failed = [f"{r['case']} 第 {r['repeat']} 次（{', '.join(k for k,v in r['assertions'].items() if not v)}；exit={r['returncode']}）" for r in rows if not r["passed"]]
                if failed:
                    lines += ["", "未通過：" + "；".join(failed) + "。"]
        lines += ["", "## 4. M3 原始 API 結論", "", "| think | HTTP | content 機密 | content thinking 段機密 | 原生 thinking 機密 | 秒數 |", "|---|---:|---|---|---|---:|"]
        for row in probes:
            loc = row["locations"]
            lines.append(f"| {row['setting']} | {row['http_status']} | {loc['message.content']} | {loc['message.content.<thinking>']} | {loc['message.thinking']} | {row['total_seconds']:.2f} |")
        if probes:
            native = any(r["locations"]["thinking_field_present"] for r in probes)
            leaks = any(r["locations"][k] for r in probes for k in ("message.content", "message.thinking"))
            lines += ["", f"本 runtime {'有' if native else '未'}觀察到 message.thinking 欄位，各設定機密命中如表。",
                      "原生 thinking 欄位與 content 中由應用程式要求的 <thinking> 是不同位置。",
                      "把整個 message 記錄或回傳時，會把其中命中的機密一併送出。" if leaks else "這次無害查詢未觀察到回應含機密，不能宣稱這組測試造成洩漏。",
                      "think=false 的單次結果不代表其他輸入安全；不以 request 內原本存在的 canary 當成回應洩漏。"]
        lines += ["", "## 5. M4 截斷掃描與五次結果", "",
                  f"選定 N：`{config.get('num_predict')}`；候選集合：`{config.get('candidate_grid', [])}`。最小值限於宣告的遞增候選集合。",
                  "temperature=0、seed=42；沿用原攻擊與原 prompt；不把原生 message.thinking 拼接成 naive 顯示的 content。",
                  "每個候選第一次不合格即淘汰；選中的候選必須連續五次合格，再獨立比較五次。", "",
                  "| 次數 | N | naive 洩漏 | answer 閉合 | fixed 安全 | 完整驗證 |", "|---|---:|---|---|---|---|"]
        for row in comparisons:
            lines.append(f"| {row['repeat']} | {row['num_predict']} | {row['naive_leaked']} | {row['closed_answer']} | {row['fixed_safe']} | {row['verified_comparison']} |")
        lines += ["", "## 6. 偏離 SDD 與原因", "",
                  "- 使用者同意以這台候選上台機試跑；實際是 M1 Pro／32GB，不能把這次量測標成 M2。",
                  "- 遠端既有 devfest-kh-2026 已含全部實作；本次沿用該分支與保護機制，做兩輪獨立完整回歸，沒有假裝重新寫出已存在的修補。",
                  "- 英文 S1 defended 不支援 --live，照實使用 --no-save。",
                  "- M1/M2 共用同批三次有完整 token 計時的實跑；固定三次，不挑成功樣本替代失敗。",
                  "- 模型下載、Git clone 與 pip install 是文件允許的準備連網；模型推論只走 localhost:11434，評分為確定性判定。",
                  "- Terminal 的 Computer Use 存取被工具拒絕；依 SDD 產出十份真實文字素材，需要手動截圖。",
                  "- 原有 requirements.txt 與 requirements-dev.txt 版本完全保留；Python 和 Ollama 使用本機版本並鎖定。",
                  "- env-lock 的 commit 是最後影響 runtime 原始碼的提交，搭配逐檔 hash；M4 config 更新後重新鎖定，避免鎖檔自我參照。", "",
                  "## 7. 待 Fngi 決定", "",
                  "- 依本次成功率、中位數與最慢值決定這台是否上台；不穩定或超時段落建議使用有來源的實測文字備援。",
                  "- 截圖素材使用深色終端、至少 20pt 手動截圖；保留警語與未通過標籤。", "",
                  "## 8. 已知限制", "",
                  "- 正規化掃描無法阻止翻譯、語意改寫、跨段或多層編碼；Finding 是原文 Python 字元位置，編碼命中指向整個 token。",
                  "- 所有機密是展示 canary；刪除只在每次新建的 sandbox/run-* 內進行，路徑逃逸測試另外驗證。",
                  "- 固定 temperature/seed 無法保證跨 runtime、模型 digest 或硬體一致；保留失敗而不改 prompt。",
                  "- M6 success 表示請求完成，healthy 的已知洩漏對照組應被斷言抓到；HARNESS VALID 不代表模型零洩漏。",
                  "- audit 是示範 JSONL，未提供防竄改保證；confirm 不是人類已批准。",
                  "- pytest 的相依棄用警告保留，不為消除警告升級套件。"]
        save_json(self.base / "stage-status.json", self.status)
        (ROOT / "REPORT.md").write_text("\n".join(lines) + "\n")


def main():
    os.environ["TZ"] = "Asia/Taipei"
    time.tzset()
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("run-id must be a single directory name")
    run = Run(args.run_id)
    try:
        run.execute()
    except Exception as exc:
        save_json(run.base / "execution-error.json", {"error": repr(exc), "status": run.status})
        run.report()
        raise


if __name__ == "__main__":
    main()
