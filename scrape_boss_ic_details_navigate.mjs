import fs from "node:fs/promises";
import path from "node:path";

const cdpUrl = process.argv[2] || "http://127.0.0.1:9222";
const inputPath = process.argv[3] || "C:\\Users\\96259\\Desktop\\AIcoding\\贸易\\BOSS直聘_IC销售_IC采购_深圳招聘_latest.json";
const limit = Number.parseInt(process.env.BOSS_NAV_DETAIL_LIMIT || "0", 10);

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function cleanText(value) {
  return String(value || "")
    .replace(/\u00a0/g, " ")
    .replace(/[ \t\r\f\v]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
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
  await cdp.send("Page.enable");
  return cdp;
}

async function save(payload, latestPath) {
  payload.meta.nav_detail_updated_at = new Date().toLocaleString("zh-CN", { hour12: false });
  await fs.writeFile(inputPath, JSON.stringify(payload, null, 2), "utf8");
  await fs.writeFile(latestPath, JSON.stringify(payload, null, 2), "utf8");
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

async function readDetailFromPage(cdp) {
  return cdp.eval(`
    (() => {
      const pick = (selectors) => {
        for (const selector of selectors) {
          const el = document.querySelector(selector);
          if (el && el.innerText && el.innerText.trim()) return el.innerText.trim();
        }
        return '';
      };
      const title = document.title || '';
      const text = document.body ? document.body.innerText : '';
      return {
        url: location.href,
        title,
        security: title.includes('请稍候') || location.href.includes('/security-check') || text.includes('安全验证'),
        desc: pick(['.job-sec-text', '.job-detail-section .text', '.job-detail-section', '.job-detail']),
        address: pick(['.location-address', '.job-address-desc', '.job-location .location-address']),
        bodyHead: text.slice(0, 260)
      };
    })()
  `);
}

const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
payload.meta ||= {};
const jobs = Array.isArray(payload.jobs) ? payload.jobs : [];
const latestPath = path.join(path.dirname(inputPath), "BOSS直聘_IC销售_IC采购_深圳招聘_latest.json");

copyDuplicateDetails(jobs);
let targets = jobs.filter((job) => !job.description && job.detail_url);
if (limit > 0) targets = targets.slice(0, limit);
console.log(`jobs=${jobs.length} targets=${targets.length}`);

let cdp = await currentCdp();
let consecutiveSecurity = 0;

for (let i = 0; i < targets.length; i += 1) {
  const job = targets[i];
  if (job.description) {
    payload.meta.nav_detail_progress = `${i + 1}/${targets.length}`;
    payload.meta.nav_detail_success_count = jobs.filter((item) => item.description).length;
    payload.meta.nav_detail_address_count = jobs.filter((item) => item.address).length;
    await save(payload, latestPath);
    continue;
  }
  console.log(`[nav-detail] ${i + 1}/${targets.length} ${job.query} ${job.job_name} - ${job.company}`);
  let ok = false;

  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      await cdp.send("Page.navigate", { url: job.detail_url });
      await sleep(4200 + Math.random() * 2800 + attempt * 1200);
      let detail = await readDetailFromPage(cdp);

      if (detail.security || cleanText(detail.desc).length < 20) {
        console.log(`  attempt=${attempt} security_or_empty title=${detail.title} url=${detail.url}`);
        await sleep(8000 + Math.random() * 8000);
        detail = await readDetailFromPage(cdp);
      }

      if (detail.security || cleanText(detail.desc).length < 20) {
        job.detail_status = `navigate failed: ${detail.title || "empty detail"}`;
        consecutiveSecurity += detail.security ? 1 : 0;
        if (consecutiveSecurity >= 3) {
          const coolMs = 180000 + Math.random() * 120000;
          console.log(`  cooldown ${Math.round(coolMs / 1000)}s`);
          payload.meta.nav_detail_progress = `${i + 1}/${targets.length}`;
          await save(payload, latestPath);
          await sleep(coolMs);
          consecutiveSecurity = 0;
          cdp.close();
          cdp = await currentCdp();
        }
        continue;
      }

      job.description = cleanText(detail.desc);
      job.address = cleanText(detail.address);
      job.detail_status = "ok";
      consecutiveSecurity = 0;
      ok = true;
      console.log(`  ok desc=${job.description.length} address=${job.address.length}`);
      break;
    } catch (error) {
      job.detail_status = `navigate error: ${error.message}`;
      console.log(`  attempt=${attempt} ${job.detail_status}`);
      cdp.close();
      await sleep(8000 + attempt * 4000);
      cdp = await currentCdp();
    }
  }

  copyDuplicateDetails(jobs);
  payload.meta.nav_detail_progress = `${i + 1}/${targets.length}`;
  payload.meta.nav_detail_success_count = jobs.filter((item) => item.description).length;
  payload.meta.nav_detail_address_count = jobs.filter((item) => item.address).length;
  await save(payload, latestPath);

  if (!ok) {
    await sleep(10000 + Math.random() * 10000);
  } else {
    await sleep(2200 + Math.random() * 3500);
  }

  if ((i + 1) % 50 === 0) {
    const restMs = 45000 + Math.random() * 45000;
    console.log(`  batch rest ${Math.round(restMs / 1000)}s`);
    await sleep(restMs);
  }
}

cdp.close();
copyDuplicateDetails(jobs);
payload.meta.nav_detail_progress = "done";
payload.meta.nav_detail_success_count = jobs.filter((item) => item.description).length;
payload.meta.nav_detail_address_count = jobs.filter((item) => item.address).length;
await save(payload, latestPath);
console.log(`done desc=${jobs.filter((job) => job.description).length}/${jobs.length} addr=${jobs.filter((job) => job.address).length}/${jobs.length}`);
