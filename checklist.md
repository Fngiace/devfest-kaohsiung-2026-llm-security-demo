# 2026-11-03 候選上台機驗收

- [x] M0：M1 Pro／32GB 真實環境鎖與環境檢查。
- [x] M1：八支腳本各三次，24/24 通過。
- [x] M2：秒數、token 數、token/s 中位數與初始建議。
- [x] M3：三設定真實 request/response、欄位結論。
- [x] M4：完成候選掃描並誠實回報沒有連續五次合格的 N。
- [ ] M4：五次一致 LIVE 重現未達成；改用本機 N448 真實回應備援。
- [x] M5：57 項 pytest 全過，整個程序小於 3 秒。
- [ ] M5：完整回歸 23/24，RAG 攻擊一次未重現；防禦 12/12 通過。
- [x] M6：naive 全過、strict 兩壞一好；首行合成警語。
- [x] M7：政策外部化、拒絕刪除、逐次 JSONL 稽核。
- [x] M8：本機 fallback、十份截圖文字替代素材、RUNSHEET。
- [x] 最終彩排：9 LIVE 通過、2 預定備援；純備援 11 段亦通過。
- [x] 推論只走 localhost；準備階段的模型下載、安裝與 Git 使用網路。
- [x] 原始攻擊、prompt、canary、requirements 與 COSCUP fallback 完整性通過。
- [x] 全部提交在 devfest-kh-2026，main 未修改。

細節與來源見 REPORT.md；未勾選項目不能宣稱成功。
