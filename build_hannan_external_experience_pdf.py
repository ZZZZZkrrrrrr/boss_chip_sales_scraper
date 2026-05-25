from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet


OUTPUT = Path(r"C:\Users\96259\Desktop\AIcoding\贸易\汉南电子_外贸业务员_全网经验爬取整理_周铠然.pdf")

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

styles = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "TitleCN",
    parent=styles["Title"],
    fontName="STSong-Light",
    fontSize=21,
    leading=29,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#0F3D3E"),
    spaceAfter=8,
)

SUBTITLE = ParagraphStyle(
    "SubtitleCN",
    parent=styles["Normal"],
    fontName="STSong-Light",
    fontSize=10.2,
    leading=16,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#4B5563"),
    spaceAfter=14,
)

H1 = ParagraphStyle(
    "H1CN",
    parent=styles["Heading1"],
    fontName="STSong-Light",
    fontSize=15.5,
    leading=22,
    textColor=colors.HexColor("#0F766E"),
    spaceBefore=12,
    spaceAfter=7,
)

H2 = ParagraphStyle(
    "H2CN",
    parent=styles["Heading2"],
    fontName="STSong-Light",
    fontSize=12.5,
    leading=18,
    textColor=colors.HexColor("#111827"),
    spaceBefore=8,
    spaceAfter=4,
)

BODY = ParagraphStyle(
    "BodyCN",
    parent=styles["Normal"],
    fontName="STSong-Light",
    fontSize=9.8,
    leading=15.5,
    textColor=colors.HexColor("#111827"),
    alignment=TA_LEFT,
    spaceAfter=4,
)

SMALL = ParagraphStyle(
    "SmallCN",
    parent=BODY,
    fontSize=8.5,
    leading=12.5,
    textColor=colors.HexColor("#374151"),
)

QUOTE = ParagraphStyle(
    "QuoteCN",
    parent=BODY,
    fontSize=9.7,
    leading=15.5,
    leftIndent=8,
    rightIndent=8,
    borderPadding=7,
    borderColor=colors.HexColor("#D1FAE5"),
    backColor=colors.HexColor("#ECFDF5"),
    textColor=colors.HexColor("#064E3B"),
    spaceBefore=3,
    spaceAfter=7,
)

WARN = ParagraphStyle(
    "WarnCN",
    parent=BODY,
    fontSize=9.7,
    leading=15.5,
    leftIndent=8,
    rightIndent=8,
    borderPadding=7,
    borderColor=colors.HexColor("#FED7AA"),
    backColor=colors.HexColor("#FFF7ED"),
    textColor=colors.HexColor("#7C2D12"),
    spaceBefore=3,
    spaceAfter=7,
)

CHECK = ParagraphStyle(
    "CheckCN",
    parent=BODY,
    leftIndent=13,
    firstLineIndent=-9,
)


def p(text, style=BODY):
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def h1(text):
    return p(text, H1)


def h2(text):
    return p(text, H2)


def bullet(text):
    return p("• " + text, CHECK)


def quote(text):
    return p(text, QUOTE)


def warn(text):
    return p(text, WARN)


