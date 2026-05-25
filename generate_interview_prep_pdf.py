from __future__ import annotations

import json
import unicodedata
from datetime import datetime
from pathlib import Path

import fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


TRADE_DIR = Path(r"C:\Users\96259\Desktop\AIcoding\贸易")
PROJECT_DIR = Path(r"D:\Organized\Projects\PyCharm_Project\boss_chip_sales_scraper")
OUTPUT_PDF = TRADE_DIR / "周铠然_芯片销售第一批面试准备_20260428.pdf"
JOBS_JSON = TRADE_DIR / "BOSS直聘_芯片销售_深圳招聘_latest.json"


SOURCE_URLS = [
    ("Indeed：Sales Engineer Interview Questions", "https://www.indeed.com/career-advice/interviewing/sales-engineer-interview-questions"),
    ("Indeed Hire：Sales Engineer Interview Questions 2026", "https://www.indeed.com/hire/interview-questions/sales-engineer"),
    ("HubSpot：Objection Handling", "https://blog.hubspot.com/sales/handling-common-sales-objections"),
    ("HireQuotient：Sales Engineer Interview Questions", "https://www.hirequotient.com/blog/sales-engineer-interview-questions-and-answers"),
    ("职场密码：半导体销售工程师面试题库", "https://mianti.zcmima.cn/qiyemianjing/49720.html"),
]


