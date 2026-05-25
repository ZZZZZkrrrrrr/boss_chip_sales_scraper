import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const inputPath = process.argv[2];
const outputPath = process.argv[3];

if (!inputPath || !outputPath) {
  console.error("Usage: node build_boss_ic_jobs_excel.mjs <input.json> <output.xlsx>");
  process.exit(2);
}

function value(input) {
  if (input === undefined || input === null) return "";
  if (Array.isArray(input)) return input.filter(Boolean).join(" | ");
  return String(input);
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

function sheetNameFor(query, fallback) {
  return String(query || fallback).replace(/[\\/*?:[\]]/g, "").slice(0, 31) || fallback;
}

const raw = JSON.parse(await fs.readFile(inputPath, "utf8"));
const jobs = Array.isArray(raw.jobs) ? raw.jobs : [];
const meta = raw.meta || {};

const headers = [
  "序号",
  "搜索关键词",
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

function rowsFor(items) {
  return items.map((job, index) => [
    index + 1,
    value(job.query),
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
    value(meta.nav_detail_updated_at || meta.crawled_at),
  ]);
}

function buildDataSheet(workbook, sheetName, items, tableName) {
  const sheet = workbook.worksheets.add(sheetName);
  sheet.showGridLines = false;

  const rows = rowsFor(items);
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
  sheet.getRange(`B1:B${dataLastRow}`).format.columnWidthPx = 90;
  sheet.getRange(`C1:C${dataLastRow}`).format.columnWidthPx = 230;
  sheet.getRange(`D1:D${dataLastRow}`).format.columnWidthPx = 92;
  sheet.getRange(`E1:I${dataLastRow}`).format.columnWidthPx = 78;
  sheet.getRange(`J1:J${dataLastRow}`).format.columnWidthPx = 180;
  sheet.getRange(`K1:O${dataLastRow}`).format.columnWidthPx = 110;
  sheet.getRange(`P1:R${dataLastRow}`).format.columnWidthPx = 190;
  sheet.getRange(`S1:S${dataLastRow}`).format.columnWidthPx = 430;
  sheet.getRange(`T1:T${dataLastRow}`).format.columnWidthPx = 260;
  sheet.getRange(`U1:U${dataLastRow}`).format.columnWidthPx = 320;
  sheet.getRange(`V1:X${dataLastRow}`).format.columnWidthPx = 90;
  if (rows.length) {
    sheet.getRange(`A2:${lastCol}${rows.length + 1}`).format.rowHeightPx = 86;
  }

  sheet.freezePanes.freezeRows(1);

  if (rows.length) {
    const table = sheet.tables.add(`A1:${lastCol}${rows.length + 1}`, true, tableName);
    table.style = "TableStyleMedium4";
    table.showFilterButton = true;
  }

  return sheet;
}

const workbook = Workbook.create();
buildDataSheet(workbook, "全部职位", jobs, "AllIcJobs");

const queries = Array.isArray(meta.queries) && meta.queries.length
  ? meta.queries
  : [...new Set(jobs.map((job) => job.query).filter(Boolean))];

let tableIndex = 1;
for (const query of queries) {
  const safeSheetName = sheetNameFor(query, `关键词${tableIndex}`);
  buildDataSheet(workbook, safeSheetName, jobs.filter((job) => job.query === query), `QueryJobs${tableIndex}`);
  tableIndex += 1;
}

const summary = workbook.worksheets.add("抓取说明");
summary.showGridLines = false;

const queryRows = Array.isArray(meta.query_results)
  ? meta.query_results
      .map((item) => `${item.query}: 列表${item.list_count ?? ""}条 / 平台返回总数${item.total_count_reported ?? ""}`)
      .join("\n")
  : "";

summary.getRange("A1:B13").values = [
  ["项目", "内容"],
  ["搜索关键词", value(queries)],
  ["城市编码", value(meta.city_code)],
  ["关键词统计", queryRows],
  ["职位总数", String(jobs.length)],
  ["职位描述非空数", String(jobs.filter((job) => job.description).length)],
  ["工作地址非空数", String(jobs.filter((job) => job.address).length)],
  ["详情状态 ok 数", String(jobs.filter((job) => job.detail_status === "ok").length)],
  ["列表抓取时间", value(meta.crawled_at)],
  ["详情补齐时间", value(meta.nav_detail_updated_at)],
  ["JSON源文件", path.resolve(inputPath)],
  ["说明", "数据来自 BOSS 直聘搜索页和职位详情页；不同关键词可能存在重复岗位，全部职位表按抓取结果保留关键词来源。"],
  ["来源链接", value(meta.source_urls ? Object.entries(meta.source_urls).map(([query, url]) => `${query}: ${url}`).join("\n") : "")],
];
summary.getRange("A1:B1").format.fill.color = "#0F766E";
summary.getRange("A1:B1").format.font.color = "#FFFFFF";
summary.getRange("A1:B1").format.font.bold = true;
summary.getRange("A1:B13").format.font.name = "Microsoft YaHei";
summary.getRange("A1:B13").format.font.size = 10;
summary.getRange("A1:B13").format.wrapText = true;
summary.getRange("A1:A13").format.columnWidthPx = 125;
summary.getRange("B1:B13").format.columnWidthPx = 760;
summary.freezePanes.freezeRows(1);

const lastCol = colName(headers.length);
const previewRows = Math.min(Math.max(jobs.length + 1, 2), 8);
const inspect = await workbook.inspect({
  kind: "table",
  range: `全部职位!A1:${lastCol}${previewRows}`,
  include: "values",
  tableMaxRows: 8,
  tableMaxCols: 9,
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

await workbook.render({ sheetName: "全部职位", range: `A1:${lastCol}${Math.min(Math.max(jobs.length + 1, 2), 12)}`, scale: 1, format: "png" });
for (const query of queries) {
  const safeSheetName = sheetNameFor(query, "关键词");
  const itemCount = jobs.filter((job) => job.query === query).length;
  await workbook.render({ sheetName: safeSheetName, range: `A1:${lastCol}${Math.min(Math.max(itemCount + 1, 2), 12)}`, scale: 1, format: "png" });
}
await workbook.render({ sheetName: "抓取说明", range: "A1:B13", scale: 1, format: "png" });

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
