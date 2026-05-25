import fs from "node:fs/promises";

const cdpUrl = process.argv[2] || "http://127.0.0.1:9222";
const inputPath = process.argv[3] || "C:\\Users\\96259\\Desktop\\AIcoding\\贸易\\BOSS直聘_IC销售_IC采购_深圳招聘_latest.json";

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

function clean(text) {
  return String(text || "").replace(/\s+/g, " ").trim();
}

async function currentCdp() {
  const pages = await getJson(`${cdpUrl}/json`);
  const page = pages.find((item) => item.type === "page" && item.url.includes("zhipin.com") && !item.url.startsWith("chrome://"));
  if (!page) throw new Error("No BOSS page found");
  const cdp = new CdpPage(page.webSocketDebuggerUrl);
  await cdp.connect();
  await cdp.send("Runtime.enable");
  return cdp;
}

const payload = JSON.parse(await fs.readFile(inputPath, "utf8"));
const jobs = payload.jobs.slice(0, 8);
const cdp = await currentCdp();
for (const job of jobs) {
  const result = await cdp.eval(`
    (async () => {
      const response = await fetch(${JSON.stringify(job.detail_url)}, { credentials: 'include' });
      const text = await response.text();
      const doc = new DOMParser().parseFromString(text, 'text/html');
      const desc = doc.querySelector('.job-sec-text')?.innerText || doc.querySelector('.job-detail-section .text')?.innerText || '';
      const address = doc.querySelector('.location-address')?.innerText || doc.querySelector('.job-address-desc')?.innerText || '';
      return { status: response.status, finalUrl: response.url, title: doc.title, desc, address, text: text.slice(0, 300) };
    })()
  `);
  console.log(JSON.stringify({
    job: job.job_name,
    company: job.company,
    status: result.status,
    title: result.title,
    descLen: clean(result.desc).length,
    address: clean(result.address),
    finalUrl: result.finalUrl,
    textHead: clean(result.text).slice(0, 120),
  }, null, 2));
}
cdp.close();