PRIORITY_ROWS = [
    {
        "priority": "A1 最高优先级",
        "company": "甲象",
        "job": "芯片销售",
        "why": "经验不限、高中门槛；岗位内容是网络/电话开发客户、需求处理、报价、下单、售前售中售后，和你的校园销售、项目咨询接单闭环高度一致。",
        "risk": "喜欢电话沟通；要能接受陌生开发和反复跟进。面试重点讲你如何从闲鱼/社群/朋友圈找到客户并推进成交。",
        "strategy": "主打：我做过从获客、咨询、报价、成交、售后到转介绍的完整动作，愿意从每天打电话、建客户表、跟询价开始。",
    },
    {
        "priority": "A1 最高优先级",
        "company": "深圳市亨智达科技",
        "job": "芯片销售双休+高提成",
        "why": "经验不限、高中门槛；工作明确是电话或网络开发、产品销售、订单处理、回款、客户跟踪报告，适合从基础销售动作切入。",
        "risk": "岗位写年龄25-35且电销经验优先。你不要强调年龄，重点证明自己有线上获客、咨询接待、报价协商和抗压能力。",
        "strategy": "主打：我已经习惯线上沟通客户、记录需求、报价解释和成交后跟进，可以快速适应电话/网络销售节奏。",
    },
    {
        "priority": "A1 最高优先级",
        "company": "富恒兴",
        "job": "芯片销售",
        "why": "经验不限、高中门槛；要求集中在喜欢销售、诚实守信、喜欢电子行业，硬性行业经验较少。",
        "risk": "小团队可能需要主动性强，培训体系未必完整。要提前准备“我入职前两周怎么学习产品线和开发客户”的回答。",
        "strategy": "主打：我不是等客户分配的人，之前就用闲鱼、社群、转介绍找客户，愿意自己做客户线索积累。",
    },
    {
        "priority": "A1 最高优先级",
        "company": "世微半导体",
        "job": "半导体IC（芯片）销售专员",
        "why": "经验不限、大专门槛；岗位写通过公司资源和行业平台开发客户，负责报价、订单、交货计划、回款，并要求持续学习IC知识。",
        "risk": "会考察业务拓展、沟通、谈判、独立开发能力。不能只说想学习，要给出每日开发客户的方法。",
        "strategy": "主打：我有客户沟通和项目推进经验，能把客户需求整理成型号、数量、交期、目标价，再内部询价反馈。",
    },
    {
        "priority": "A1 最高优先级",
        "company": "深圳奇普尼克电子",
        "job": "芯片销售工程师（双休，TOB销售小白培养）",
        "why": "标题明确“小白培养”；1年以内、大专门槛；公司有国内终端和海外终端客户资源待开发，适合新人从客户跟进和深度开发做起。",
        "risk": "TOB销售周期更长，客户多为汽车、医疗、新能源、工业、消费电子；要会讲“长期跟进”和“记录客户需求”。",
        "strategy": "主打：我做过AI方案客户试用反馈和项目交付跟进，理解B端客户不是聊一次就成交，需要持续推进。",
    },
    {
        "priority": "A1 最高优先级",
        "company": "芯科华高",
        "job": "销售专员（可接受应届生，双休）",
        "why": "经验不限、本科门槛，专业不限且接受应届生；职责覆盖邮件、电话、拜访、开发终端客户、询报价、订单合同、交货、回款。",
        "risk": "涉及全球贸易商/制造商和出差展会，可能看重英文与商务规范。你有CET6，可以把英语和资料学习能力带出来。",
        "strategy": "主打：我是数据专业但学习能力强，CET6，能把复杂产品信息整理清楚并用客户听得懂的话表达。",
    },
    {
        "priority": "A1 最高优先级",
        "company": "谷芯羽电子",
        "job": "华强北芯片电子元器件销售-高提成接受小白",
        "why": "经验不限、学历不限，技能标签写接受小白新手、电话销售、网络销售、面销/陌拜，岗位行业就是半导体/元器件/芯片。",
        "risk": "描述也写“必须有销售经验，线上电销经验或面销经验”。你不能说纯小白，要说自己有校园销售和项目咨询接单销售闭环。",
        "strategy": "主打：我有销售经验，只是芯片行业新人；我做过线上咨询接待、价格解释、售后跟进和转介绍。",
    },
    {
        "priority": "A2 高优先级",
        "company": "宏博通",
        "job": "芯片终端销售",
        "why": "经验不限、大专门槛；岗位明确写有ToB销售经验想转电子行业深耕的小白还招2个、一带一，并有采购、助理跟单、物流支持。",
        "risk": "同时写0.5年以上电子元器件终端客户销售经验优先，客户是电子行业头部客户，压力和目标感会更强。",
        "strategy": "主打：我有ToB需求梳理和方案推进经验，愿意从客户建档、需求记录、跟单回款这些基础动作做扎实。",
    },
    {
        "priority": "A2 高优先级",
        "company": "富满微电子集团股份",
        "job": "芯片销售工程师（可接受应届生）",
        "why": "1年以内、大专门槛，标题明确可接受应届生；公司规模更大，岗位职责清晰：客户需求、竞品信息、市场拓展和销售。",
        "risk": "更偏原厂/集团型销售，电子工程、FAE、通信、元器件经验优先；要补电源管理、MOS管、移动电源、无线充基础。",
        "strategy": "主打：我专业第一、学习速度快，有技术理解力，可以快速学习产品线，再用客户沟通能力做销售推进。",
    },
    {
        "priority": "A2 高优先级",
        "company": "昂宇电子",
        "job": "芯片销售工程师",
        "why": "经验不限、大专门槛；描述写可接受优秀应届生；公司代理线多，适合技术理解力较强的应届生切入。",
        "risk": "职责有Design in/Design win、拜访报告、配合技术部门解决问题，面试会更看重学习能力和长期行业意愿。",
        "strategy": "主打：我有AI方案售前支持经验，能配合技术团队把客户问题讲清楚、跟进验证和反馈。",
    },
    {
        "priority": "A2 高优先级",
        "company": "深圳市佳集芯科技",
        "job": "电子元器件/芯片销售（朝九晚六）",
        "why": "1年以内、高中门槛；公司是国产单片机代理和方案公司，要求学习产品特性、客户维护、通过渠道寻找意向客户。",
        "risk": "有电子元器件销售经验优先，且需要熟悉市场行情。你要提前准备MCU、PCBA、消费电子应用这几个关键词。",
        "strategy": "主打：我学习能力强，能把产品特性、客户场景、报价和售后问题整理成表，逐步沉淀客户线索。",
    },
    {
        "priority": "A2 高优先级",
        "company": "昂瑞微",
        "job": "芯片销售经理",
        "why": "在校/应届、本科门槛；职责是客户拓展、产品推广、项目跟踪、订单管理、回款跟踪，和应届培养匹配。",
        "risk": "标题叫经理但实际收应届；偏原厂芯片销售，可能更看重沟通、责任感、项目推进和学生干部经历。",
        "strategy": "主打：我有数学社部长/项目协作经历，也做过客户需求和项目推进，愿意长期学习芯片产品与客户行业。",
    },
    {
        "priority": "B 可投",
        "company": "深圳市联亿芯电子科技",
        "job": "芯片外贸销售",
        "why": "描述明确可接受应届生小白；如果想走外贸方向，CET6和线上获客学习经历可以加分。",
        "risk": "1-3年、大专，且外贸需要英语邮件、询盘、展会、海外客户开发。英语口语和外贸流程要准备。",
        "strategy": "主打：我CET6，平时会学习社媒获客方法，能从B2B平台、官网、LinkedIn、邮件触达客户开始。",
    },
    {
        "priority": "B 可投",
        "company": "恒晟辉",
        "job": "IC销售 芯片销售 元器件销售",
        "why": "经验不限、大专门槛；描述写无销售经验择优录取；工作包含线上渠道开拓海外市场、报价、订单、交货、回款。",
        "risk": "英语可作为工作语言，偏海外销售。只适合你愿意走外贸并能接受英文沟通。",
        "strategy": "主打：我英语六级，愿意从英文产品资料、邮件模板、客户资料表和询价流程开始补齐。",
    },
    {
        "priority": "B 可投",
        "company": "鸿迈电子",
        "job": "芯片销售工程师",
        "why": "虽然经验栏是1-3年，但描述鼓励愿意在电子行业长期发展的优秀人才（含优秀应届毕业生）面试。",
        "risk": "0-20人小公司，可能更希望来人能很快开发业务；需要表现出强开发意愿和执行力。",
        "strategy": "主打：我能根据销售任务做客户拜访计划、目标拆解、备货预测和回款跟踪，不怕从基础动作做起。",
    },
    {
        "priority": "B 可投",
        "company": "芯伯乐电子",
        "job": "（原厂）芯片销售工程师/元器件销售",
        "why": "描述有全流程培训、老板和资深销售带教、公司资源池、公海客户、初级到高级销售路径，对新人友好。",
        "risk": "经验栏写3-5年，系统筛选可能卡你；只能作为高质量练手/争取机会，不放在最前面。",
        "strategy": "主打：我对半导体芯片感兴趣，有技术理解力和销售闭环基础，愿意接受产品线和销售技巧培训。",
    },
    {
        "priority": "C 练手/备选",
        "company": "飞思瑞克",
        "job": "芯片销售（双休）",
        "why": "描述写试用期拉微信群、销售经理协助成交、过程中学习培训，动作对新人相对具体。",
        "risk": "经验栏写3-5年，有责底薪和业绩要求明显，压力较大；适合练习销售面试，不建议第一顺位。",
        "strategy": "主打：我有社群获客和线上触达经验，可以把拉群、筛选潜在客户、需求记录做成标准动作。",
    },
    {
        "priority": "C 练手/备选",
        "company": "富友昌",
        "job": "蓝牙方案销售专员",
        "why": "经验栏写经验不限、学历不限，且有日常技术培训赋能。",
        "risk": "正文要求3年以上电子产品解决方案销售经验、市场资源和人脉，和小白不匹配。除非HR主动约，否则不要作为核心目标。",
        "strategy": "主打：如果面试，只讲AI方案演示和客户需求匹配，不要把自己包装成已有电子方案资源的人。",
    },
]


