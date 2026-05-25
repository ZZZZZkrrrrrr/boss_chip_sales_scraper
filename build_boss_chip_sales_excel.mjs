import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const inputPath = process.argv[2];
const outputPath = process.argv[3];

if (!inputPath || !outputPath) {
  console.error("Usage: node build_boss_chip_sales_excel.mjs <input.json> <output.xlsx>");
  process.exit(2);
}

function value(value) {
  if (value === undefined || value === null) return "";
  if (Array.isArray(value)) return value.filter(Boolean).join(" | ");
  return String(value);
}

function colName(index) {
  let name = "";
  while (index > 0) {
    const rem = (index - 1) % 26;
    name = String.fromCharCode(65 + rem) + name;
    index = Math.floor((index - 1) / 26);
  }
  return name;
}

const raw = JSON.parse(await fs.readFile(inputPath, "utf8"));
const jobs = Array.isArray(raw.jobs) ? raw.jobs : [];
const meta = raw.meta || {};

const headers = [
  "序号",
  "职位名称",
  "薪资",
  "城市",
  "区域",
  "商圈",
  "经验",
  "学历",
  "公司",
  "行业",
  "公司规模",
  "融资阶段",
  "招聘人",
  "招聘人职位",
  "职位标签",
  "技能/关键词",
  "福利",
  "职位描述",
  "工作地址",
  "详情链接",
  "来源页码",
  "详情状态",
  "抓取时间",
];

const rows = jobs.map((job, index) => [
  index + 1,
  value(job.job_name),
  value(job.salary),
  value(job.city),
  value(job.district),
  value(job.business_district),
  value(job.experience),
  value(job.degree),
  value(job.company),
  value(job.industry),
  value(job.company_scale),
  value(job.financing_stage),
  value(job.boss_name),
  value(job.boss_title),
  value(job.tags),
  value(job.skills),
  value(job.welfare),
  value(job.description),
  value(job.address),
  value(job.detail_url),
  value(job.source_page),
  value(job.detail_status),
  value(meta.crawled_at),
]);

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("职位数据");
const summary = workbook.worksheets.add("抓取说明");
sheet.showGridLines = false;
summary.showGridLines = false;

const lastCol = colName(headers.length);
const dataLastRow = Math.max(rows.length + 1, 2);

sheet.getRange(`A1:${lastCol}1`).values = [headers];
if (rows.length) {
  sheet.getRange(`A2:${lastCol}${rows.length + 1}`).values = rows;
}

const header = sheet.getRange(`A1:${lastCol}1`);
header.format.fill.color = "#0F766E";
header.format.font.color = "#FFFFFF";
header.format.font.bold = true;
header.format.wrapText = true;
header.format.rowHeightPx = 34;

const dataRange = sheet.getRange(`A1:${lastCol}${dataLastRow}`);
dataRange.format.font.name = "Microsoft YaHei";
dataRange.format.font.size = 10;
dataRange.format.wrapText = true;
dataRange.format.verticalAlignment = "Top";

sheet.getRange(`A1:A${dataLastRow}`).format.columnWidthPx = 58;
sheet.getRange(`B1:B${dataLastRow}`).format.columnWidthPx = 230;
sheet.getRange(`C1:C${dataLastRow}`).format.columnWidthPx = 88;
sheet.getRange(`D1:H${dataLastRow}`).format.columnWidthPx = 78;
sheet.getRange(`I1:I${dataLastRow}`).format.columnWidthPx = 180;
sheet.getRange(`J1:N${dataLastRow}`).format.columnWidthPx = 110;
sheet.getRange(`O1:Q${dataLastRow}`).format.columnWidthPx = 190;
sheet.getRange(`R1:R${dataLastRow}`).format.columnWidthPx = 420;
sheet.getRange(`S1:S${dataLastRow}`).format.columnWidthPx = 260;
sheet.getRange(`T1:T${dataLastRow}`).format.columnWidthPx = 320;
sheet.getRange(`U1:W${dataLastRow}`).format.columnWidthPx = 90;
if (rows.length) {
  sheet.getRange(`A2:${lastCol}${rows.length + 1}`).format.rowHeightPx = 86;
}
sheet.freezePanes.freezeRows(1);

if (rows.length) {
  const table = sheet.tables.add(`A1:${lastCol}${rows.length + 1}`, true, "BossChipSalesJobs");
  table.style = "TableStyleMedium4";
  table.showFilterButton = true;
}

summary.getRange("A1:B9").values = [
  ["项目", "内容"],
  ["搜索关键词", value(meta.query)],
  ["城市编码", value(meta.city_code)],
  ["来源链接", value(meta.source_url)],
  ["列表返回总数", value(meta.total_count_reported)],
  ["去重职位数", String(jobs.length)],
  ["抓取时间", value(meta.crawled_at)],
  ["JSON源文件", path.resolve(inputPath)],
  ["说明", "数据来自 BOSS直聘搜索页和详情页，详情页受登录状态和站点访问限制影响。"],
];
summary.getRange("A1:B1").format.fill.color = "#0F766E";
summary.getRange("A1:B1").format.font.color = "#FFFFFF";
summary.getRange("A1:B1").format.font.bold = true;
summary.getRange("A1:B9").format.font.name = "Microsoft YaHei";
summary.getRange("A1:B9").format.font.size = 10;
summary.getRange("A1:B9").format.wrapText = true;
summary.getRange("A1:A9").format.columnWidthPx = 120;
summary.getRange("B1:B9").format.columnWidthPx = 620;
summary.freezePanes.freezeRows(1);

const inspect = await workbook.inspect({
  kind: "table",
  range: `职位数据!A1:${lastCol}${Math.min(dataLastRow, 8)}`,
  include: "values",
  tableMaxRows: 8,
  tableMaxCols: 8,
  tableMaxCellChars: 80,
});
console.log(inspect.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "formula error scan",
});
console.log(errors.ndjson);

await workbook.render({ sheetName: "职位数据", range: `A1:${lastCol}${Math.min(dataLastRow, 12)}`, scale: 1, format: "png" });
await workbook.render({ sheetName: "抓取说明", range: "A1:B9", scale: 1, format: "png" });

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
