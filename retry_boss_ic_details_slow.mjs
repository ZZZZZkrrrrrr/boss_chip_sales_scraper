import fs from "node:fs/promises";
import path from "node:path";

const BASE_URL = "https://www.zhipin.com";
const cdpUrl = process.argv[2] || "http://127.0.0.1:9222";
const inputPath = process.argv[3] || "C:\\Users\\96259\\Desktop\\AIcoding\\贸易\\BOSS直聘_IC销售_IC采购_深圳招聘_latest.json";
const limit = Number.parseInt(process.env.BOSS_DETAIL_LIMIT || "0", 10);

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

function findDeep(obj, keyNames) {
  const queue = [obj];
  const seen = new Set();
  while (queue.length) {
    const item = queue.shift();
    if (!item || typeof item !== "object" || seen.has(item)) continue;
    seen.add(item);
    for (const key of keyNames) {
      if (Object.prototype.hasOwnProperty.call(item, key) && item[key] !== null && item[key] !== "") return item[key];
    }
    for (const value of Object.values(item)) {
      if (value && typeof value === "object") queue.push(value);
    }
  }
  return "";
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

function detailApiUrl(job) {
  const params = new URLSearchParams();
  if (job.security_id) params.set("securityId", job.security_id);
  if (job.job_id) params.set("jobId", job.job_id);
  if (job.lid) params.set("lid", job.lid);
  return `${BASE_URL}/wapi/zpgeek/job/detail.json?${params}`;
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
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

async function currentCdp() {
  const pages = await getJson(`${cdpUrl}/json`);
  const page = pages.find((item) => item.type === "page" && item.url.includes("zhipin.com") && !item.url.startsWith("chrome://"));
  if (!page) throw new Error("没有找到 BOSS 直聘页面，请保持登录后的 Chrome 窗口打开。");
  const cdp = new CdpPage(page.webSocketDebuggerUrl);
  await cdp.connect();
  await cdp.send("Runtime.enable");
  return cdp;
}

async function withFreshPage(fn, retries = 3) {
  let lastError;
  for (let i = 1; i <= retries; i += 1) {
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
      await sleep(5000 * i);
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
  try {
    const data = JSON.parse(result.text);
    data._http_status = result.status;
    data._response_url = result.url;
    return data;
  } catch {
    return { code: -1, message: "non-json", raw: result.text.slice(0, 300), _http_status: result.status };
  }
}

async function save(payload, latestPath) {
  payload.meta.detail_retry_updated_at = new Date().toLocaleString("zh-CN", { hour12: false });
  await fs.writeFile(inputPath, JSON.stringify(payload, null, 2), "utf8");
  await fs.writeFile(latestPath, JSON.stringify(payload, null, 2), "utf8");
}

const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
payload.meta ||= {};
const jobs = Array.isArray(payload.jobs) ? payload.jobs : [];
const latestPath = path.join(path.dirname(inputPath), "BOSS直聘_IC销售_IC采购_深圳招聘_latest.json");

const detailByKey = new Map();
for (const job of jobs) {
  if (job.description) {
    const key = job.job_id || job.detail_url;
    if (key) detailByKey.set(key, job);
  }
}
for (const job of jobs) {
  const key = job.job_id || job.detail_url;
  const found = key ? detailByKey.get(key) : null;
  if (found && !job.description) {
    job.description = found.description || "";
    job.address = job.address || found.address || "";
    job.welfare = job.welfare || found.welfare || "";
    job.tags = job.tags || found.tags || "";
    job.boss_name = job.boss_name || found.boss_name || "";
    job.boss_title = job.boss_title || found.boss_title || "";
    job.detail_status = "copied from duplicate";
  }
}

let missing = jobs.filter((job) => !job.description);
if (limit > 0) missing = missing.slice(0, limit);

console.log(`jobs=${jobs.length} missing=${jobs.filter((job) => !job.description).length} run=${missing.length}`);
let consecutiveSecurity = 0;

for (let i = 0; i < missing.length; i += 1) {
  const job = missing[i];
  const key = job.job_id || job.detail_url;
  const copied = key ? detailByKey.get(key) : null;
  if (copied?.description) {
    job.description = copied.description;
    job.address = job.address || copied.address || "";
    job.detail_status = "copied from duplicate";
    await save(payload, latestPath);
    continue;
  }

  console.log(`[detail-retry] ${i + 1}/${missing.length} ${job.query} ${job.job_name} - ${job.company}`);
  let success = false;

  for (let attempt = 1; attempt <= 4; attempt += 1) {
    const waitMs = 18000 + Math.random() * 17000 + attempt * 6000 + consecutiveSecurity * 4000;
    await sleep(waitMs);
    try {
      const data = await withFreshPage((cdp) => pageFetch(cdp, detailApiUrl(job)));
      if (!(data.code === 0 || data.code === "0")) {
        job.detail_status = `detail api failed: code=${data.code} ${data.message || ""}`;
        console.log(`  attempt=${attempt} ${job.detail_status}`);
        if (String(data.code) === "37" || String(data.message || "").includes("异常")) {
          consecutiveSecurity += 1;
          if (consecutiveSecurity >= 5) {
            const coolMs = 240000 + Math.random() * 120000;
            console.log(`  security cooldown ${Math.round(coolMs / 1000)}s`);
            await save(payload, latestPath);
            await sleep(coolMs);
            consecutiveSecurity = 0;
          }
          continue;
        }
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
      console.log(`  attempt=${attempt} ${job.detail_status}`);
      success = Boolean(job.description);
      if (success && key) detailByKey.set(key, job);
      consecutiveSecurity = 0;
      break;
    } catch (error) {
      job.detail_status = `error: ${error.message}`;
      console.log(`  attempt=${attempt} ${job.detail_status}`);
    }
  }

  payload.meta.detail_retry_progress = `${i + 1}/${missing.length}`;
  payload.meta.detail_retry_success_count = jobs.filter((item) => item.description).length;
  payload.meta.detail_retry_address_count = jobs.filter((item) => item.address).length;
  await save(payload, latestPath);
}

console.log(`done desc=${jobs.filter((job) => job.description).length}/${jobs.length} addr=${jobs.filter((job) => job.address).length}/${jobs.length}`);
