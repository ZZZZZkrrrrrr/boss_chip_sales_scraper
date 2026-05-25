from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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


OUTPUT = Path(r"C:\Users\96259\Desktop\AIcoding\贸易\汉南电子_电子元器件外贸业务员_面试准备_周铠然.pdf")


pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

styles = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "TitleCN",
    parent=styles["Title"],
    fontName="STSong-Light",
    fontSize=22,
    leading=30,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#0F3D3E"),
    spaceAfter=10,
)

SUBTITLE = ParagraphStyle(
    "SubtitleCN",
    parent=styles["Normal"],
    fontName="STSong-Light",
    fontSize=11,
    leading=18,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#4B5563"),
    spaceAfter=16,
)

H1 = ParagraphStyle(
    "H1CN",
    parent=styles["Heading1"],
    fontName="STSong-Light",
    fontSize=16,
    leading=22,
    textColor=colors.HexColor("#0F766E"),
    spaceBefore=12,
    spaceAfter=8,
)

H2 = ParagraphStyle(
    "H2CN",
    parent=styles["Heading2"],
    fontName="STSong-Light",
    fontSize=13,
    leading=19,
    textColor=colors.HexColor("#111827"),
    spaceBefore=8,
    spaceAfter=5,
)

BODY = ParagraphStyle(
    "BodyCN",
    parent=styles["Normal"],
    fontName="STSong-Light",
    fontSize=10.2,
    leading=16.5,
    textColor=colors.HexColor("#111827"),
    alignment=TA_LEFT,
    spaceAfter=5,
)

SMALL = ParagraphStyle(
    "SmallCN",
    parent=BODY,
    fontSize=8.7,
    leading=13,
    textColor=colors.HexColor("#374151"),
)

QUOTE = ParagraphStyle(
    "QuoteCN",
    parent=BODY,
    fontSize=10,
    leading=16,
    leftIndent=8,
    rightIndent=8,
    borderPadding=7,
    borderColor=colors.HexColor("#D1FAE5"),
    backColor=colors.HexColor("#ECFDF5"),
    textColor=colors.HexColor("#064E3B"),
    spaceBefore=3,
    spaceAfter=8,
)

CHECK = ParagraphStyle(
    "CheckCN",
    parent=BODY,
    leftIndent=14,
    firstLineIndent=-10,
)


def para(text, style=BODY):
    text = escape(str(text)).replace("\n", "<br/>")
    return Paragraph(text, style)


def bullet(text):
    return para("• " + text, CHECK)


def h1(text):
    return para(text, H1)


def h2(text):
    return para(text, H2)


def quote(text):
    return para(text, QUOTE)


