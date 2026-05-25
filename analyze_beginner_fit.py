from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(r"C:\Users\96259\Desktop\AIcoding")
JSON_PATH = next(ROOT.glob("*/BOSS*_20260428_022919.json"))


POSITIVE_PATTERNS = [
    ("明确接受小白", r"接受.{0,8}小白|小白|新手|销售小白"),
    ("接受应届/实习/无经验", r"应届|无经验|经验不限|不限经验|可接受应届|接受应届"),
    ("公司培养/带教/培训", r"培养|培训|带教|老带新|导师|完善的晋升|晋升通道"),
    ("提供资源/线索", r"提供.{0,8}(客户|资源|线索)|分配.{0,8}(客户|资源|线索)|公司.{0,8}资源"),
    ("电话/网络/面销基础销售", r"电话销售|网络销售|销售代表|销售专员|销售助理|市场拓展"),
]

NEGATIVE_PATTERNS = [
    ("硬性销售经验", r"必须有销售经验|有.{0,8}销售经验|1年以上.{0,8}销售|一年以上.{0,8}销售|相关行业销售经验|IC销售工作经验|芯片销售经验|半导体销售经验"),
    ("要求熟悉行业/产品", r"熟悉.{0,12}(芯片|IC|半导体|电子元器件|元器件|行业|产品|市场)|了解.{0,12}(芯片|IC|半导体|电子元器件)"),
    ("资深/经理/大客户", r"资深|经理|总监|负责人|合伙人|大客户|KA|Key Account|百万"),
    ("客户资源要求", r"自带.{0,8}(客户|资源)|客户资源|渠道资源|行业资源"),
    ("外语/外贸门槛", r"外贸|海外|英语|俄语|日语|韩语|小语种|B2B"),
]


def score(job: dict) -> tuple[int, list[str], list[str]]:
    title = job.get("job_name", "") or ""
    exp = job.get("experience", "") or ""
    degree = job.get("degree", "") or ""
    text = "\n".join(str(job.get(k, "") or "") for k in [
        "job_name",
        "experience",
        "degree",
        "company",
        "tags",
        "skills",
        "welfare",
        "description",
    ])

    s = 50
    reasons: list[str] = []
    risks: list[str] = []

    if "经验不限" in exp:
        s += 22
        reasons.append("经验不限")
    elif "在校" in exp or "应届" in exp:
        s += 20
        reasons.append("应届/在校可投")
    elif "1年以内" in exp:
        s += 8
        reasons.append("经验要求较低")
    elif "1-3年" in exp:
        s -= 10
        risks.append("标注1-3年经验")
    elif "3-5年" in exp:
        s -= 25
        risks.append("标注3-5年经验")
    elif "5-10年" in exp or "10年以上" in exp:
        s -= 40
        risks.append("标注高年限经验")

    if "学历不限" in degree:
        s += 12
        reasons.append("学历不限")
    elif "大专" in degree:
        s += 4
        reasons.append("大专门槛")
    elif "本科" in degree:
        s -= 6
        risks.append("本科门槛")

    if re.search(r"助理|专员|代表|市场销售|电话|网络|销售\b", title):
        s += 6
        reasons.append("岗位名称偏基础销售")
    if re.search(r"经理|总监|负责人|合伙人|资深|大客户", title):
        s -= 22
        risks.append("岗位名称偏管理/资深")
    if "外贸" in title or "海外" in title:
        s -= 12
        risks.append("岗位偏外贸/海外")

    for name, pat in POSITIVE_PATTERNS:
        if re.search(pat, text, re.I):
            s += {
                "明确接受小白": 28,
                "接受应届/实习/无经验": 20,
                "公司培养/带教/培训": 12,
                "提供资源/线索": 10,
                "电话/网络/面销基础销售": 8,
            }[name]
            reasons.append(name)

    for name, pat in NEGATIVE_PATTERNS:
        if re.search(pat, text, re.I):
            s -= {
                "硬性销售经验": 24,
                "要求熟悉行业/产品": 16,
                "资深/经理/大客户": 20,
                "客户资源要求": 18,
                "外语/外贸门槛": 14,
            }[name]
            risks.append(name)

    if re.search(r"接受.{0,8}小白", text) and re.search(r"必须有销售经验|线上电销经验|面销经验", text):
        risks.append("接受小白但要求已有销售/电销/面销经验")
        s -= 10

    return max(0, min(100, s)), list(dict.fromkeys(reasons)), list(dict.fromkeys(risks))


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    jobs = data["jobs"]
    ranked = []
    for job in jobs:
        fit_score, reasons, risks = score(job)
        ranked.append({**job, "score": fit_score, "reasons": reasons, "risks": risks})

    ranked.sort(key=lambda x: (-x["score"], int(x.get("source_page") or 0), x.get("company", "")))

    print("path", JSON_PATH)
    print("总岗位", len(jobs))
    print("经验不限", sum(1 for j in jobs if "经验不限" in (j.get("experience") or "")))
    print("学历不限", sum(1 for j in jobs if "学历不限" in (j.get("degree") or "")))
    print("明确含小白/新手/应届/培养/无经验", sum(1 for j in jobs if re.search(r"小白|新手|应届|培养|无经验", "\n".join(str(j.get(k, "") or "") for k in ["job_name", "tags", "skills", "description"]))))
    print("高分>=80", sum(1 for j in ranked if j["score"] >= 80))

    print("\nTOP 40")
    for i, job in enumerate(ranked[:40], 1):
        desc = (job.get("description") or "").replace("\n", " ")
        print(f"{i}. {job['score']} | {job.get('company')} | {job.get('job_name')} | {job.get('experience')} | {job.get('degree')} | 页{job.get('source_page')}")
        print("   +", "；".join(job["reasons"][:6]))
        print("   -", "；".join(job["risks"][:6]) or "无明显硬门槛")
        print("   desc:", desc[:180])

    print("\nAVOID 25")
    for job in sorted(ranked, key=lambda x: x["score"])[:25]:
        print(f"{job['score']} | {job.get('company')} | {job.get('job_name')} | {job.get('experience')} | {job.get('degree')} | risks={';'.join(job['risks'][:5])}")


if __name__ == "__main__":
    main()