def norm(text: object) -> str:
    value = "" if text is None else str(text)
    return unicodedata.normalize("NFKC", value).replace("\u200b", "").strip()


def p(text: str, style: ParagraphStyle) -> Paragraph:
    safe = norm(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe = safe.replace("\n", "<br/>")
    return Paragraph(safe, style)


def find_resume_text() -> tuple[Path | None, str]:
    root = Path.home() / "Desktop" / "work"
    files = list(root.rglob("*13692871429*.pdf"))
    target = next((f for f in files if "销售" in f.name), None)
    if not target:
        return None, ""
    doc = fitz.open(str(target))
    text = "\n".join(page.get_text() for page in doc)
    return target, norm(text)


def load_jobs() -> dict[str, dict]:
    data = json.loads(JOBS_JSON.read_text(encoding="utf-8"))
    jobs = {}
    for job in data["jobs"]:
        jobs[norm(job.get("company"))] = job
    return jobs


def make_styles() -> dict[str, ParagraphStyle]:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "CNBase",
        parent=styles["Normal"],
        fontName="STSong-Light",
        fontSize=9.2,
        leading=13,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    return {
        "title": ParagraphStyle(
            "CNTitle",
            parent=base,
            fontSize=22,
            leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#14324A"),
            spaceAfter=10,
        ),
        "subtitle": ParagraphStyle(
            "CNSubtitle",
            parent=base,
            fontSize=11,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=12,
        ),
        "h1": ParagraphStyle(
            "CNH1",
            parent=base,
            fontSize=15,
            leading=20,
            textColor=colors.HexColor("#123B5D"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "CNH2",
            parent=base,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0B6B68"),
            spaceBefore=6,
            spaceAfter=4,
        ),
        "body": base,
        "small": ParagraphStyle(
            "CNSmall",
            parent=base,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#2D3748"),
        ),
        "table": ParagraphStyle(
            "CNTable",
            parent=base,
            fontSize=7.3,
            leading=9.8,
            spaceAfter=0,
        ),
        "table_head": ParagraphStyle(
            "CNTableHead",
            parent=base,
            fontSize=7.6,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.white,
            spaceAfter=0,
        ),
        "quote": ParagraphStyle(
            "CNQuote",
            parent=base,
            fontSize=9,
            leading=13,
            leftIndent=8,
            rightIndent=8,
            backColor=colors.HexColor("#F3F7FA"),
            borderColor=colors.HexColor("#D6E3EA"),
            borderWidth=0.4,
            borderPadding=6,
            spaceBefore=4,
            spaceAfter=6,
        ),
    }


def add_page_number(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("STSong-Light", 8)
    canvas.setFillColor(colors.HexColor("#718096"))
    canvas.drawRightString(285 * mm, 10 * mm, f"第 {doc.page} 页")
    canvas.drawString(12 * mm, 10 * mm, "周铠然｜芯片销售第一批面试准备")
    canvas.restoreState()


def table(data, widths, style, repeat_rows=1) -> LongTable:
    t = LongTable(data, colWidths=widths, repeatRows=repeat_rows, splitByRow=1)
    t.setStyle(style)
    return t


def build_company_table(rows: list[dict], jobs: dict[str, dict], s: dict[str, ParagraphStyle]) -> LongTable:
    header = ["优先级", "公司", "岗位/门槛", "为什么适合小白", "注意点", "面试主打法"]
    data = [[p(x, s["table_head"]) for x in header]]
    for row in rows:
        job = jobs.get(row["company"], {})
        gate = " / ".join(
            x for x in [
                row["job"],
                norm(job.get("experience")),
                norm(job.get("degree")),
                norm(job.get("company_scale")),
                f"页码{norm(job.get('source_page'))}" if job else "",
            ]
            if x
        )
        data.append([
            p(row["priority"], s["table"]),
            p(row["company"], s["table"]),
            p(gate, s["table"]),
            p(row["why"], s["table"]),
            p(row["risk"], s["table"]),
            p(row["strategy"], s["table"]),
        ])

    widths = [25 * mm, 27 * mm, 43 * mm, 66 * mm, 64 * mm, 64 * mm]
    return table(
        data,
        widths,
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#174A65")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        ),
    )


def build_small_table(rows: list[list[str]], widths, s: dict[str, ParagraphStyle]) -> Table:
    data = [[p(cell, s["table_head"]) for cell in rows[0]]]
    for row in rows[1:]:
        data.append([p(cell, s["table"]) for cell in row])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B6B68")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def add_bullets(story: list, items: list[str], styles: dict[str, ParagraphStyle]) -> None:
    for item in items:
        story.append(p("• " + item, styles["body"]))


def main() -> None:
    jobs = load_jobs()
    resume_path, resume_text = find_resume_text()
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=11 * mm,
        bottomMargin=16 * mm,
        title="周铠然芯片销售第一批面试准备",
        author="Codex",
    )
    s = make_styles()
    story = []

    story.append(p("芯片销售第一批面试准备", s["title"]))
    story.append(p("候选人：周铠然｜目标：深圳芯片/电子元器件销售｜生成日期：2026-04-28", s["subtitle"]))
    story.append(p("核心定位", s["h1"]))
    story.append(
        p(
            "不要把自己说成“完全小白”。更准确的定位是：技术背景转芯片/电子元器件销售的新人，已有客户沟通、需求挖掘、方案讲解、报价协商、项目跟进、售后维护和线上获客意识，愿意从客户开发、询价报价、订单跟进和回款这些基础动作做起。",
            s["quote"],
        )
    )
    story.append(p("简历最该打出去的三张牌", s["h2"]))
    add_bullets(
        story,
        [
            "AI产品/解决方案支持：参与客户沟通、需求梳理、Demo演示、试用反馈和三方协同，能证明你不是只会聊天，而是能理解客户痛点并推动项目。",
            "校园电动车销售：通过闲鱼、表白墙、朋友圈、校园群、班级群和线下转介绍获客，做过线上咨询、线下看车、价格解释、成交推进和售后维护。",
            "校外项目咨询与编程辅导：通过闲鱼、朋友圈、社群、熟人转介绍获取线索，确认需求、周期、交付标准、修改范围，做报价协商、进度同步和交付后跟进。",
            "补充表达：平时会主动学习社媒找客户方法，例如通过行业关键词、企业主页、社群、短视频平台、招聘平台和企查查类渠道找潜在客户线索。",
        ],
        s,
    )
    story.append(Spacer(1, 5))
    story.append(
        build_small_table(
            [
                ["面试中不要这样说", "建议这样说"],
                ["我是小白，想学习。", "我是芯片行业新人，但不是销售和客户沟通小白。我做过获客、需求确认、报价、成交、交付和售后闭环。"],
                ["我没芯片经验。", "我没有芯片行业销售经验，但我有技术理解力和客户推进经验，型号和产品线可以通过培训、资料和客户案例快速补齐。"],
                ["我平时刷视频学找客户。", "我会主动学习社媒获客方法，并把它转成客户线索表、触达话术、需求记录和持续跟进动作。"],
            ],
            [70 * mm, 205 * mm],
            s,
        )
    )

    story.append(PageBreak())
    story.append(p("第一批投递与面试优先级", s["h1"]))
    story.append(
        p(
            "排序逻辑：不看工资，只看小白成功率。优先选择经验不限/应届可投/小白培养/公司提供资源/岗位动作偏基础销售的岗位；谨慎对待大客户经理、外贸英语强要求、必须自带客户、3年以上行业经验、客户资源型岗位。",
            s["body"],
        )
    )
    story.append(build_company_table(PRIORITY_ROWS, jobs, s))

    story.append(PageBreak())
    story.append(p("首批投递节奏", s["h1"]))
    story.append(
        build_small_table(
            [
                ["批次", "公司", "目标", "准备重点"],
                ["第1天", "甲象、亨智达、富恒兴、世微半导体、奇普尼克、芯科华高、谷芯羽", "拿到最多面试机会，练熟销售闭环表达", "背熟自我介绍、客户开发方法、价格异议处理、无芯片经验回答。"],
                ["第2天", "宏博通、富满微、昂宇、佳集芯、昂瑞微", "冲更正规或技术含量更高岗位", "补产品基础：IC、MCU、MOS、PMIC、BOM、Design-in/Design-win。"],
                ["第3天", "联亿芯、恒晟辉、鸿迈、芯伯乐、飞思瑞克、富友昌", "补充机会和练面试", "外贸岗位准备英文自我介绍和邮件开发；经验栏3-5年的岗位只作为争取/练手。"],
            ],
            [28 * mm, 78 * mm, 78 * mm, 91 * mm],
            s,
        )
    )
    story.append(p("BOSS打招呼模板", s["h2"]))
    story.append(
        p(
            "您好，我是2026届本科生周铠然，数据科学与大数据技术专业，GPA 3.64，专业排名1/63。我虽然是芯片销售新人，但有客户沟通、需求梳理、方案讲解、报价协商、项目跟进和售后维护经历，也做过校园销售和线上接单获客。看到贵司岗位偏客户开发、询报价和订单跟进，我愿意从基础销售动作做起，也能快速学习芯片/电子元器件产品知识，想进一步沟通面试机会。",
            s["quote"],
        )
    )

    story.append(p("1分钟自我介绍", s["h1"]))
    story.append(
        p(
            "您好，我叫周铠然，是广州南方学院数据科学与大数据技术专业2026届本科生，GPA 3.64，专业排名1/63。我之前主要做AI产品方案支持、客户需求梳理和项目交付，也做过校园二手电动车销售和校外项目咨询接单，实际经历过获客、沟通、报价、成交、交付、售后和转介绍这些环节。我现在想转向芯片/电子元器件销售，是因为这个岗位既需要客户沟通，也需要快速学习产品和理解客户应用场景。我承认自己没有芯片行业销售经验，但我有技术理解力、学习速度和完整的客户服务闭环经验，愿意从客户开发、询价报价、订单跟进和客户维护这些基础动作做起。",
            s["quote"],
        )
    )
    story.append(p("30秒版本", s["h2"]))
    story.append(
        p(
            "我是周铠然，2026届本科生，数据科学与大数据技术专业，专业排名1/63。我有AI方案售前支持、校园销售和项目咨询接单经历，做过获客、需求确认、报价、成交、交付和售后。芯片行业我还是新人，但我有技术理解力和销售闭环经验，愿意从客户开发、询报价、跟单回款这些基础动作做起。",
            s["quote"],
        )
    )

    story.append(p("三段经历怎么讲", s["h1"]))
    story.append(
        build_small_table(
            [
                ["经历", "面试表达重点", "可以证明的能力"],
                ["AI方案售前/解决方案支持", "客户觉得审核效率低、流程不标准、人力成本高，我参与需求梳理、Demo演示、试用反馈和技术/产品/业务协同，让客户理解方案价值。", "需求挖掘、方案讲解、技术转商务、跨部门推进。"],
                ["校园电动车销售", "我通过闲鱼、校园群、朋友圈和转介绍找客户，根据预算、续航、成色和售后需求推荐车型，解释价格差异，推进成交并做售后跟进。", "线上获客、客户接待、报价协商、成交推进、售后维护。"],
                ["校外项目咨询接单", "我通过闲鱼、社群和熟人介绍获取线索，确认需求、周期、交付标准和修改范围，再结合复杂度报价，交付后跟进评价和后续需求。", "需求确认、报价意识、项目推进、客户信任、复购转介绍。"],
            ],
            [54 * mm, 150 * mm, 72 * mm],
            s,
        )
    )

    story.append(PageBreak())
    story.append(p("芯片销售必背行业基础", s["h1"]))
    story.append(
        build_small_table(
            [
                ["关键词", "你要会这样解释"],
                ["IC/芯片/电子元器件", "IC是集成电路；电子元器件范围更大，还包括电阻、电容、电感、二三极管、MOS、MCU、存储芯片、电源管理芯片等。"],
                ["BOM", "客户项目需要采购的物料清单。销售通常根据BOM确认品牌、型号、封装、数量、交期和目标价。"],
                ["OEM/ODM/EMS", "OEM偏代工生产，ODM偏设计+制造，EMS偏电子制造服务；这些企业通常是元器件采购的重要客户。"],
                ["FAE", "现场应用工程师，负责技术支持、选型、问题定位和客户技术沟通。销售要会把客户问题准确转给FAE。"],
                ["Design-in/Design-win", "Design-in是进入客户设计选型；Design-win是客户最终采用并进入项目/量产机会。"],
                ["询价/报价/交期/回款", "芯片销售基础闭环：客户给型号和需求，销售内部确认库存和成本，报价并跟进订单、交付、对账和回款。"],
                ["客户最关心", "价格、库存、交期、原装正品、替代型号、账期、售后响应、供货稳定性。"],
            ],
            [48 * mm, 228 * mm],
            s,
        )
    )
    story.append(p("芯片销售完整流程", s["h2"]))
    add_bullets(
        story,
        [
            "找客户：根据公司产品线锁定消费电子、工控、安防、医疗、新能源、机器人、PCBA、方案公司、贸易商等目标客户。",
            "问需求：确认客户常用品牌、缺料型号、封装、数量、交期、目标价、是否可替代、项目阶段。",
            "询价报价：把型号、品牌、数量、交期、票税、付款方式整理清楚，再和采购/主管确认价格和库存。",
            "推进成交：说明价格构成、交期、品质保证、售后响应，必要时提供样品或替代型号。",
            "交付回款：跟进订单、物流、验收、对账、开票和回款，保持客户复购。",
        ],
        s,
    )

    story.append(p("客户开发方法：把社媒学习讲专业", s["h1"]))
    story.append(
        p(
            "我会先根据公司产品线确定目标客户，比如消费电子、工控、安防、LED、电源、PCBA、方案公司、贸易商。然后通过企查查、官网、招聘信息、短视频平台、行业微信群/QQ群、展会名单、B2B平台、LinkedIn或外贸平台找线索，整理公司名、主营产品、联系人、可能用到的型号或品类。第一次触达不会硬推产品，而是先问常用品牌、缺料型号、交期压力、替代料需求或长期采购需求。有需求后记录型号、品牌、封装、数量、交期、目标价，再内部询价报价并持续跟进。",
            s["quote"],
        )
    )

    story.append(PageBreak())
    story.append(p("高频面试问答", s["h1"]))
    qa_rows = [
        ["问题", "建议回答"],
        ["你没有芯片销售经验，为什么能做？", "我没有芯片行业销售经验，但不是销售小白。我做过校园销售和项目咨询接单，经历过获客、需求确认、报价、成交、售后和转介绍；也做过AI方案客户需求梳理、Demo演示和项目跟进。芯片型号可以学，但客户沟通、需求判断、推进反馈这些基础能力我已经有。"],
        ["你怎么开发客户？", "先看公司产品线和目标行业，建立客户画像；再从企查查、官网、招聘信息、展会名单、社群、短视频平台、B2B平台找线索；触达时先问常用品牌、缺料型号、交期痛点和替代需求；有机会后把型号、数量、交期、目标价整理给采购/主管确认。"],
        ["客户嫌价格贵怎么办？", "先确认是不是同品牌、同型号、同封装、同批次、同交期、同税运条件，避免客户拿不同条件比价。再强调正品、交期、售后和稳定供应价值；如果客户确实有目标价，我会反馈采购/主管，看能否通过数量、账期、替代型号或阶梯报价解决。"],
        ["客户问你不懂的型号怎么办？", "不乱答。我会把完整型号、品牌、封装、数量、用途、交期、目标价记下来，先查资料，再请教采购/FAE/主管，并给客户明确回复时间。销售的专业不是当场假装懂，而是准确记录、快速确认、可靠回复。"],
        ["你怎么理解芯片销售？", "不是简单卖货，而是围绕客户项目需求匹配供应：缺料、交期、替代、降本、供货稳定和售后响应。销售要连接客户、采购、仓库、技术和财务，把询价、报价、订单、交付、对账、回款形成闭环。"],
        ["你的优势是什么？", "第一，学习能力强，专业排名1/63；第二，有技术理解力，能理解复杂产品并转成客户听得懂的表达；第三，有销售闭环经历，做过线上获客、报价、成交、售后和转介绍；第四，做过B端AI方案支持，知道客户不是成交就结束，还要验证价值和持续跟进。"],
        ["你的短板是什么？", "芯片行业型号、产品线和客户资源还需要积累。但我已经开始补IC、MCU、MOS、存储、电源管理、BOM、OEM/ODM/EMS等基础概念。入职后我会先跟产品线、客户案例、报价流程和客户开发话术，把基础动作做扎实。"],
        ["你能接受电话销售/陌生开发吗？", "可以。我之前做校园销售和接单咨询时，本质上也要主动触达陌生客户、解释需求、筛选意向、持续跟进。电话和网络开发会更标准化，我会把每天触达数量、有效需求、报价机会和跟进状态记录下来。"],
        ["客户不回复怎么办？", "先判断客户阶段。如果只是初次触达，我会换一个更具体的问题或价值点；如果已经询价，我会围绕交期、价格有效期、替代型号、样品机会做跟进；如果长期不回，就降低频率，定期发送有价值的信息，避免无意义骚扰。"],
        ["为什么选择芯片/电子元器件销售？", "这个行业既有销售挑战，也有技术学习深度。我的背景是数据和AI，学习复杂产品比较快，同时我又做过客户沟通和销售闭环，所以希望进入一个能长期积累客户、产品和供应链能力的行业。"],
        ["你对薪资怎么看？", "我现在第一目标是进入行业、把客户开发和产品知识打扎实。薪资按公司岗位体系来，我更看重新人培训、产品线、客户资源、提成规则是否清楚，以及能不能长期成长。"],
    ]
    story.append(build_small_table(qa_rows, [58 * mm, 218 * mm], s))

    story.append(PageBreak())
    story.append(p("按公司类型准备不同话术", s["h1"]))
    story.append(
        build_small_table(
            [
                ["公司类型", "对应公司", "你要重点讲什么", "反问面试官"],
                ["基础客户开发型", "甲象、亨智达、富恒兴、谷芯羽", "校园销售、闲鱼/社群获客、报价解释、售后维护、能接受电话和网络开发。", "新人每天大概需要触达多少客户？公司有客户线索表或产品培训吗？"],
                ["资源/平台支持型", "世微、宏博通、奇普尼克", "B端需求梳理、客户跟进、记录需求、询报价、订单交付和长期维护。", "公司资源是老客户、公海、平台线索还是完全自开发？新人从老客户维护还是新客户开发开始？"],
                ["技术销售/原厂代理型", "富满微、昂宇、昂瑞微、芯科华高、佳集芯", "技术理解力、AI方案演示、学习速度、把复杂产品讲清楚、配合FAE/技术解决问题。", "新人重点学习哪些产品线？常见客户行业和应用场景是什么？销售和FAE怎么分工？"],
                ["外贸/海外客户型", "联亿芯、恒晟辉", "CET6、英文资料学习、B2B平台/社媒找客户、邮件开发、询盘整理。", "主要开发渠道是阿里国际站、环球资源、Google、LinkedIn还是展会？新人是否有英文邮件模板？"],
                ["练手/高风险型", "芯伯乐、飞思瑞克、富友昌、鸿迈", "积极主动、愿意从基础动作做起，但不要夸大电子行业客户资源。", "经验要求是否硬性？新人是否有带教和产品培训？试用期考核指标是什么？"],
            ],
            [42 * mm, 52 * mm, 119 * mm, 63 * mm],
            s,
        )
    )
    story.append(p("每场面试必问的5个问题", s["h2"]))
    add_bullets(
        story,
        [
            "新人入职前1个月主要学习哪些产品线和客户案例？",
            "公司是原厂、代理、现货贸易，还是终端客户开发为主？",
            "客户资源是公司分配一部分，还是完全自己开发？",
            "新人通常从询报价、跟单、老客户维护，还是直接开发新客户开始？",
            "销售、采购、FAE/技术支持、跟单助理之间怎么协作？",
        ],
        s,
    )

    story.append(PageBreak())
    story.append(p("面试前一天复习清单", s["h1"]))
    add_bullets(
        story,
        [
            "背熟30秒和1分钟自我介绍，开头一定说“芯片行业新人，不是销售小白”。",
            "准备3个故事：AI方案客户需求、校园电动车成交、项目咨询接单报价。每个故事都要有客户来源、客户痛点、你做了什么、结果是什么。",
            "打开目标公司BOSS页面，记住产品线、客户类型、经验/学历要求、岗位职责和一个你想问的问题。",
            "背熟行业基础词：IC、MCU、MOS、PMIC、Memory、BOM、OEM、ODM、EMS、FAE、Design-in、Design-win。",
            "准备客户开发计划：每天找多少线索、怎么分类、怎么触达、怎么记录需求、怎么跟进报价。",
            "准备价格异议回答：先确认同型号同条件，再谈正品、交期、售后、稳定供应，最后反馈采购争取方案。",
            "不要主动把话题拉到工资。用户当前目标是不看工资、优先拿offer和行业入口。",
        ],
        s,
    )
    story.append(p("面试当天表达纪律", s["h2"]))
    add_bullets(
        story,
        [
            "每个回答尽量落到动作：找客户、建表、问需求、记型号、询价、报价、跟订单、催回款、售后维护。",
            "承认短板但立刻给补救方案：没有行业经验，但能通过产品线资料、客户案例、报价流程和带教快速补齐。",
            "不要说“我什么都愿意学”就结束，要说“我入职第一周先背产品线和常见型号，第二周跟老销售整理客户案例，第三周开始建立自己的线索表”。",
            "如果被问到社媒找客户，强调你学习的是方法论，不是刷视频：关键词搜索、客户画像、线索表、触达话术、持续跟进。",
        ],
        s,
    )

    story.append(p("资料来源", s["h1"]))
    source_rows = [
        ["类型", "来源"],
        ["本地岗位数据", str(JOBS_JSON)],
        ["本地Excel", str(TRADE_DIR / "BOSS直聘_芯片销售_深圳招聘_完整_20260428.xlsx")],
        ["本地简历", str(resume_path) if resume_path else "未找到销售岗简历PDF"],
    ]
    for name, url in SOURCE_URLS:
        source_rows.append([name, url])
    story.append(build_small_table(source_rows, [55 * mm, 220 * mm], s))
    if resume_text:
        story.append(p("简历核对摘要", s["h2"]))
        story.append(
            p(
                "已从销售岗简历中核对：2026届本科、数据科学与大数据技术、GPA 3.64/4、专业排名1/63；具备客户沟通、需求挖掘、方案讲解、报价协商、项目跟进与售后维护能力；经历包含AI方案支持、校园电动车销售、校外项目咨询与编程辅导。",
                s["small"],
            )
        )

    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(OUTPUT_PDF)


if __name__ == "__main__":
    main()