def tbl(data, widths, header=True):
    rows = []
    for r, row in enumerate(data):
        style = SMALL if r else ParagraphStyle("TH", parent=SMALL, textColor=colors.white)
        rows.append([p(cell, style) for cell in row])
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ]
    t.setStyle(TableStyle(cmds))
    return t


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("STSong-Light", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(18 * mm, 10 * mm, "汉南电子外贸业务员｜全网经验整理")
    canvas.drawRightString(192 * mm, 10 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


sources = [
    ["简历本", "外贸业务员面试经验：笔试、英文邮件/翻译、中文英文初面", "https://www.jianliben.com/article/detail/43223"],
    ["职业圈", "外贸业务员真实面经：简历深挖、岗位理解、供应商/交期/售后情景题", "https://www.job592.com/pay/ms/458.html"],
    ["锤子简历", "外贸业务员面经与避坑：警惕面试套取原公司资源、超长翻译测试等", "https://www.100chui.com/article/147582.html"],
    ["邦阅网", "电子元器件外贸社区问答：客户类型、终端工厂、平台、社媒、海关数据", "https://www.52by.com/faq/78210?reply_id=367200"],
    ["探迹", "电子元器件外贸客户群与客户开发：B2B平台、Google、论坛、老客户转介绍、真实报价", "https://www.tungee.com/about/news-detail/613ec9042527ee70fa865693.html"],
    ["富通天下", "电子元器件国外客户开发：搜索引擎、展会、代理、海关数据、社媒、独立站", "https://www.joinf.com/trade-detail/186.html"],
    ["Gycharm", "Google 开发电子元器件客户：制造商、批发商、品牌商、应用行业关键词", "https://www.gycharm.com/blog-node-654.html"],
    ["LinkedIn 职位", "IC芯片外贸业务员岗位样本：阿里国际站、TBF/HKIN、LinkedIn、Google、Skype、订单跟踪", "https://cn.linkedin.com/jobs/view/ic%E8%8A%AF%E7%89%87%E5%A4%96%E8%B4%B8%E4%B8%9A%E5%8A%A1%E5%91%98-at-%E6%B7%B1%E5%9C%B3%E5%B8%82%E5%8D%8E%E5%B0%94%E7%94%B5%E5%AD%90%E6%9C%89%E9%99%90%E5%85%AC%E5%8F%B8-4156581518"],
    ["LinkedIn Sales", "社媒销售建议：完善资料、找关键人、利用共同关系、关注客户动态、InMail 跟进", "https://business.linkedin.com/sales-solutions/resources/social-selling/top-sales-tips.html."],
    ["HubSpot", "B2B 冷邮件：简洁、个性化、角色相关、清晰CTA、测试跟踪", "https://blog.hubspot.com/sales/the-cold-email-template-that-won-16-new-b2b-customers"],
    ["HubSpot", "LinkedIn prospecting：清晰策略、专业资料、持续建立销售管道", "https://blog.hubspot.com/sales/master-in-sales-linkedin-prospecting"],
    ["Reddit r/b2b_sales", "LinkedIn 销售讨论：不要一上来推销，先个性化连接、评论互动、再问角色相关问题", "https://www.reddit.com/r/b2b_sales/comments/1st3uro/selling_on_linkedin/"],
    ["Reddit r/b2b_sales", "B2B LinkedIn 冷触达讨论：避免 spam，少量有意义跟进，把 LinkedIn 当长期个人品牌与研究渠道", "https://www.reddit.com/r/b2b_sales/comments/1qjlu1x/does_cold_outreach_on_linkedin_actually_work_in/"],
    ["Reddit r/China_irl", "外贸从业讨论：深圳外贸新人底薪、无经验被拒、英语和开发客户压力", "https://www.reddit.com/r/China_irl/comments/1hlx3vt/%E5%A4%96%E8%B4%B8%E6%91%B8%E9%B1%BC%E8%B4%B4%E6%9C%89%E5%81%9A%E5%A4%96%E8%B4%B8%E7%9A%84redditer%E5%90%97%E5%B8%8C%E6%9C%9B%E5%A4%A7%E5%AE%B6%E5%8F%AF%E4%BB%A5%E8%AE%A8%E8%AE%BA%E4%B8%80%E4%B8%8B%E5%B7%A5%E4%BD%9C%E7%9B%B8%E5%85%B3/"],
]

story = []
story.append(p("汉南电子 · 电子元器件外贸业务员", TITLE))
story.append(p("全网公开经验爬取整理｜面试准备版｜周铠然", SUBTITLE))
story.append(quote(
    "整理目标：从公开网站、论坛、社交媒体和岗位样本中提炼“这个岗位真实会问什么、真正看重什么、新人怎么包装、怎么避坑”。"
    "本文件只使用公开可访问网页内容，不绕登录、不采集私密内容。"
))

story.append(h1("0. 结论先看"))
for item in [
    "这个岗位的核心不是“会不会背 IC 名词”，而是：能不能主动开发海外客户、快速处理询盘、按流程报价、持续跟进订单、维护客户信任。",
    "外贸面试高频考察：英文自我介绍/邮件翻译、简历深挖、销售经历、岗位理解、客户开发方法、供应商/交期/质量异常情景题、薪资与抗压。",
    "电子元器件外贸比普通外贸更重视：完整型号、品牌、数量、DC、包装、货期、货源真实性、质量风险、客户目标价、付款和交期。",
    "新人最安全包装：没有正式 IC 外贸经验，但做过客户沟通、销售闭环、需求确认、报价协商、交付跟进；已主动学习 IC 外贸客户开发和 RFQ 流程。",
    "朋友建议里能用的是“我有行业朋友介绍过流程、我看好行业、愿意从基础做起”；不建议编家庭公司、真实客户资源或自称懂行情。"
]:
    story.append(bullet(item))

story.append(h1("1. 本次爬取范围"))
story.append(tbl(
    [["来源类型", "代表来源", "主要提炼内容"],
     ["面试经验网站", "简历本、职业圈、锤子简历", "外贸岗位常见笔试、英文测试、中文/英文面试、情景题和避坑。"],
     ["行业论坛/问答", "邦阅网、探迹、富通天下、Gycharm", "电子元器件外贸客户类型、渠道开发、真实报价、老客户维护。"],
     ["岗位样本", "LinkedIn/招聘页上的 IC 外贸业务员职位", "平台操作、客户开发工具、订单跟踪、抗压和提成模式。"],
     ["社交媒体/社区", "LinkedIn Sales、HubSpot、Reddit B2B sales", "LinkedIn/邮件获客方法、不要硬推、个性化、长期维护。"],
     ["不可稳定抓取平台", "小红书等强登录内容平台", "公开搜索页无法稳定读取全文；本报告不绕登录，只使用公开可访问内容。"]],
    [34 * mm, 55 * mm, 84 * mm]
))

story.append(h1("2. 岗位真实画像：面试官到底在招什么人"))
story.append(h2("2.1 岗位动作"))
for item in [
    "开发客户：社交媒体、邮件、电话、Google、LinkedIn、B2B 平台、论坛、老客户转介绍。",
    "处理询盘：客户发型号后，确认 P/N、品牌、数量、DC、包装、是否原装、目标价、交期、目的地。",
    "报价跟进：和采购/供应商确认库存、价格、货期、质量风险，再反馈客户；客户嫌贵时问 TP 和可放宽条件。",
    "订单交付：PO/PI、付款、备货、质检、发货、物流追踪、签收反馈。",
    "客户维护：记录常用型号、行业、采购节奏、价格敏感度、沟通偏好，争取 Daily RFQ 和复购。"
]:
    story.append(bullet(item))

story.append(h2("2.2 对新人最看重的能力"))
story.append(tbl([
    ["能力", "面试官会怎么判断", "你怎么证明"],
    ["英语基础", "英文自我介绍、邮件回复、资料阅读", "CET6；能写询盘确认邮件；口语诚实说基础商务可。"],
    ["客户开发意愿", "愿不愿意主动找客户，能否接受被拒", "讲校园销售、闲鱼接单、社媒获客学习。"],
    ["流程意识", "是否知道询盘不能乱报价", "背熟 RFQ 八要素：型号、品牌、数量、DC、包装、目标价、交期、目的地。"],
    ["抗压与跟进", "能否持续 follow-up，不怕冷启动", "讲自己能建客户表、每日跟进、复盘回复率。"],
    ["诚信与风险意识", "能否避免乱承诺、质量纠纷", "强调报价前确认货源、交期、原装、质检和付款。"],
], [38 * mm, 60 * mm, 75 * mm]))

story.append(h1("3. 全网面经提炼：可能会怎么面"))
story.append(h2("3.1 常见流程"))
for item in [
    "第一轮：HR 初筛，问求职意向、英语、经验、是否接受底薪、是否能到岗。",
    "笔试/小测试：外贸岗位常见英文邮件回复、中英互译、逻辑分析或简单情景题。",
    "业务主管面：深挖简历、销售经历、开发客户方法、对岗位理解、是否能抗压。",
    "情景题：供应商报价不一致、低价但交期慢、高价但能准时、质量异常、客户赔偿、供应商扯皮。",
    "终面/老板面：看稳定性、赚钱欲望、是否能接受底薪+提成、是否愿意长期做这个行业。"
]:
    story.append(bullet(item))

story.append(h2("3.2 高频问题清单"))
story.append(tbl([
    ["问题", "考察点", "回答方向"],
    ["你没有 IC 外贸经验，为什么能做？", "自知、学习能力、销售底层能力", "承认无正式经验，但有获客/报价/交付闭环，已学习 RFQ 和客户开发。"],
    ["你有什么销售经历？", "是否真做过客户沟通", "校园电动车销售、个人接单、AI 产品客户沟通。"],
    ["你怎么开发海外客户？", "是否懂外贸获客", "Google、LinkedIn、Facebook、B2B、论坛、海关数据、客户表。"],
    ["客户发来型号你怎么处理？", "流程意识", "先补齐型号、品牌、数量、DC、目标价、交期等，再查货报价。"],
    ["客户嫌贵怎么办？", "谈判与跟进", "问目标价和可放宽条件，再核渠道，不乱承诺。"],
    ["供应商交期变化怎么办？", "风险处理", "先内部确认，再如实同步客户，给替代方案或新交期。"],
    ["你英语口语怎么样？", "外贸沟通能力", "CET6，邮件/阅读强，基础商务口语可，复杂谈判继续练。"],
], [48 * mm, 43 * mm, 82 * mm]))

story.append(h2("3.3 面试避坑"))
for item in [
    "不要把“我没有经验”挂在嘴边；改成“我没有正式 IC 外贸经验，但有客户沟通和销售闭环经验”。",
    "如果对方一直套你朋友/前公司的客户、供应商、报价资料，要保持警惕；公开面经里出现过类似套资源风险。",
    "如果公司只谈高提成但讲不清底薪、提成基数、回款后多久发、试用期指标，要继续追问。",
    "不要为了表现懂行业乱说行情；说“我会关注行情，但报价以当天渠道库存、DC、交期为准”。",
]:
    story.append(bullet(item))

story.append(PageBreak())

story.append(h1("4. 电子元器件外贸客户从哪里来"))
story.append(h2("4.1 客户类型"))
story.append(tbl([
    ["客户类型", "例子", "面试表达"],
    ["终端工厂", "EMS、OEM、ODM、PCBA 工厂、工业设备厂、消费电子厂", "稳定但切入难，需要长期建立信任。"],
    ["贸易商/分销商", "IC distributor、broker、wholesaler", "成交快、询盘多，但价格敏感、竞争激烈。"],
    ["品牌商/产品公司", "无人机、医疗电子、安防、照明、通信设备品牌", "可以从产品应用倒推电子元器件需求。"],
    ["当地代理", "目标市场本地代理/渠道", "适合开拓区域市场，借助对方当地资源。"],
], [35 * mm, 58 * mm, 80 * mm]))

story.append(h2("4.2 开发渠道"))
for item in [
    "Google 搜索：产品词 + 客户类型 + 国家/地区，例如 IC distributor USA、electronics manufacturer Germany、PCB manufacturer Vietnam。",
    "LinkedIn：找 Buyer、Purchasing Manager、Sourcing、Procurement、Engineer、Founder 等角色。",
    "B2B 平台：阿里国际站、中国制造、Global Sources、TBF、HKIN、Seekic、ICSource 等。",
    "行业论坛：福步、外贸论坛、电子元器件板块、行业社群，用来找需求、学行情、找同行/买家。",
    "海关数据：看目标市场进口商、采购周期、供应商分布，筛潜在客户。",
    "展会：电子展、慕尼黑电子展、地区行业展，适合建立初步信任和拿名片。",
    "公司网站/独立站/SEO：被动接询盘，展示库存、品牌、资质、联系方式。",
    "老客户转介绍：老客户、客户联系人、贸易参考、客户官网 partners/suppliers 页面。"
]:
    story.append(bullet(item))

story.append(h2("4.3 你面试时可以说的客户开发方法"))
story.append(quote(
    "我会先根据公司主做的国外品牌和主控 IC 品类，确定客户画像，比如 EMS/OEM/ODM、电子制造商、海外分销商、工业设备和消费电子品牌。然后通过 Google、LinkedIn、行业网站、B2B 平台和论坛找公司与联系人，建立客户表，记录国家、官网、联系人、职位、邮箱、主营产品、可能需求和下次跟进时间。第一次触达不直接硬推，而是介绍公司能支持的品牌和优势，询问对方是否有 RFQ 或短缺料需求。"
))

story.append(h1("5. 社媒与邮件获客经验：怎么不像广告狗"))
story.append(h2("5.1 LinkedIn/社媒公开经验提炼"))
for item in [
    "资料先专业：头像、标题、简介要让客户知道你是做电子元器件供应支持的。",
    "先研究再触达：看客户公司、职位、产品线、近期动态，不要群发模板。",
    "连接请求不要一上来推销；接受后先互动，再问与对方角色相关的问题。",
    "社媒不是一次性成交工具，更像长期个人名片和客户研究工具。",
    "跟进要克制：第一条没回，可以发一次有意义 follow-up，再换渠道或暂时放入后续跟进。"
]:
    story.append(bullet(item))

story.append(h2("5.2 适合你背的社媒获客话术"))
story.append(quote(
    "我平时关注社媒开发客户的方法。我的理解是，LinkedIn 不能一上来就发广告，而是先找到目标客户，比如采购、sourcing、buyer、工程负责人，了解他们公司做什么产品，再用简短、具体的问题建立联系。例如问他们是否有某类 IC 或电子元器件短缺需求，而不是直接发一大段公司介绍。"
))

story.append(h2("5.3 冷邮件结构"))
story.append(tbl([
    ["部分", "写法", "电子元器件外贸例子"],
    ["标题", "短、具体、和客户角色相关", "IC sourcing support / Shortage parts support"],
    ["开头", "说明你为什么联系他", "看到贵司做工业控制/电子制造，可能会有 IC sourcing 需求。"],
    ["价值", "一句话说你能帮什么", "我们可支持国外品牌 IC、主控、存储和被动件询价。"],
    ["CTA", "低摩擦提问", "如果有 RFQ，可以发我 P/N 和 QTY，我帮您查库存。"],
    ["跟进", "问目标价/交期/替代，不要骚扰", "如果价格不合适，可告知 target price，我再核渠道。"],
], [25 * mm, 48 * mm, 100 * mm]))

story.append(h2("5.4 英文开发信模板"))
story.append(quote(
    "Subject: IC sourcing support\n\n"
    "Hi [Name],\n\n"
    "This is Kairan from HCN Technology in Shenzhen. We support electronic components sourcing, including ICs, controllers, memory and passive components.\n\n"
    "If you have any shortage parts or RFQs, please feel free to send me the part number and quantity. I can help check stock, date code, lead time and quotation.\n\n"
    "Best regards,\nKairan"
))

story.append(h1("6. RFQ/报价/跟单：电子元器件外贸最核心"))
story.append(h2("6.1 客户发来型号时要补齐的信息"))
story.append(tbl([
    ["信息", "为什么重要", "英文问法"],
    ["Full P/N", "型号差一个字符都可能是不同料", "Could you confirm the full part number?"],
    ["Brand", "同型号不同品牌价格差异大", "Which brand do you need?"],
    ["Quantity", "数量决定价格阶梯和库存", "What quantity do you need?"],
    ["DC", "年份/批号影响价格和可接受度", "Any date code requirement?"],
    ["Condition", "原装、散新、拆机、翻新风险不同", "Do you need original and new parts?"],
    ["Packing", "原厂原包、托盘、卷带、散装", "Any packing requirement?"],
    ["Target Price", "判断是否能做", "May I know your target price?"],
    ["Lead Time", "交期是能否成交关键", "What is your required delivery date?"],
    ["Destination", "影响物流和报价", "Where should we ship the goods?"],
], [32 * mm, 61 * mm, 80 * mm]))

story.append(h2("6.2 面试情景题标准答案"))
story.append(tbl([
    ["情景", "回答逻辑"],
    ["供应商给你的价格比老同事高", "先确认是否同一品牌、DC、包装、数量、付款、交期；再向供应商核价，不直接质疑；必要时找第二渠道比价。"],
    ["低价货不能准时，高价货能准时但利润低", "先看客户交期是否硬性；如果客户赶交期，优先保交付和信誉；同步说明两个方案，让客户选择。"],
    ["货有质量问题但责任不明", "先收集证据：照片、检测报告、批次、包装、签收记录；内部协同采购/质检/供应商，再给客户处理方案。"],
    ["客户嫌贵", "问目标价、数量、交期、DC 可否放宽；重新核渠道；做不了就如实反馈，不乱承诺。"],
    ["供应商交期延误", "第一时间确认新交期和原因，主动同步客户，给替代货源或拆单方案，降低客户损失。"],
], [45 * mm, 128 * mm]))

story.append(h2("6.3 你的流程化回答"))
story.append(quote(
    "我不会拿到型号就直接报价。电子元器件尤其是 IC 外贸，型号、品牌、数量、DC、包装、交期、原装状态和付款方式都会影响报价和风险。我的流程是：先补齐客户需求，再找采购或供应商确认库存和价格，报价时写清有效期、DC、交期和包装，客户反馈后继续跟进目标价和可接受条件。"
))

story.append(PageBreak())

story.append(h1("7. 结合你简历的回答模板"))
story.append(h2("7.1 自我介绍"))
story.append(quote(
    "您好，我叫周铠然，本科是数据科学与大数据技术，英语六级。虽然我没有正式做过 IC 外贸业务员，但我有客户沟通和销售相关实践。\n\n"
    "之前在 AI 产品实习中，我参与客户需求梳理、产品介绍、Demo 演示和客户反馈跟进；在校期间也做过校园电动车销售和个人接单，通过校园社群、朋友圈、闲鱼和转介绍触达客户，完成需求确认、报价沟通、交付和售后维护。\n\n"
    "我现在比较想往电子元器件外贸销售方向发展，已经在学习通过 Google、LinkedIn、邮件和 B2B 平台开发客户，也在学习 IC 外贸的询盘、报价、DC、交期和订单跟进流程。我愿意从基础做起，把客户开发和跟单流程跑熟。"
))

story.append(h2("7.2 没经验怎么说"))
story.append(quote(
    "我没有正式 IC 外贸经验，但我不是客户沟通和销售小白。我做过获客、需求确认、报价、成交、交付和售后闭环。IC 外贸的产品知识和平台流程我还在学习，但我已经知道这个岗位核心是客户开发、询盘回复、快速报价、订单跟进和长期维护。我愿意从基础型号、客户表、开发信和 RFQ 流程开始做。"
))

story.append(h2("7.3 你为什么看好这个行业"))
story.append(quote(
    "我看好电子元器件外贸，是因为它不是纯一次性销售，客户复购和长期合作很重要。这个行业产品型号多、信息变化快、价格和交期波动大，业务员需要持续学习和快速响应。我本身学习能力、信息检索和客户跟进能力比较强，所以想在这个方向长期积累。"
))

story.append(h2("7.4 朋友建议的安全说法"))
story.append(quote(
    "我有行业朋友给我讲过一些电子元器件贸易流程，所以我知道自己不能装懂。客户问货时要先确认型号、数量、DC、目标价和交期；报价要看当天渠道和库存；质量和交期不能乱承诺。我现在希望先进入这个行业，把客户开发、询报价和订单跟进这些基础动作做扎实。"
))

story.append(warn(
    "不建议说：我家里/父母/朋友公司就在做这个，所以我有资源。除非完全真实。更稳妥的说法是：我有朋友在行业里，向他了解过流程和行情，因此更确定自己想入行。"
))

story.append(h1("8. 面试中文高频问答"))
qa = [
    ("过去有销售经验吗？",
     "有一些销售相关实践，主要是校园电动车销售和个人接单。电动车销售是先对接本地门店了解货源和价格，再通过校园社群、朋友圈、同学转介绍触达客户，沟通预算、续航、使用场景和售后需求后进行推荐、报价、成交和后续跟进。个人接单则是通过闲鱼、朋友圈等渠道获取需求，完成需求确认、报价沟通、交付和售后维护。"),
    ("你想做外贸还是国内？",
     "我更倾向外贸方向。我的英语六级，英文阅读和邮件沟通基础比较好，而且我对通过 Google、LinkedIn、Facebook、邮件等渠道开发海外客户比较感兴趣。外贸也更考验客户开发、信息检索和持续跟进，这些和我的能力比较匹配。"),
    ("你接触过 SSD、CPU、内存条等服务器业务吗？",
     "目前还没有正式做过这类业务，但我有主动了解过存储、CPU、内存等基础硬件品类，也知道这类产品在品牌、型号、容量、频率、代际、成色、渠道、交期上都需要重点确认。如果岗位需要，我可以从型号、参数、报价流程和客户需求匹配开始快速学习。"),
    ("你怎么看底薪 5-6K？",
     "我理解外贸销售一般是底薪加提成。因为我是转入电子元器件外贸方向，前期更看重平台、培训、产品线和客户资源。底薪方面我希望在 6K 左右，具体可以结合试用期、提成机制和考核方式沟通。"),
    ("你能接受主动开发客户吗？",
     "可以接受。我知道外贸业务员不能只等询盘，尤其是电子元器件贸易，需要主动找客户、建客户表、发开发信、持续跟进。我平时也在学习社媒和搜索引擎开发客户的方法。"),
    ("你最大的短板是什么？",
     "短板是没有正式 IC 外贸实操经验，所以刚开始产品型号和平台流程需要学习。但我的优势是学习能力强、执行力强、有客户沟通和销售闭环经验。我会用客户表、产品表和每日复盘来缩短上手周期。"),
]
for q, a in qa:
    story.append(h2(q))
    story.append(quote(a))

story.append(h1("9. 英文准备"))
story.append(h2("9.1 英文自我介绍"))
story.append(quote(
    "Hello, my name is Kairan Zhou. I majored in Data Science and Big Data Technology, and I have passed CET-6.\n\n"
    "I do not have formal working experience in IC foreign trade yet, but I have experience in customer communication, requirement analysis, quotation discussion and follow-up. I am interested in electronic components and foreign trade sales, and I am learning product knowledge, customer development methods and RFQ handling process.\n\n"
    "I am willing to start from the basics, learn fast, and work hard to develop customers and follow orders."
))

story.append(h2("9.2 英文 RFQ 回复"))
story.append(quote(
    "Thanks for your inquiry. Could you please confirm the full part number, brand, quantity, date code requirement, target price, delivery schedule and destination? I will check the stock and get back to you soon."
))

story.append(h2("9.3 客户嫌贵"))
story.append(quote(
    "Thanks for your feedback. May I know your target price and required delivery date? I will check again with our suppliers and try to find a better solution for you."
))

story.append(h2("9.4 报价有效期"))
story.append(quote(
    "Please note that the quotation is subject to final stock confirmation. The price is valid for today due to market fluctuation."
))

story.append(h1("10. 面试反问问题"))
for item in [
    "公司目前主做哪些国外品牌？主控 IC 主要是 MCU、存储、通信、电源还是其他方向？",
    "客户主要是海外 EMS/OEM 工厂、终端工厂，还是贸易商/分销商更多？",
    "新人入职后是否有产品知识、报价流程、平台操作和开发信培训？谁带新人？",
    "客户来源是公司分配询盘、平台客户，还是完全需要自己开发？",
    "试用期主要考核什么：客户开发数量、有效询盘、报价数量、成交额还是过程指标？",
    "底薪是否固定 5-6K？试用期底薪多少？提成按销售额还是毛利？回款后多久发？",
    "报价时采购、销售、质检、物流怎么配合？质量问题由谁处理？",
    "公司是否有 B2B 平台、LinkedIn、海关数据、邮箱系统或 CRM？"
]:
    story.append(bullet(item))

story.append(h1("11. 你明天可以照着执行的准备清单"))
story.append(tbl([
    ["时间", "动作", "目标"],
    ["面试前一天", "背熟自我介绍、没经验解释、RFQ流程、英文自我介绍", "让回答有逻辑，不慌。"],
    ["面试前一天", "查汉南电子官网/企查查/BOSS页面，记住成立时间、地点、半导体/芯片、主做国外品牌", "证明你做过功课。"],
    ["面试当天路上", "复习 10 个词：P/N、QTY、DC、TP、Lead Time、MOQ、PO、PI、EMS、OEM", "面试官问基础时不空白。"],
    ["面试中", "先承认无正式经验，再强调销售闭环、英语、社媒获客、学习能力", "不装老手，也不像纯小白。"],
    ["面试结束", "问培训、客户来源、提成、试用期考核、报价协作", "判断公司是否适合入门。"],
], [28 * mm, 84 * mm, 61 * mm]))

story.append(h1("12. 入职后 30/60/90 天计划"))
story.append(tbl([
    ["阶段", "目标", "动作"],
    ["30 天", "熟悉产品和流程", "整理公司主做品牌/型号；学习 RFQ、报价、PI、PO、交期、付款；建立客户开发表模板。"],
    ["60 天", "开始稳定开发客户", "每天通过 Google/LinkedIn/B2B/论坛找客户，发送开发信，记录回复率，跟进有效询盘。"],
    ["90 天", "形成客户池和询盘节奏", "沉淀重点客户、常用型号、价格敏感度；提升报价速度；争取小单成交或稳定 RFQ。"],
], [25 * mm, 55 * mm, 93 * mm]))

story.append(h1("13. 来源清单"))
story.append(p("以下为本次公开网页检索与整理使用的主要来源。PDF 中均为总结与改写，不复制大段原文。", SMALL))
story.append(tbl([["平台", "主题", "链接"]] + sources, [25 * mm, 74 * mm, 74 * mm]))

story.append(h1("14. 最后背诵版"))
story.append(quote(
    "我没有正式 IC 外贸经验，但我不是销售和客户沟通小白。我做过校园销售、个人接单和 AI 产品客户沟通，完整经历过找客户、确认需求、报价沟通、交付跟进和售后维护。我现在已经在学习电子元器件外贸的基础流程，比如通过 Google、LinkedIn、邮件和 B2B 平台开发客户，客户问货时确认型号、品牌、数量、DC、目标价、交期和付款方式，再去匹配渠道报价。我愿意从基础做起，先把产品、客户开发和订单跟进流程跑熟。"
))


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=18 * mm,
    bottomMargin=16 * mm,
)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)
print(OUTPUT)
