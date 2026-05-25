import fs from "node:fs/promises";
import path from "node:path";

const BASE_URL = "https://www.zhipin.com";
const CITY_CODE = "101280600";
const DEFAULT_OUTPUT_DIR = "C:\\Users\\96259\\Desktop\\AIcoding\\贸易";
const DEFAULT_QUERIES = ["IC销售", "IC采购"];

const cdpUrl = process.argv[2] || "http://127.0.0.1:9222";
const outputDir = process.argv[3] || DEFAULT_OUTPUT_DIR;
const queries = process.argv.slice(4).length ? process.argv.slice(4) : DEFAULT_QUERIES;
const listOnly = process.env.BOSS_LIST_ONLY === "1";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function cleanText(value) {
  if (value == null) return "";
  if (Array.isArray(value)) return value.map(cleanText).filter(Boolean).join(" | ");
  return String(value)
    .replace(/\u00a0/g, " ")
    .replace(/[ \t\r\f\v]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function firstPresent(data, keys) {
  for (const key of keys) {
    if (
      Object.prototype.hasOwnProperty.call(data, key) &&
      data[key] !== null &&
      data[key] !== "" &&
      !(Array.isArray(data[key]) && data[key].length === 0)
    ) {
      return data[key];
    }
  }
  return "";
}

function findDeep(obj, keyNames) {
  const queue = [obj];
  const seen = new Set();
  while (queue.length) {
    const item = queue.shift();
    if (!item || typeof item !== "object" || seen.has(item)) continue;
    seen.add(item);
    for (const key of keyNames) {
      if (Object.prototype.hasOwnProperty.call(item, key) && item[key] !== null && item[key] !== "") {
        return item[key];
      }
    }
    for (const value of Object.values(item)) {
      if (value && typeof value === "object") queue.push(value);
    }
  }
  return "";
}

function normalizeListJob(raw, pageNo, query) {
  const jobId = firstPresent(raw, ["encryptJobId", "jobId", "securityJobId"]);
  const securityId = firstPresent(raw, ["securityId"]);
  const lid = firstPresent(raw, ["lid"]);
  const params = new URLSearchParams();
  if (lid) params.set("lid", lid);
  if (securityId) params.set("securityId", securityId);

  return {
    query,
    job_id: cleanText(jobId),
    security_id: cleanText(securityId),
    lid: cleanText(lid),
    job_name: cleanText(firstPresent(raw, ["jobName", "name", "title"])),
    salary: cleanText(firstPresent(raw, ["salaryDesc", "salary", "salaryName"])),
    city: cleanText(firstPresent(raw, ["cityName", "city"])),
    district: cleanText(firstPresent(raw, ["areaDistrict", "districtName", "area"])),
    business_district: cleanText(firstPresent(raw, ["businessDistrict", "businessDistrictName"])),
    experience: cleanText(firstPresent(raw, ["jobExperience", "experienceName", "experience"])),
    degree: cleanText(firstPresent(raw, ["jobDegree", "degreeName", "degree"])),
    company: cleanText(firstPresent(raw, ["brandName", "companyName"])),
    industry: cleanText(firstPresent(raw, ["brandIndustry", "industryName", "industry"])),
    company_scale: cleanText(firstPresent(raw, ["brandScaleName", "scaleName", "scale"])),
    financing_stage: cleanText(firstPresent(raw, ["brandStageName", "stageName", "stage"])),
    boss_name: cleanText(firstPresent(raw, ["bossName", "encryptBossName"])),
    boss_title: cleanText(firstPresent(raw, ["bossTitle", "bossPosition"])),
    tags: cleanText(firstPresent(raw, ["jobLabels", "labels", "tagList"])),
    skills: cleanText(firstPresent(raw, ["skills", "skillLabels"])),
    welfare: cleanText(firstPresent(raw, ["welfareList", "welfare"])),
    source_page: String(pageNo),
    source: "BOSS直聘",
    detail_url: jobId ? `${BASE_URL}/job_detail/${jobId}.html${params.toString() ? `?${params}` : ""}` : "",
    description: "",
    address: "",
    detail_status: "",
  };
}

function extractJobs(data) {
  const zp = data.zpData || data.data || {};
  const jobs = zp.jobList || zp.jobs || zp.list || data.jobList || data.list || [];
  const hasMore = zp.hasMore ?? zp.hasNextPage ?? zp.hasNext ?? zp.has_more;
  const total = zp.totalCount ?? zp.total ?? zp.count;
  return {
    jobs: Array.isArray(jobs) ? jobs : [],
    hasMore:
      typeof hasMore === "boolean"
        ? hasMore
        : hasMore == null
          ? null
          : String(hasMore).toLowerCase() === "true" || String(hasMore) === "1",
    total: Number.isFinite(Number(total)) ? Number(total) : null,
  };
}

function collectDetail(detail) {
  const zp = detail.zpData || detail.data || detail;
  return {
    description: cleanText(findDeep(zp, ["jobDesc", "jobDescription", "description", "postDescription", "desc"])),
    address: cleanText(findDeep(zp, ["address", "jobAddress", "locationAddress", "addressDesc", "workAddress"])),
    welfare: cleanText(findDeep(zp, ["welfareList", "welfare", "showSkills"])),
    tags: cleanText(findDeep(zp, ["jobLabels", "labels", "skillLabels", "skills"])),
    boss_name: cleanText(findDeep(zp, ["bossName", "name"])),
    boss_title: cleanText(findDeep(zp, ["bossTitle", "bossPosition", "title"])),
    company: cleanText(findDeep(zp, ["brandName", "companyName"])),
  };
}

function searchPageUrl(query) {
  const params = new URLSearchParams({
    query,
    city: CITY_CODE,
    industry: "",
    position: "",
  });
  return `${BASE_URL}/web/geek/jobs?${params}`;
}

function jobListUrl(query, pageNo, pageSize) {
  const params = new URLSearchParams({
    scene: "1",
    query,
    city: CITY_CODE,
    experience: "",
    payType: "",
    partTime: "",
    degree: "",
    industry: "",
    scale: "",
    stage: "",
    position: "",
    jobType: "",
    salary: "",
    multiBusinessDistrict: "",
    multiSubway: "",
    page: String(pageNo),
    pageSize: String(pageSize),
  });
  return `${BASE_URL}/wapi/zpgeek/search/joblist.json?${params}`;
}

function detailUrl(job) {
  const params = new URLSearchParams();
  if (job.security_id) params.set("securityId", job.security_id);
  if (job.job_id) params.set("jobId", job.job_id);
  if (job.lid) params.set("lid", job.lid);
  return `${BASE_URL}/wapi/zpgeek/job/detail.json?${params}`;
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText} for ${url}`);
  return response.json();
}

class CdpPage {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.nextId = 1;
    this.pending = new Map();
  }

  async connect() {
    this.ws = new WebSocket(this.wsUrl);
    this.ws.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (!message.id || !this.pending.has(message.id)) return;
      const { resolve, reject } = this.pending.get(message.id);
      this.pending.delete(message.id);
      if (message.error) reject(new Error(JSON.stringify(message.error)));
      else resolve(message.result);
    });
    await new Promise((resolve, reject) => {
      this.ws.addEventListener("open", resolve, { once: true });
      this.ws.addEventListener("error", reject, { once: true });
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error(`CDP timeout: ${method}`));
        }
      }, 60000);
    });
  }

  async eval(expression) {
    const result = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise: true,
      returnByValue: true,
      userGesture: true,
    });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  }

  close() {
    this.ws?.close();
  }
}

async function getOrCreatePage() {
  const pages = await getJson(`${cdpUrl}/json`);
  let page = pages.find((item) => item.type === "page" && item.url.includes("zhipin.com") && !item.url.startsWith("chrome://"));
  if (!page) {
    const opened = await fetch(`${cdpUrl}/json/new?${encodeURIComponent(searchPageUrl(queries[0]))}`, { method: "PUT" });
    if (!opened.ok) throw new Error(`cannot create BOSS tab: ${opened.status}`);
    page = await opened.json();
    await sleep(5000);
  }
  return page;
}

async function currentCdp() {
  const page = await getOrCreatePage();
  const cdp = new CdpPage(page.webSocketDebuggerUrl);
  await cdp.connect();
  await cdp.send("Runtime.enable");
  await cdp.send("Page.enable");
  return cdp;
}

async function withFreshPage(fn, retries = 4) {
  let lastError;
  for (let attempt = 1; attempt <= retries; attempt += 1) {
    const cdp = await currentCdp();
    try {
      const result = await fn(cdp);
      cdp.close();
      return result;
    } catch (error) {
      cdp.close();
      lastError = error;
      const text = String(error?.message || error);
      if (!text.includes("navigated") && !text.includes("closed") && !text.includes("CDP timeout")) throw error;
      await sleep(2500 * attempt);
    }
  }
  throw lastError;
}

async function pageFetch(cdp, url) {
  const expression = `
    (async () => {
      const response = await fetch(${JSON.stringify(url)}, {
        credentials: 'include',
        headers: {
          'Accept': 'application/json, text/plain, */*',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });
      const text = await response.text();
      return { status: response.status, url: response.url, text };
    })()
  `;
  const result = await cdp.eval(expression);
  let data;
  try {
    data = JSON.parse(result.text);
  } catch {
    data = { code: -1, message: "non-json", raw: result.text.slice(0, 300) };
  }
  data._http_status = result.status;
  data._response_url = result.url;
  return data;
}

async function verifyLogin() {
  const status = await withFreshPage((cdp) =>
    cdp.eval(`
      (() => {
        const text = document.body ? document.body.innerText : '';
        return {
          url: location.href,
          title: document.title,
          logged: !text.includes('验证码登录') && !text.includes('扫码登录') && (text.includes('消息') || text.includes('简历') || location.href.includes('/web/geek/jobs')),
          text: text.slice(0, 300)
        };
      })()
    `),
  );
  if (!status.logged) {
    throw new Error(`未检测到BOSS登录态：${status.title} ${status.url}`);
  }
}

async function navigateSearch(query) {
  await withFreshPage(async (cdp) => {
    await cdp.send("Page.navigate", { url: searchPageUrl(query) });
    return true;
  });
  await sleep(4500);
}

async function scrapeList(query) {
  console.log(`\n[query] ${query}`);
  await navigateSearch(query);
  const jobs = [];
  const seen = new Set();
  let total = null;

  for (let pageNo = 1; pageNo <= 50; pageNo += 1) {
    let data = null;
    for (let attempt = 1; attempt <= 5; attempt += 1) {
      data = await withFreshPage((cdp) => pageFetch(cdp, jobListUrl(query, pageNo, Number(process.env.BOSS_PAGE_SIZE || "15"))));
      if (data.code === 0 || data.code === "0") break;
      const retryable = String(data.code) === "37" || String(data.message || "").includes("异常");
      console.log(`[list-retry] ${query} page=${pageNo} attempt=${attempt} code=${data.code} message=${data.message || ""}`);
      if (!retryable || attempt === 5) break;
      await navigateSearch(query);
      await sleep(18000 + attempt * 12000 + Math.random() * 9000);
    }
    if (!(data.code === 0 || data.code === "0")) {
      throw new Error(`列表接口失败 query=${query} page=${pageNo} code=${data.code} message=${data.message || ""}`);
    }
    const extracted = extractJobs(data);
    if (extracted.total != null) total = extracted.total;
    console.log(`[list] ${query} page=${pageNo} jobs=${extracted.jobs.length} total=${total ?? ""}`);
    if (!extracted.jobs.length) break;

    for (const raw of extracted.jobs) {
      const job = normalizeListJob(raw, pageNo, query);
      const key = job.job_id || `${job.query}|${job.job_name}|${job.company}|${job.salary}`;
      if (seen.has(key)) continue;
      seen.add(key);
      jobs.push(job);
    }

    if (extracted.hasMore === false) break;
    if (total && jobs.length >= total) break;
    await sleep(6500 + Math.random() * 5500);
  }

  return { jobs, total };
}

async function writePayload(payload, outputPath, latestPath) {
  await fs.writeFile(outputPath, JSON.stringify(payload, null, 2), "utf8");
  await fs.writeFile(latestPath, JSON.stringify(payload, null, 2), "utf8");
}

async function fillDetails(jobs, onProgress = null) {
  for (let i = 0; i < jobs.length; i += 1) {
    const job = jobs[i];
    console.log(`[detail] ${i + 1}/${jobs.length} ${job.query} ${job.job_name} - ${job.company}`);
    for (let attempt = 1; attempt <= 3; attempt += 1) {
      try {
        if (attempt > 1) await sleep(7000 + Math.random() * 5000 + attempt * 2000);
        const data = await withFreshPage((cdp) => pageFetch(cdp, detailUrl(job)));
        if (!(data.code === 0 || data.code === "0")) {
          job.detail_status = `detail api failed: code=${data.code} ${data.message || ""}`;
          if (String(data.code) === "37" || String(data.message || "").includes("异常")) continue;
          break;
        }

        const detail = collectDetail(data);
        if (detail.description) job.description = detail.description;
        if (detail.address) job.address = detail.address;
        if (detail.welfare && !job.welfare) job.welfare = detail.welfare;
        if (detail.tags && !job.tags) job.tags = detail.tags;
        if (detail.boss_name && !job.boss_name) job.boss_name = detail.boss_name;
        if (detail.boss_title && !job.boss_title) job.boss_title = detail.boss_title;
        if (detail.company && !job.company) job.company = detail.company;
        job.detail_status = job.description ? "ok" : "detail api ok, description not found";
        break;
      } catch (error) {
        job.detail_status = `error: ${error.message}`;
      }
    }
    await sleep(1800 + Math.random() * 2200);
    if (onProgress && ((i + 1) % 20 === 0 || i + 1 === jobs.length)) {
      await onProgress(i + 1, jobs.length);
    }
  }
}

function timestamp() {
  const now = new Date();
  return [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
    "_",
    String(now.getHours()).padStart(2, "0"),
    String(now.getMinutes()).padStart(2, "0"),
    String(now.getSeconds()).padStart(2, "0"),
  ].join("");
}

async function main() {
  await verifyLogin();

  await fs.mkdir(outputDir, { recursive: true });
  const stamp = timestamp();
  const safeQueryStem = queries.join("_").replace(/[\\/:*?"<>|]/g, "_").slice(0, 80);
  const stem = `BOSS直聘_${safeQueryStem}_深圳招聘_${stamp}`;
  const outputPath = path.join(outputDir, `${stem}.json`);
  const latestPath = path.join(outputDir, `BOSS直聘_${safeQueryStem}_深圳招聘_latest.json`);
  const startedAt = new Date();
  const queryResults = [];
  const allJobs = [];
  const payload = {
    meta: {
      queries,
      city_code: CITY_CODE,
      source_urls: Object.fromEntries(queries.map((query) => [query, searchPageUrl(query)])),
      query_results: queryResults,
      list_count: 0,
      crawled_at: startedAt.toLocaleString("zh-CN", { hour12: false }),
      detail_progress: "",
    },
    jobs: allJobs,
  };

  for (const query of queries) {
    const result = await scrapeList(query);
    const queryResult = { query, total_count_reported: result.total, list_count: result.jobs.length, detail_done: 0 };
    queryResults.push(queryResult);
    allJobs.push(...result.jobs);
    payload.meta.list_count = allJobs.length;
    payload.meta.detail_progress = `${query} list done`;
    await writePayload(payload, outputPath, latestPath);

    if (listOnly) {
      queryResult.detail_done = 0;
      queryResult.detail_total = result.jobs.length;
      queryResult.description_count = 0;
      payload.meta.detail_progress = `${query} list only`;
      await writePayload(payload, outputPath, latestPath);
      continue;
    }

    await fillDetails(result.jobs, async (done, total) => {
      queryResult.detail_done = done;
      queryResult.detail_total = total;
      queryResult.description_count = result.jobs.filter((job) => job.description).length;
      payload.meta.list_count = allJobs.length;
      payload.meta.detail_progress = `${query} ${done}/${total}`;
      await writePayload(payload, outputPath, latestPath);
    });
    queryResult.description_count = result.jobs.filter((job) => job.description).length;
    queryResult.detail_done = result.jobs.length;
    queryResult.detail_total = result.jobs.length;
    payload.meta.detail_progress = `${query} detail done`;
    await writePayload(payload, outputPath, latestPath);
  }

  payload.meta.list_count = allJobs.length;
  payload.meta.finished_at = new Date().toLocaleString("zh-CN", { hour12: false });
  payload.meta.detail_progress = "done";
  await writePayload(payload, outputPath, latestPath);
  console.log(`\n[done] ${outputPath}`);
  console.log(`[latest] ${latestPath}`);
  console.log(`[summary] jobs=${allJobs.length} desc=${allJobs.filter((job) => job.description).length}`);
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});