def table(data, col_widths=None, header=True):
    wrapped = []
    for r, row in enumerate(data):
        style = SMALL if r else ParagraphStyle("TableHeader", parent=SMALL, textColor=colors.white)
        wrapped.append([para(cell, style) for cell in row])
    t = Table(wrapped, colWidths=col_widths, repeatRows=1 if header else 0)
    cmd = [
        ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D1D5DB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        cmd.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F766E")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ])
    t.setStyle(TableStyle(cmd))
    return t


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("STSong-Light", 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(18 * mm, 10 * mm, "汉南电子外贸业务员面试准备")
    canvas.drawRightString(192 * mm, 10 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


story = []

story.append(para("汉南电子 · 电子元器件外贸业务员", TITLE))
story.append(para("周铠然面试准备手册｜根据岗位 JD、个人简历、行业朋友建议整理", SUBTITLE))
story.append(quote(
    "本资料的核心策略：不要装作有 IC 外贸实操经验；要表现为“有销售/客户沟通底层能力，已主动学习行业流程，愿意从客户开发、询报价、订单跟进这些基础做起”。"
))

story.append(h1("目录"))
for item in [
    "1. 岗位画像与公司判断",
    "2. 你的匹配点、风险点和包装主线",
    "3. 行业朋友建议如何转成面试话术",
    "4. 必背行业基础与外贸业务流程",
    "5. 客户开发、RFQ、报价、跟单场景话术",
    "6. 高频中文问答与英文问答",
    "7. 薪资、反问、试用期沟通",
    "8. 面试前 24 小时清单与 30/60/90 天计划",
]:
    story.append(bullet(item))

story.append(PageBreak())

story.append(h1("1. 岗位画像与公司判断"))
story.append(h2("1.1 岗位基本信息"))
story.append(table([
    ["项目", "内容", "你要怎么理解"],
    ["岗位", "电子元器件外贸业务员", "不是纯技术岗，核心是海外客户开发、询盘回复、报价跟进、订单交付和回款。"],
    ["薪资", "BOSS 页面 10-15K；HR 沟通底薪 5-6K", "大概率是底薪 + 提成。面试时重点问清提成基数、发放时间、试用期考核。"],
    ["经验/学历", "1-3年，大专；英语、国际贸易相关专业优先", "你不是硬匹配，但 CET6、本科、客户沟通实践、学习能力可以弥补。"],
    ["公司", "深圳市汉南电子技术有限公司，2017 年成立，20-99 人，半导体/芯片，未融资", "小型贸易/代理分销公司，可能更看重能否快速开发客户、跟进询盘和执行。"],
    ["地点", "深圳罗湖区深华商业大厦 1106", "你在深圳，通勤和稳定性可以作为加分点。"],
], [28 * mm, 73 * mm, 72 * mm]))

story.append(h2("1.2 JD 拆解"))
for item in [
    "多渠道开展电子元器件外贸业务：说明岗位需要主动开发海外客户，不是只等询盘。",
    "通过社交媒体、邮件、电话沟通开发跟进客户：这和你平时关注社媒获客教程高度相关，要重点讲。",
    "了解客户需求、加深客户印象、提高合作率：考察客户沟通、持续跟进和客户档案管理。",
    "跟进订单交期、货款到账，保障订单交付：考察细心、责任心、跨部门协作和风险意识。",
    "英语听说读写流利/四级以上：你 CET6 是硬加分，但口语要诚实说“基础商务沟通可，复杂谈判仍在提升”。",
    "商业意识、谈判技巧、抗压、开拓能力：需要用校园销售、个人接单、AI 产品客户沟通来证明。",
]:
    story.append(bullet(item))

story.append(h2("1.3 对这家公司的初步判断"))
story.append(para(
    "汉南电子从截图看是电子元器件代理、分销、方案设计开发、技术咨询与服务公司，客户可能包括 EMS/OEM 工厂、工业电子、5G 通信等方向。"
    "HR 说“国外品牌为主，主控 IC 比较多，都做”。这说明公司可能做贸易分销，不一定只做单一代理线。你面试时要问清：主要品牌、客户类型、是否提供询盘、是否有培训、报价和采购如何配合。"
))
story.append(quote(
    "你的第一目标不是证明自己很懂 IC，而是证明：你愿意做客户开发，能快速学习型号和行情，英语邮件能用，客户跟进有耐心，能接受底薪 + 提成模式。"
))

story.append(h1("2. 你的匹配点、风险点和包装主线"))
story.append(h2("2.1 你的真实优势"))
for item in [
    "英语六级：外贸岗位至少能支撑英文资料阅读、邮件沟通、基础商务表达。",
    "数据科学本科，专业排名 1/63，GPA 3.64/4：证明学习能力强、信息检索和结构化能力强。",
    "AI 产品实习：做过客户需求梳理、产品介绍、Demo 演示、客户反馈跟进，能迁移到外贸客户需求确认。",
    "校园电动车销售：有真实销售闭环，包含找货源、控成本、社群推广、客户沟通、报价、成交、售后。",
    "闲鱼/朋友圈/转介绍接单：有线上获客、需求确认、报价协商、交付维护的实践。",
    "关注社媒获客：可以连接到 LinkedIn、Facebook、Google、邮件开发海外客户。",
    "在深圳稳定：可到岗、可长期发展，不需要长期回学校。",
]:
    story.append(bullet(item))

story.append(h2("2.2 你的风险点"))
for item in [
    "没有正式 IC 外贸实习经验：不要说自己有经验，要说“有底层销售能力 + 主动学习行业流程”。",
    "简历里写了“熟悉蓝牙和血压芯片”等表述，面试时可能被追问：要降调解释为“主动学习了解过，不是实操报价经验”。",
    "口语不是强项：不要说口语非常流利，应该说“基础商务沟通可以，复杂谈判还在提升”。",
    "岗位写 1-3 年经验：你要用学习能力、销售实践、朋友行业建议和入行意愿弥补。",
    "底薪 5-6K：要提前接受这是销售岗底薪模式，关注提成规则和客户资源，而不是只看底薪。",
]:
    story.append(bullet(item))

story.append(h2("2.3 推荐主线"))
story.append(quote(
    "我没有正式 IC 外贸经验，但我有客户沟通、需求确认、报价协商、交付跟进和售后维护的实践。"
    "我英语六级，能处理基础英文邮件和资料；平时也在学习电子元器件产品知识、客户开发方法和询报价流程。"
    "我愿意从产品型号、客户开发、询盘回复、报价跟单这些基础做起，目标是在这个行业长期发展。"
))

story.append(h1("3. 行业朋友建议如何转成面试话术"))
story.append(h2("3.1 可用的建议"))
for item in [
    "可以说“有朋友在电子元器件/存储/报价相关行业，我向他了解过贸易商的业务流程和行情波动”。",
    "可以说“这个行业靠信息差、客户开发、快速响应和长期关系，不是简单卖货”。",
    "可以说“贸易商要关注价格、交期、货源真实性、DC、客户目标价和回款风险”。",
    "可以说“我目前不敢说懂行情，但知道存储、主控 IC、国外品牌芯片价格波动快，需要持续跟市场和供应商”。",
    "可以说“底薪 5-6K 我能理解，销售岗更看重提成机制、客户资源、培训和成长”。",
]:
    story.append(bullet(item))

story.append(h2("3.2 不建议照搬的说法"))
for item in [
    "不要编自己有 IC 客户、真实订单或供应商资源。面试官一追问型号、价格、客户背景，很容易露馅。",
    "不要编父母、家人、舍友一定在这个行业，除非是真的。可以说“朋友/行业朋友给我讲过一些流程”。",
    "不要绝对说“存储现在一定降价”或“IC 一定涨价”。行情变化很快，你应该说“近期价格波动大，具体以当天渠道报价为准”。",
    "不要说自己技术很强，可以给客户做深度方案选型。你可以说“我能配合技术/采购同事做基础需求确认和信息整理”。",
]:
    story.append(bullet(item))

story.append(h2("3.3 如果被问：你怎么知道这个行业？"))
story.append(quote(
    "我有朋友在电子元器件相关行业，所以最近也向他了解过一些贸易商的业务流程。我的理解是，这个行业不是单纯卖产品，而是要靠客户开发、信息搜集、快速响应和供应链匹配。客户问货时，要确认完整型号、品牌、数量、DC、是否原装、目标价、交期和付款方式，再去匹配货源和报价。"
))

story.append(h2("3.4 行情表达的安全版本"))
story.append(para(
    "面试官如果问你是否了解行情，可以用保守版本。根据 TrendForce 2026 年 3 月底发布的记忆体价格调查，AI 服务器需求和供应配置变化推动 2026 年二季度 DRAM、NAND 合约价上行。"
    "因此你可以说："
))
story.append(quote(
    "我不敢说自己已经很懂行情，但我知道电子元器件特别是存储、主控 IC、服务器相关料价格波动很快。近期 AI 服务器需求、存储供应紧张等因素会影响 DRAM、NAND、SSD 等价格，所以报价不能凭感觉，要以当天供应商渠道、库存、DC 和交期为准。"
))

story.append(h1("4. 必背行业基础与外贸业务流程"))
story.append(h2("4.1 术语速记"))
story.append(table([
    ["术语", "意思", "面试中怎么用"],
    ["IC", "集成电路", "客户问货的核心产品类型，必须确认完整料号。"],
    ["MCU", "微控制器，很多主控 IC 属于这一类", "汉南说主控 IC 多，你可以先记 MCU、控制器、通信控制等。"],
    ["Memory", "存储类芯片，如 DRAM、NAND、Flash、eMMC", "客户可能问 SSD、内存、存储颗粒等。"],
    ["P/N", "Part Number，完整型号", "客户问货第一步确认 P/N。"],
    ["QTY", "Quantity，数量", "报价前必须确认数量。"],
    ["DC", "Date Code，生产年份/周期", "现货贸易很关注 DC，新旧年份影响价格。"],
    ["TP", "Target Price，目标价", "客户嫌贵时要问 TP。"],
    ["Lead Time", "交期", "交期太久可能客户不要，不能乱承诺。"],
    ["MOQ/SPQ", "最小起订量/标准包装数量", "报价时要知道是否整包、整盘、整箱。"],
    ["Original/New", "原装/全新", "不能把翻新、拆机、散新说成原装。"],
    ["PO/PI", "采购订单/形式发票", "客户确认后进入订单流程。"],
    ["EMS/OEM/ODM", "电子制造服务商/代工/设计制造", "外贸客户常见类型。"],
], [25 * mm, 55 * mm, 93 * mm]))

story.append(h2("4.2 外贸销售完整流程"))
for item in [
    "1. 明确产品方向：公司主做国外品牌主控 IC、电子元器件、代理/分销产品。",
    "2. 找客户：Google、LinkedIn、Facebook、行业网站、展会名单、B2B 平台、海关数据、老客户转介绍。",
    "3. 建客户表：公司名、国家、官网、联系人、职位、邮箱、WhatsApp/LinkedIn、主营产品、潜在需求、最后跟进时间。",
    "4. 第一次触达：简短介绍公司、主营品牌、优势产品，询问是否有 BOM/RFQ 需求。",
    "5. 收到询盘：确认 P/N、品牌、QTY、DC、目标价、交期、收货地、付款方式、是否接受替代。",
    "6. 查货报价：与采购/供应商确认库存、价格、交期、包装、货源可靠性，再报价给客户。",
    "7. 跟进客户：客户嫌贵就问目标价；客户犹豫就问交期/质量/付款顾虑；客户没回就定期 follow up。",
    "8. 成交订单：客户下 PO，公司出 PI，确认付款、发货、质检、物流。",
    "9. 售后与复购：确认客户收货、使用反馈，沉淀客户偏好和常用型号，持续挖掘需求。",
]:
    story.append(bullet(item))

story.append(h2("4.3 你要重点学习的产品方向"))
for item in [
    "主控 IC：可先理解 MCU、控制器、通信控制芯片、工业控制相关芯片。",
    "国外品牌：TI、ST、NXP、ADI、ON、Infineon、Microchip、Renesas、Samsung、Kioxia、Hynix。",
    "存储类：DRAM、NAND Flash、eMMC、SSD、DDR4/DDR5、服务器内存。",
    "被动件/常规料：电阻、电容、电感、二三极管、MOS、连接器。",
    "客户行业：EMS/OEM/ODM、工控、电源、新能源、通信、消费电子、服务器/存储设备。",
]:
    story.append(bullet(item))

story.append(PageBreak())

story.append(h1("5. 客户开发、RFQ、报价、跟单场景话术"))
story.append(h2("5.1 客户开发方法"))
story.append(para("面试官如果问你怎么开发海外客户，你要说得像一个已经做过预习的人。"))
story.append(quote(
    "我会先根据公司主营品牌和品类确定客户画像，比如 EMS、OEM、ODM、工业控制设备商、PCBA 工厂、电子维修商、海外贸易商。然后通过 Google、LinkedIn、Facebook、公司官网、展会名单和 B2B 平台找公司和联系人，整理到客户表里，再用邮件或 LinkedIn 私信做第一轮触达。触达后持续记录客户反馈、常用型号和下一次跟进时间。"
))

story.append(h2("5.2 客户表字段"))
story.append(table([
    ["字段", "作用"],
    ["Company / Website", "确认客户公司和官网，判断是否真实客户。"],
    ["Country / Region", "判断时差、物流、付款方式和常用沟通工具。"],
    ["Contact / Position", "优先找采购、Buyer、Sourcing、Procurement、Engineer。"],
    ["Email / LinkedIn / WhatsApp", "客户触达和持续跟进渠道。"],
    ["Main Products", "判断客户是否可能用到主控 IC、存储、被动件等。"],
    ["Possible Demand", "记录客户可能采购的品牌、系列或 BOM。"],
    ["Last Contact / Next Step", "防止客户跟丢，形成持续跟进节奏。"],
], [48 * mm, 125 * mm]))

story.append(h2("5.3 RFQ 信息不完整时怎么问"))
story.append(quote(
    "中文：请问这个料方便确认一下完整型号、品牌、数量、DC 要求、是否原装原包、目标价、交期要求和收货地区吗？我确认完整信息后马上帮您查库存和报价。"
))
story.append(quote(
    "English: Thanks for your inquiry. Could you please confirm the full part number, brand, quantity, date code requirement, target price, delivery schedule and destination? I will check the stock and get back to you soon."
))

story.append(h2("5.4 客户嫌贵时怎么回"))
story.append(quote(
    "中文：收到，我再帮您核一下渠道。请问您这边目标价大概是多少？交期和 DC 要求能否放宽？如果目标价明确，我可以再帮您匹配更合适的货源。"
))
story.append(quote(
    "English: Thanks for your feedback. May I know your target price and required delivery date? I will check again with our suppliers and try to find a better solution."
))

story.append(h2("5.5 交期不确定时怎么回"))
story.append(quote(
    "我先不直接承诺交期，需要和供应商确认库存、包装和出货安排。确认后我会把价格、DC、交期和有效期一起反馈给客户，避免后面产生纠纷。"
))

story.append(h2("5.6 客户已读不回怎么跟进"))
story.append(quote(
    "English follow-up: Hi, just checking whether you have any update on this RFQ. If the price is not workable, please share your target price and I will try to support. We can also check alternative options if needed."
))

story.append(h1("6. 高频中文问答"))
qa = [
    ("请你做一个自我介绍。",
     "您好，我叫周铠然，本科是数据科学与大数据技术，英语六级。虽然我没有正式的 IC 外贸实习经历，但我有客户沟通和销售相关实践。之前在 AI 产品实习中，我参与过客户需求梳理、产品介绍、Demo 演示和客户反馈跟进；在校期间也做过校园电动车销售和个人接单，通过社群、朋友圈、闲鱼和转介绍触达客户，完成需求确认、报价沟通、交付和售后维护。我现在想往电子元器件外贸销售方向发展，平时也在学习 Google、LinkedIn、Facebook、邮件开发客户，以及 IC 料号、数量、DC、交期、目标价这些询报价基础流程。"),
    ("你没有 IC 外贸经验，为什么觉得能做？",
     "我承认自己没有正式 IC 外贸经验，所以我不会说自己已经很懂行业。但我有销售和客户沟通的底层能力，包括找客户、确认需求、报价沟通、交付跟进和售后维护。IC 外贸对新人来说，前期最重要的是肯学产品、肯主动开发客户、响应快、能持续跟进。我英语六级，英文阅读和邮件沟通基础比较好，也愿意从产品型号、报价流程、客户开发这些基础开始做。"),
    ("你有过销售经验吗？",
     "有过一些销售相关实践，主要是校园电动车销售和个人接单。电动车销售是先对接本地门店了解货源和价格，再通过校园社群、朋友圈、同学转介绍触达客户，沟通预算、续航、使用场景和售后需求后进行推荐、报价、成交和后续跟进。个人接单则是通过闲鱼、朋友圈等渠道获取需求，完成需求确认、报价沟通、交付和售后维护。"),
    ("你为什么想做外贸业务，而不是国内销售？",
     "我英语基础还可以，CET6 已通过，英文阅读和邮件沟通能力比纯国内销售更能发挥出来。外贸业务也更依赖主动开发、信息检索、持续跟进和客户关系沉淀，这些和我的学习能力、数据整理能力、社媒获客兴趣比较匹配。"),
    ("你怎么开发海外客户？",
     "我会先根据公司主营产品和品牌确定客户画像，比如 EMS、OEM、ODM、电子制造商、海外贸易商等。然后通过 Google、LinkedIn、Facebook、公司官网、行业展会名单和 B2B 平台找公司和联系人，建立客户表，再通过邮件或社媒私信进行触达。第一次触达不会硬推产品，而是介绍公司能供应的品牌和优势，询问对方是否有 IC 或电子元器件需求，再持续跟进。"),
    ("客户问一个型号，你怎么处理？",
     "我会先确认完整型号、品牌、数量、DC 要求、是否原装、目标价、交期、收货地区和付款方式。如果信息不完整，先补齐信息，不会直接盲目报价。确认后再去内部系统、采购同事或供应商渠道查货，比较价格、交期和可靠性，再给客户报价。"),
    ("客户说价格太高怎么办？",
     "我会先确认客户目标价和交期要求，同时询问 DC、包装、付款方式是否能放宽。然后再和采购或供应商核价，看是否有更合适渠道。如果确实做不了，我也会如实反馈，避免为了成交乱承诺。"),
    ("你了解这个行业行情吗？",
     "我现在不敢说自己很懂行情，但我知道电子元器件尤其是存储、主控 IC、服务器相关料价格波动很快。近期 AI 服务器需求和存储供应变化会影响 DRAM、NAND、SSD 等产品价格，所以报价必须以当天供应商渠道、库存、DC 和交期为准。"),
    ("你的英语口语怎么样？",
     "我英语六级已通过，英文阅读和邮件沟通能力比较好。口语可以进行基础日常和简单商务沟通，例如自我介绍、确认型号、数量、交期、付款方式等；复杂商务谈判还在提升中。目前也在针对外贸和 IC 销售场景练习英文表达。"),
    ("目前还需要回学校吗？",
     "目前基本不需要长期回学校，课程和毕业事项已经进入收尾阶段，后续如有学校事务也可以提前协调处理。我现在在深圳，可以稳定到岗，不影响正常工作。"),
    ("你能接受底薪 5-6K 吗？",
     "我了解外贸销售一般是底薪加提成。因为我是转入电子元器件外贸方向，前期更看重平台、培训和成长机会。底薪方面我希望在 6K 左右，具体可以结合公司的试用期、提成机制和考核方式沟通。"),
]
for q, a in qa:
    story.append(h2(q))
    story.append(quote(a))

story.append(PageBreak())

story.append(h1("7. 英文面试与邮件话术"))
story.append(h2("7.1 英文自我介绍"))
story.append(quote(
    "Hello, my name is Kairan Zhou. I majored in Data Science and Big Data Technology, and I have passed CET-6.\n\n"
    "I do not have formal working experience in IC foreign trade yet, but I have experience in customer communication, requirement analysis, quotation discussion and follow-up. I am interested in electronic components and foreign trade sales, and I am learning product knowledge, customer development methods and RFQ handling process.\n\n"
    "I am willing to start from the basics, learn fast, and work hard to develop customers and follow orders."
))

story.append(h2("7.2 首封开发信"))
story.append(quote(
    "Subject: Electronic Components Supply Support\n\n"
    "Dear [Name],\n\n"
    "This is Kairan from HCN Technology. We focus on electronic components, including ICs, memory, controllers and passive components. We support customers with sourcing, quotation and delivery follow-up.\n\n"
    "If you have any RFQ or shortage parts, please feel free to send us the part number and quantity. I will check and reply as soon as possible.\n\n"
    "Best regards,\n"
    "Kairan"
))

story.append(h2("7.3 询问信息"))
story.append(quote(
    "Could you please confirm the full part number, brand, quantity, date code requirement, target price, delivery schedule and destination?"
))

story.append(h2("7.4 报价有效期"))
story.append(quote(
    "Please note that the quotation is subject to final stock confirmation. The price is valid for today due to market fluctuation."
))

story.append(h2("7.5 没货或需要替代"))
story.append(quote(
    "Currently we do not have confirmed stock for this part. Would you accept an alternative brand or different date code? I can check other options for you."
))

story.append(h1("8. 薪资、反问、试用期沟通"))
story.append(h2("8.1 薪资谈法"))
story.append(para(
    "不要一开始就说“我要 10-15K 底薪”。岗位页面 10-15K 很可能是综合薪资，HR 已经说底薪 5-6K。建议表达为："
))
story.append(quote(
    "我了解外贸销售是底薪加提成模式。因为我是转入电子元器件外贸方向，前期更看重平台、培训、产品线和客户资源。底薪方面我希望能在 6K 左右，具体可以结合试用期、提成机制、客户资源和考核方式来沟通。"
))

story.append(h2("8.2 必问问题"))
for item in [
    "公司目前主做哪些国外品牌和品类？主控 IC 具体偏 MCU、存储、通信、电源还是其他？",
    "客户主要是 EMS/OEM 工厂，还是海外贸易商更多？",
    "新人入职后有没有产品知识、报价流程、客户开发方式培训？",
    "客户来源是公司分配询盘，还是需要自己通过 Google、LinkedIn、Facebook、邮件开发？",
    "试用期主要考核什么？客户开发数量、询盘数量、报价数量、成交额，还是过程指标？",
    "报价时采购、销售、质检、物流怎么配合？",
    "底薪、提成比例、提成基数、回款周期、提成发放时间是怎样的？",
    "是否有新人保护期或老业务带教？",
]:
    story.append(bullet(item))

story.append(h2("8.3 判断公司是否靠谱"))
story.append(table([
    ["问题", "健康信号", "风险信号"],
    ["培训", "有产品、报价、平台、邮件模板培训", "只说自己摸索，没有人带"],
    ["客户来源", "有平台/老客户/询盘，也鼓励自开发", "完全没有资源，只要求大量冷开发"],
    ["提成", "说明按利润或销售额计算，回款后多久发", "提成规则模糊，随口承诺高薪"],
    ["货源/质检", "有采购、质检、供应商审核流程", "只要成交，不讲品质风险"],
    ["试用期", "过程指标清晰，例如客户数、询盘数、报价数", "只看成交，不给学习周期"],
], [35 * mm, 69 * mm, 69 * mm]))

story.append(h1("9. 面试前 24 小时清单"))
story.append(h2("9.1 必背三段话"))
for item in [
    "自我介绍：本科数据科学 + CET6 + 客户沟通/销售实践 + 想转电子元器件外贸。",
    "无经验解释：没有正式 IC 外贸经验，但有获客、需求、报价、交付、售后底层能力，愿意从基础做起。",
    "RFQ 流程：型号、品牌、数量、DC、原装、目标价、交期、收货地、付款方式，确认后再查货报价。",
]:
    story.append(bullet(item))

story.append(h2("9.2 需要带/准备"))
for item in [
    "纸质简历 2 份，手机里保存 PDF 简历。",
    "提前查路线：罗湖区深华商业大厦 1106，至少提前 15-20 分钟到。",
    "穿着：干净简单，衬衫/POLO/休闲西裤即可，不要太随意。",
    "手机备忘录写好：英文自我介绍、RFQ 话术、反问问题、薪资底线。",
    "准备一个小本子，面试时记录产品线、客户来源、提成规则。",
    "提前把 LinkedIn、Google、Facebook、邮件开发客户的基本逻辑再看一遍。",
]:
    story.append(bullet(item))

story.append(h2("9.3 面试当天态度"))
for item in [
    "不要紧张，也不要一直强调“我没经验”。正确说法是“我没有正式 IC 外贸经验，但我已经了解基础流程，并且愿意从基础做起”。",
    "多使用岗位关键词：外贸客户开发、社媒、邮件、询盘、RFQ、报价、DC、交期、回款、复购。",
    "如果不懂产品问题，别乱答：说“这个我目前了解还不深，但我会按型号、品牌、封装、DC、应用场景去查资料和向同事确认”。",
    "突出你愿意做主动开发，而不是只想等客户。外贸业务员最怕新人不愿意找客户。",
]:
    story.append(bullet(item))

story.append(h1("10. 入职后 30/60/90 天计划"))
story.append(table([
    ["阶段", "目标", "具体动作"],
    ["前 30 天", "熟悉产品和流程", "学习主控 IC、存储、常见品牌；熟悉报价、PI、PO、交期、回款流程；整理 100 家潜在客户。"],
    ["31-60 天", "开始稳定开发客户", "每天通过 Google/LinkedIn/Facebook/邮件触达客户；建立客户表；跟进 RFQ；复盘邮件回复率。"],
    ["61-90 天", "形成自己的客户池", "沉淀重点客户，追踪常用型号和需求；提升报价速度；争取小单成交或形成稳定询盘。"],
], [30 * mm, 48 * mm, 95 * mm]))

story.append(h1("11. 可直接背诵的结束陈述"))
story.append(quote(
    "我知道自己不是有多年经验的候选人，但我这次不是随便投递。我已经了解这个岗位需要主动开发海外客户、快速响应询盘、确认型号数量 DC 交期、跟进报价和订单。我有客户沟通、销售实践和英文基础，也愿意接受从基础开始学习。只要公司有清晰的产品和流程培训，我会尽快把客户开发、报价跟进和订单流程跑起来。"
))

story.append(h1("12. 资料来源与面试前再确认"))
for item in [
    "岗位截图：BOSS 直聘“汉南电子 · 电子元器件外贸业务员”。",
    "个人简历：周铠然+13692871429+IC销售岗.pdf。",
    "行业朋友建议：可去面、底薪可谈 6000、重点突出看好行业和主动学习，不要害怕没有经验。",
    "行情参考：TrendForce 2026-03-31 关于 2026 年二季度 DRAM/NAND 合约价上行的市场调查。链接：https://www.trendforce.com/presscenter/news/20260331-12995.html",
    "行情参考：TrendForce 2026-03-04 Memory Spot Price Update。链接：https://www.trendforce.com/news/2026/03/04/insights-memory-spot-price-update-dram-spots-top-contracts/",
]:
    story.append(bullet(item))

story.append(quote(
    "面试前最后提醒：行情只说“我有关注、价格波动快、报价以当天渠道为准”，不要装专家；经验只说“我有销售和客户沟通底层能力”，不要硬说自己做过 IC 外贸。"
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
doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
print(OUTPUT)
