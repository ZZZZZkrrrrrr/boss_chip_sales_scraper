from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(r"C:\Users\96259\Desktop\AIcoding")
JSON_PATH = next(ROOT.glob("*/BOSS*_20260428_022919.json"))


def has_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def level(job: dict) -> tuple[str, list[str], list[str]]:
    title = job.get("job_name", "") or ""
    exp = job.get("experience", "") or ""
    degree = job.get("degree", "") or ""
    text = "\n".join(str(job.get(k, "") or "") for k in [
        "job_name", "experience", "degree", "company", "tags", "skills", "description"
    ])

    positives: list[str] = []
    risks: list[str] = []

    if "经验不限" in exp:
        positives.append("经验不限")
    if "学历不限" in degree or "高中" in degree or "中专" in degree:
        positives.append(f"学历门槛低：{degree}")
    elif "大专" in degree:
        positives.append("大专可投")
    elif "本科" in degree:
        risks.append("本科门槛")
    if re.search(r"小白|新手|应届|可接受应届|2026届|经验不限|无经验", text):
        positives.append("描述/标签对新人友好")
    if re.search(r"培养|培训|带教|老带新|导师|晋升通道", text):
        positives.append("有培养/培训信号")
    if re.search(r"提供.{0,10}(客户|资源|线索)|分配.{0,10}(客户|资源|线索)|公司提供", text):
        positives.append("有资源/线索支持")
    if re.search(r"电话|网络|销售专员|销售代表|市场拓展", text):
        positives.append("偏基础销售动作")

    hard_bad = [
        "不招小白", "无经验勿扰", "必须有销售经验", "自带客户", "自带资源",
    ]
    if has_any(text, hard_bad):
        risks.append("明确排斥零经验或要求自带资源")
    if re.search(r"(1|一|2|两|3|三)年.{0,8}(销售|芯片|IC|半导体|电子元器件).*经验", text):
        risks.append("描述里要求年限经验")
    if re.search(r"经理|总监|负责人|合伙人|资深|大客户|KA|海外|外贸", title):
        risks.append("岗位名称偏资深/外贸/大客户")
    if "外贸" in text or "英语" in text or "海外" in text or "B2B" in text:
        risks.append("可能有外贸/英语门槛")
    if "熟悉" in text and re.search(r"熟悉.{0,16}(芯片|IC|半导体|电子元器件|元器件|市场|行业)", text):
        risks.append("要求熟悉芯片/元器件市场")

    if "明确排斥零经验或要求自带资源" in risks:
        return "不建议", positives, risks
    if "岗位名称偏资深/外贸/大客户" in risks:
        return "不建议", positives, risks
    if exp not in ("经验不限", "在校/应届", "1年以内") and not re.search(r"应届|小白|无经验|培养", text):
        return "不建议", positives, risks + [f"经验栏为{exp}"]

    risk_count = len(risks)
    pos_count = len(positives)
    if ("经验不限" in positives or exp in ("在校/应届", "1年以内")) and pos_count >= 3 and risk_count == 0:
        return "A优先", positives, risks
    if ("经验不限" in positives or re.search(r"应届|小白|培养", text)) and risk_count <= 1:
        return "B可投", positives, risks
    return "C备选", positives, risks


def main() -> None:
    jobs = json.loads(JSON_PATH.read_text(encoding="utf-8"))["jobs"]
    buckets = {"A优先": [], "B可投": [], "C备选": [], "不建议": []}
    for job in jobs:
        lv, pos, risks = level(job)
        buckets[lv].append((job, pos, risks))

    for lv in ["A优先", "B可投", "C备选", "不建议"]:
        print("\n", lv, len(buckets[lv]))
        for job, pos, risks in buckets[lv][:40]:
            desc = (job.get("description") or "").replace("\n", " ")
            print(f"- {job.get('company')} | {job.get('job_name')} | {job.get('experience')} | {job.get('degree')} | 页{job.get('source_page')}")
            print("  +", "；".join(pos[:5]) or "无")
            print("  -", "；".join(risks[:5]) or "无明显硬伤")
            print("  desc:", desc[:130])


if __name__ == "__main__":
    main()
