import fs from "node:fs/promises";

const cdpUrl = process.argv[2] || "http://127.0.0.1:9222";
const inputPath = process.argv[3];
const batchSize = Number.parseInt(process.env.BOSS_FAST_BATCH_SIZE || "4", 10);
const force = process.env.BOSS_FORCE_DETAILS === "1";

if (!inputPath) {
  console.error("Usage: node scrape_boss_details_fast_cdp.mjs <cdpUrl> <inputJson>");
  process.exit(1);
}

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
  const jobInfo = zp.jobInfo || {};
  const brandInfo = zp.brandInfo || {};
  return {
    description: cleanText(
      jobInfo.postDescription ||
        jobInfo.jobDesc ||
        findDeep(zp, ["postDescription", "jobDesc", "jobDescription", "description", "desc"]),
    ),
    address: cleanText(
      jobInfo.address ||
        jobInfo.locationAddress ||
        jobInfo.addressDesc ||
        findDeep(zp, ["address", "jobAddress", "locationAddress", "addressDesc", "workAddress"]),
    ),
    welfare: cleanText(findDeep(zp, ["welfareList", "welfare", "showSkills"])),
    tags: cleanText(findDeep(zp, ["jobLabels", "labels", "skillLabels", "skills"])),
    boss_name: cleanText(findDeep(zp, ["bossName", "name"])),
    boss_title: cleanText(findDeep(zp, ["bossTitle", "bossPosition", "title"])),
    company: cleanText(brandInfo.brandName || findDeep(zp, ["brandName", "companyName"])),
  };
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
  const page = pages.find(
    (item) => item.type === "page" && item.url.includes("zhipin.com") && !item.url.startsWith("chrome://"),
  );
  if (!page) throw new Error("No BOSS page found. Keep the logged-in browser open.");
  const cdp = new CdpPage(page.webSocketDebuggerUrl);
  await cdp.connect();
  await cdp.send("Runtime.enable");
  return cdp;
}

function detailApi(job) {
  const params = new URLSearchParams();
  if (job.security_id) params.set("securityId", job.security_id);
  if (job.job_id) params.set("jobId", job.job_id);
  if (job.lid) params.set("lid", job.lid);
  return `/wapi/zpgeek/job/detail.json?${params}`;
}

async function save(payload) {
  payload.meta ||= {};
  payload.meta.fast_detail_updated_at = new Date().toLocaleString("zh-CN", { hour12: false });
  await fs.writeFile(inputPath, JSON.stringify(payload, null, 2), "utf8");
}

function copyDuplicateDetails(jobs) {
  const detailByKey = new Map();
  for (const job of jobs) {
    const key = job.job_id || job.detail_url;
    if (key && job.description) detailByKey.set(key, job);
  }
  for (const job of jobs) {
    const key = job.job_id || job.detail_url;
    const found = key ? detailByKey.get(key) : null;
    if (found && !job.description) {
      job.description = found.description || "";
      job.address = job.address || found.address || "";
      job.detail_status = "copied from duplicate";
    }
  }
}

const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
payload.meta ||= {};
const jobs = Array.isArray(payload.jobs) ? payload.jobs : [];
copyDuplicateDetails(jobs);

const targets = jobs
  .map((job, index) => ({ job, index }))
  .filter(({ job }) => (force || !job.description) && job.job_id && job.security_id);

console.log(`jobs=${jobs.length} targets=${targets.length} batch=${batchSize}`);

let cdp = await currentCdp();
let done = 0;

for (let offset = 0; offset < targets.length; offset += batchSize) {
  const batch = targets.slice(offset, offset + batchSize);
  const requestJobs = batch.map(({ job, index }) => ({
    index,
    api: detailApi(job),
    name: job.job_name,
    company: job.company,
  }));

  let responses = null;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      responses = await cdp.eval(`
        (async () => {
          const jobs = ${JSON.stringify(requestJobs)};
          return Promise.all(jobs.map(async (job) => {
            try {
              const response = await fetch(job.api, {
                credentials: 'include',
                headers: {
                  'Accept': 'application/json, text/plain, */*',
                  'X-Requested-With': 'XMLHttpRequest'
                }
              });
              const text = await response.text();
              return { index: job.index, status: response.status, text };
            } catch (error) {
              return { index: job.index, status: 0, error: String(error && error.message || error) };
            }
          }));
        })()
      `);
      break;
    } catch (error) {
      console.log(`batch=${offset + 1}-${offset + batch.length} attempt=${attempt} reconnect ${error.message}`);
      cdp.close();
      await sleep(5000 + attempt * 5000);
      cdp = await currentCdp();
    }
  }

  if (!responses) {
    for (const { job } of batch) job.detail_status = "fast detail batch failed";
    await save(payload);
    continue;
  }

  for (const result of responses) {
    const job = jobs[result.index];
    if (!job) continue;
    if (result.error) {
      job.detail_status = `fast detail error: ${result.error}`;
      continue;
    }
    let data;
    try {
      data = JSON.parse(result.text);
    } catch {
      job.detail_status = `fast detail non-json: http=${result.status}`;
      continue;
    }

    if (!(data.code === 0 || data.code === "0")) {
      job.detail_status = `fast detail failed: code=${data.code} ${data.message || ""}`;
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
    job.detail_status = job.description ? "ok" : "fast detail ok, description not found";
  }

  copyDuplicateDetails(jobs);
  done += batch.length;
  payload.meta.fast_detail_progress = `${Math.min(offset + batch.length, targets.length)}/${targets.length}`;
  payload.meta.fast_detail_success_count = jobs.filter((job) => job.description).length;
  payload.meta.fast_detail_address_count = jobs.filter((job) => job.address).length;
  await save(payload);
  console.log(
    `progress=${done}/${targets.length} desc=${payload.meta.fast_detail_success_count}/${jobs.length} addr=${payload.meta.fast_detail_address_count}/${jobs.length}`,
  );

  await sleep(350 + Math.random() * 500);
  if ((offset / batchSize + 1) % 20 === 0) await sleep(4000 + Math.random() * 3000);
}

cdp.close();
copyDuplicateDetails(jobs);
payload.meta.fast_detail_progress = "done";
payload.meta.fast_detail_success_count = jobs.filter((job) => job.description).length;
payload.meta.fast_detail_address_count = jobs.filter((job) => job.address).length;
payload.meta.detail_progress = "done";
await save(payload);
console.log(`done desc=${payload.meta.fast_detail_success_count}/${jobs.length} addr=${payload.meta.fast_detail_address_count}/${jobs.length}`);
