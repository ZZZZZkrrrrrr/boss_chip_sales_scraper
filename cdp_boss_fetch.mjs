import fs from "node:fs/promises";
import path from "node:path";

const BASE_URL = "https://www.zhipin.com";
const SEARCH_URL = "https://www.zhipin.com/web/geek/jobs?query=%E8%8A%AF%E7%89%87%E9%94%80%E5%94%AE&city=101280600&industry=&position=";

const cdpUrl = process.argv[2] || "http://127.0.0.1:9222";
const outputDir = process.argv[3] || "C:\\Users\\96259\\Desktop\\AIcoding\\贸易";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function cleanText(value) {
  if (value == null) return "";
  if (Array.isArray(value)) return value.map(cleanText).filter(Boolean).join(" | ");
  return String(value).replace(/\u00a0/g, " ").replace(/[ \t\r\f\v]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}

function firstPresent(data, keys) {
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(data, key) && data[key] !== null && data[key] !== "" && !(Array.isArray(data[key]) && data[key].length === 0)) {
      return data[key];
    }
  }
  return "";
}

function normalizeListJob(raw, pageNo) {
  const jobId = firstPresent(raw, ["encryptJobId", "jobId", "securityJobId"]);
  const securityId = firstPresent(raw, ["securityId"]);
  const lid = firstPresent(raw, ["lid"]);
  const params = new URLSearchParams();
  if (lid) params.set("lid", lid);
  if (securityId) params.set("securityId", securityId);
  return {
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
    hasMore: typeof hasMore === "boolean" ? hasMore : hasMore == null ? null : String(hasMore).toLowerCase() === "true" || String(hasMore) === "1",
    total: Number.isFinite(Number(total)) ? Number(total) : null,
  };
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

function collectDetail(detail) {
  const zp = detail.zpData || detail.data || detail;
  const description = findDeep(zp, ["jobDesc", "jobDescription", "description", "postDescription", "desc"]);
  const address = findDeep(zp, ["address", "jobAddress", "locationAddress", "addressDesc", "workAddress"]);
  const welfare = findDeep(zp, ["welfareList", "welfare", "showSkills"]);
  const tags = findDeep(zp, ["jobLabels", "labels", "skillLabels", "skills"]);
  const bossName = findDeep(zp, ["bossName", "name"]);
  const bossTitle = findDeep(zp, ["bossTitle", "bossPosition", "title"]);
  const company = findDeep(zp, ["brandName", "companyName"]);
  return {
    description: cleanText(description),
    address: cleanText(address),
    welfare: cleanText(welfare),
    tags: cleanText(tags),
    boss_name: cleanText(bossName),
    boss_title: cleanText(bossTitle),
    company: cleanText(company),
  };
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
      if (message.id && this.pending.has(message.id)) {
        const { resolve, reject } = this.pending.get(message.id);
        this.pending.delete(message.id);
        if (message.error) reject(new Error(JSON.stringify(message.error)));
        else resolve(message.result);
      }
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

  async eval(expression, awaitPromise = true) {
    const result = await this.send("Runtime.evaluate", {
      expression,
      awaitPromise,
      returnByValue: true,
      userGesture: true,
    });
    if (result.exceptionDetails) {
      throw new Error(JSON.stringify(result.exceptionDetails));
    }
    return result.result.value;
  }

  close() {
    this.ws?.close();
  }
}

async function connectCurrentPage() {
  const pageInfo = await getOrCreatePage();
  const cdp = new CdpPage(pageInfo.webSocketDebuggerUrl);
  await cdp.connect();
  await cdp.send("Runtime.enable");
  await cdp.send("Page.enable");
  return cdp;
}

async function withFreshPage(fn, retries = 4) {
  let lastError;
  for (let attempt = 1; attempt <= retries; attempt += 1) {
    const cdp = await connectCurrentPage();
    try {
      const result = await fn(cdp);
      cdp.close();
      return result;
    } catch (error) {
      cdp.close();
      lastError = error;
      const text = String(error?.message || error);
      if (!text.includes("navigated") && !text.includes("closed") && !text.includes("CDP timeout")) {
        throw error;
      }
      await sleep(2500 * attempt);
    }
  }
  throw lastError;
}

async function getOrCreatePage() {
  let pages = await getJson(`${cdpUrl}/json`);
  let page = pages.find((item) => item.type === "page" && item.url.includes("zhipin.com") && !item.url.startsWith("chrome://"));
  if (!page) {
    const opened = await fetch(`${cdpUrl}/json/new?${encodeURIComponent(SEARCH_URL)}`, { method: "PUT" });
    if (!opened.ok) throw new Error(`cannot create tab: ${opened.status}`);
    page = await opened.json();
    await sleep(5000);
  }
  return page;
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
  const result = await cdp.eval(expression, true);
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

function jobListUrl(pageNo, pageSize) {
  const params = new URLSearchParams({
    scene: "1",
    query: "芯片销售",
    city: "101280600",
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

async function main() {
  const loginText = await withFreshPage((cdp) => cdp.eval(`
      (() => {
        const text = document.body ? document.body.innerText : '';
        return {
          url: location.href,
          title: document.title,
          logged: text.includes('消息') && text.includes('简历') && !text.includes('验证码登录'),
          text: text.slice(0, 300)
        };
      })()
    `));
  if (!loginText.logged) {
    throw new Error(`未检测到登录态。当前页面：${loginText.title} ${loginText.url}`);
  }

  const jobs = [];
  const seen = new Set();
  let total = null;
  for (let pageNo = 1; pageNo <= 50; pageNo += 1) {
      const data = await withFreshPage((cdp) => pageFetch(cdp, jobListUrl(pageNo, 30)));
      if (!(data.code === 0 || data.code === "0")) {
        throw new Error(`列表接口失败 code=${data.code} message=${data.message || ""}`);
      }
      const extracted = extractJobs(data);
      if (extracted.total != null) total = extracted.total;
      console.log(`[列表] 第 ${pageNo} 页 ${extracted.jobs.length} 条`);
      if (!extracted.jobs.length) break;
      for (const raw of extracted.jobs) {
        const job = normalizeListJob(raw, pageNo);
        const key = job.job_id || `${job.job_name}|${job.company}|${job.salary}`;
        if (seen.has(key)) continue;
        seen.add(key);
        jobs.push(job);
      }
      if (extracted.hasMore === false) break;
      if (total && jobs.length >= total) break;
      await sleep(1200 + Math.random() * 1000);
  }

  for (let i = 0; i < jobs.length; i += 1) {
    const job = jobs[i];
    console.log(`[详情] ${i + 1}/${jobs.length} ${job.job_name} - ${job.company}`);
    try {
        const data = await withFreshPage((cdp) => pageFetch(cdp, detailUrl(job)));
        if (!(data.code === 0 || data.code === "0")) {
          job.detail_status = `detail api failed: code=${data.code} ${data.message || ""}`;
          continue;
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
      } catch (error) {
        job.detail_status = `error: ${error.message}`;
      }
      await sleep(1500 + Math.random() * 1800);
  }

  const now = new Date();
  const stamp = [
      now.getFullYear(),
      String(now.getMonth() + 1).padStart(2, "0"),
      String(now.getDate()).padStart(2, "0"),
      "_",
      String(now.getHours()).padStart(2, "0"),
      String(now.getMinutes()).padStart(2, "0"),
      String(now.getSeconds()).padStart(2, "0"),
  ].join("");
  const payload = {
    meta: {
      query: "芯片销售",
      city_code: "101280600",
      source_url: SEARCH_URL,
      total_count_reported: total,
      list_count: jobs.length,
      crawled_at: now.toLocaleString("zh-CN", { hour12: false }),
    },
    jobs,
  };
  await fs.mkdir(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, `BOSS直聘_芯片销售_深圳招聘_${stamp}.json`);
  await fs.writeFile(outputPath, JSON.stringify(payload, null, 2), "utf8");
  await fs.writeFile(path.join(outputDir, "BOSS直聘_芯片销售_深圳招聘_latest.json"), JSON.stringify(payload, null, 2), "utf8");
  console.log(outputPath);
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
