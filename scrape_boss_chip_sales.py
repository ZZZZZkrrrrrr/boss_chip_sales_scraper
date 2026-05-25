from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urljoin

from playwright.sync_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


DEFAULT_OUTPUT_DIR = Path(r"C:\Users\96259\Desktop\AIcoding\贸易")
DEFAULT_PROFILE_DIR = Path(r"D:\Organized\Projects\PyCharm_Project\boss_chip_sales_scraper\browser_profile")
DEFAULT_CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

BASE_URL = "https://www.zhipin.com"

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
window.chrome = window.chrome || { runtime: {} };
"""


def log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " | ".join(clean_text(item) for item in value if clean_text(item))
    text = str(value)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def first_present(data: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, "", []):
            return data[key]
    return ""


def normalize_list_job(raw: dict[str, Any], page_no: int) -> dict[str, Any]:
    city_parts = [
        first_present(raw, ["cityName", "city"]),
        first_present(raw, ["areaDistrict", "districtName", "area"]),
        first_present(raw, ["businessDistrict", "businessDistrictName"]),
    ]
    job = {
        "job_id": first_present(raw, ["encryptJobId", "jobId", "securityJobId"]),
        "security_id": first_present(raw, ["securityId"]),
        "lid": first_present(raw, ["lid"]),
        "job_name": first_present(raw, ["jobName", "name", "title"]),
        "salary": first_present(raw, ["salaryDesc", "salary", "salaryName"]),
        "city": clean_text(city_parts[0]),
        "district": clean_text(city_parts[1]),
        "business_district": clean_text(city_parts[2]),
        "experience": first_present(raw, ["jobExperience", "experienceName", "experience"]),
        "degree": first_present(raw, ["jobDegree", "degreeName", "degree"]),
        "company": first_present(raw, ["brandName", "companyName"]),
        "industry": first_present(raw, ["brandIndustry", "industryName", "industry"]),
        "company_scale": first_present(raw, ["brandScaleName", "scaleName", "scale"]),
        "financing_stage": first_present(raw, ["brandStageName", "stageName", "stage"]),
        "boss_name": first_present(raw, ["bossName", "encryptBossName"]),
        "boss_title": first_present(raw, ["bossTitle", "bossPosition"]),
        "tags": clean_text(first_present(raw, ["jobLabels", "labels", "tagList"])),
        "skills": clean_text(first_present(raw, ["skills", "skillLabels"])),
        "welfare": clean_text(first_present(raw, ["welfareList", "welfare"])),
        "source_page": page_no,
        "source": "BOSS直聘",
        "detail_url": "",
        "description": "",
        "address": "",
        "detail_status": "",
    }

    direct_url = first_present(raw, ["jobHref", "href", "url"])
    if direct_url:
        job["detail_url"] = urljoin(BASE_URL, str(direct_url))
    elif job["job_id"]:
        params = {}
        if job["lid"]:
            params["lid"] = job["lid"]
        if job["security_id"]:
            params["securityId"] = job["security_id"]
        query = f"?{urlencode(params)}" if params else ""
        job["detail_url"] = f"{BASE_URL}/job_detail/{job['job_id']}.html{query}"

    return {key: clean_text(value) for key, value in job.items()}


def search_url(query: str, city: str) -> str:
    return f"{BASE_URL}/web/geek/jobs?query={quote(query)}&city={city}&industry=&position="


def joblist_api_url(query: str, city: str, page_no: int, page_size: int) -> str:
    params = {
        "scene": "1",
        "query": query,
        "city": city,
        "experience": "",
        "payType": "",
        "partTime": "",
        "degree": "",
        "industry": "",
        "scale": "",
        "stage": "",
        "position": "",
        "jobType": "",
        "salary": "",
        "multiBusinessDistrict": "",
        "multiSubway": "",
        "page": str(page_no),
        "pageSize": str(page_size),
    }
    return f"{BASE_URL}/wapi/zpgeek/search/joblist.json?{urlencode(params)}"


def evaluate_fetch_json(page: Page, url: str) -> dict[str, Any]:
    result = page.evaluate(
        """
        async (url) => {
            const response = await fetch(url, {
                credentials: 'include',
                headers: {
                    'Accept': 'application/json, text/plain, */*',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            const text = await response.text();
            return { status: response.status, url: response.url, text };
        }
        """,
        url,
    )
    try:
        data = json.loads(result["text"])
    except json.JSONDecodeError:
        data = {"code": -1, "message": "non-json response", "raw": result["text"][:500]}
    data["_http_status"] = result["status"]
    data["_response_url"] = result["url"]
    return data


def extract_jobs_from_api(data: dict[str, Any]) -> tuple[list[dict[str, Any]], bool | None, int | None]:
    zp = data.get("zpData") or data.get("data") or {}
    jobs = (
        zp.get("jobList")
        or zp.get("jobs")
        or zp.get("list")
        or data.get("jobList")
        or data.get("list")
        or []
    )
    has_more = first_present(zp, ["hasMore", "hasNextPage", "hasNext", "has_more"])
    total = first_present(zp, ["totalCount", "total", "count"])
    if has_more == "":
        has_more = None
    if isinstance(has_more, str):
        has_more = has_more.lower() in ("true", "1", "yes")
    try:
        total_int = int(total) if total != "" else None
    except (TypeError, ValueError):
        total_int = None
    return jobs if isinstance(jobs, list) else [], has_more, total_int


def is_login_page(page: Page) -> bool:
    url = page.url
    if "/web/user" in url or "/passport" in url:
        return True
    try:
        text = page.locator("body").inner_text(timeout=1500)
    except Exception:
        return False
    return any(marker in text for marker in ["扫码登录", "验证码登录", "登录/注册"])


def has_job_page(page: Page) -> bool:
    try:
        if page.locator(".job-card-wrapper, li.job-card-wrapper, .job-list-box li").count() > 0:
            return True
    except Exception:
        return False
    return "/web/geek/jobs" in page.url and not is_login_page(page)


def is_logged_in(page: Page) -> bool:
    try:
        text = page.locator("body").inner_text(timeout=1500)
    except Exception:
        return False
    if any(marker in text for marker in ["扫码登录", "验证码登录/注册", "登录/注册", "发送验证码"]):
        return False
    return "消息" in text and "简历" in text


def wait_for_login_and_search(page: Page, query: str, city: str, login_timeout: int, require_login: bool) -> None:
    url = search_url(query, city)
    log(f"打开职位搜索页：{url}")
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    page.wait_for_timeout(3000)

    deadline = time.monotonic() + login_timeout
    reminded = False

    if require_login and not is_logged_in(page):
        login_url = f"{BASE_URL}/web/user/?from=passport-zp&fromUrl={quote(url, safe='')}"
        log("为了抓取详情，先固定停在登录页等待扫码，不再自动来回跳转。")
        page.goto(login_url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(2500)
        log("请在浏览器里完成扫码登录；检测到登录态后会自动进入搜索页。")
        while time.monotonic() < deadline:
            if is_logged_in(page):
                log("已确认账号登录。")
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(2500)
                return
            page.wait_for_timeout(3000)
        raise TimeoutError("等待扫码登录超时。请重新运行脚本或延长 --login-timeout。")

    while time.monotonic() < deadline:
        if require_login and is_logged_in(page):
            log("已确认账号登录。")
            if "/web/geek/jobs" not in page.url:
                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(2500)
            return

        if has_job_page(page):
            if not require_login:
                log("已进入职位搜索页，开始抓取。")
                return
            if not is_logged_in(page):
                login_url = f"{BASE_URL}/web/user/?from=passport-zp&fromUrl={quote(url, safe='')}"
                log("当前能看列表但未确认登录；为了抓取详情，打开登录页等待扫码。")
                page.goto(login_url, wait_until="domcontentloaded", timeout=60_000)
                page.wait_for_timeout(2500)

        if not reminded:
            log("如果浏览器显示登录二维码，请现在扫码登录；登录完成后脚本会自动继续。")
            reminded = True

        if not is_login_page(page) and "/web/geek/jobs" not in page.url:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            except PlaywrightTimeoutError:
                pass

        try:
            api_data = evaluate_fetch_json(page, joblist_api_url(query, city, 1, 30))
            jobs, _, _ = extract_jobs_from_api(api_data)
            if jobs and not require_login:
                log("登录状态有效，接口已返回职位列表。")
                if "/web/geek/jobs" not in page.url:
                    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                return
            if api_data.get("code") not in (0, "0", None):
                message = clean_text(api_data.get("message"))
                if message and not is_login_page(page):
                    log(f"等待中，接口提示：{message}")
        except Exception:
            pass

        page.wait_for_timeout(5000)

    raise TimeoutError("等待扫码登录超时。请重新运行脚本或延长 --login-timeout。")


def scrape_job_pages(page: Page, query: str, city: str, max_pages: int, page_size: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_jobs: list[dict[str, Any]] = []
    seen: set[str] = set()
    total_count: int | None = None
    consecutive_empty = 0

    for page_no in range(1, max_pages + 1):
        api_url = joblist_api_url(query, city, page_no, page_size)
        data = evaluate_fetch_json(page, api_url)
        code = data.get("code")
        if code not in (0, "0", None):
            raise RuntimeError(f"职位列表接口失败：code={code} message={data.get('message')}")

        raw_jobs, has_more, total = extract_jobs_from_api(data)
        if total is not None:
            total_count = total
        log(f"列表第 {page_no} 页返回 {len(raw_jobs)} 条。")

        if not raw_jobs:
            consecutive_empty += 1
            if consecutive_empty >= 2:
                break
        else:
            consecutive_empty = 0

        added = 0
        for raw in raw_jobs:
            if not isinstance(raw, dict):
                continue
            job = normalize_list_job(raw, page_no)
            key = job.get("job_id") or f"{job.get('job_name')}|{job.get('company')}|{job.get('salary')}|{job.get('boss_name')}"
            if key in seen:
                continue
            seen.add(key)
            all_jobs.append(job)
            added += 1

        if total_count and len(all_jobs) >= total_count:
            break
        if has_more is False:
            break
        if not raw_jobs and has_more is not True:
            break
        if added == 0 and has_more is not True:
            break

        time.sleep(random.uniform(1.2, 2.5))

    meta = {
        "query": query,
        "city_code": city,
        "source_url": search_url(query, city),
        "total_count_reported": total_count,
        "list_count": len(all_jobs),
        "page_size": page_size,
        "max_pages": max_pages,
        "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return all_jobs, meta


def fallback_between(text: str, start_markers: list[str], end_markers: list[str]) -> str:
    start_positions = [text.find(marker) + len(marker) for marker in start_markers if text.find(marker) >= 0]
    if not start_positions:
        return ""
    start = min(start_positions)
    end_candidates = [text.find(marker, start) for marker in end_markers if text.find(marker, start) > start]
    end = min(end_candidates) if end_candidates else len(text)
    return clean_text(text[start:end])


def parse_detail_dom(page: Page) -> dict[str, str]:
    data = page.evaluate(
        """
        () => {
            const text = (selector) => {
                const el = document.querySelector(selector);
                return el && el.innerText ? el.innerText.trim() : '';
            };
            const texts = (selector) => Array.from(document.querySelectorAll(selector))
                .map(el => (el.innerText || '').trim())
                .filter(Boolean);
            const body = document.body ? document.body.innerText : '';
            return {
                pageTitle: document.title || '',
                jobName: text('.job-title, .job-name, .name h1, h1'),
                salary: text('.salary, .job-banner .salary, .job-primary .salary'),
                description: text('.job-sec-text, .job-detail-section .text, .job-detail .text, .detail-content .text, .job-description'),
                address: text('.location-address, .job-address, .job-location .location-address, .job-location, .location-main'),
                bossName: text('.boss-info .name, .boss-name, .detail-op .name, .op-name'),
                bossTitle: text('.boss-info .boss-title, .boss-title, .detail-op .gray'),
                company: text('.company-info .name, .company-name, .job-company-info .name'),
                tags: texts('.job-keyword-list li, .job-tags span, .tag-list span, .job-labels span').join(' | '),
                bodyText: body
            };
        }
        """
    )
    body = clean_text(data.get("bodyText", ""))
    description = clean_text(data.get("description"))
    address = clean_text(data.get("address"))
    if not description:
        description = fallback_between(body, ["职位描述", "职位详情"], ["工作地址", "公司介绍", "工商信息", "相似职位"])
    if not address:
        address = fallback_between(body, ["工作地址"], ["公司介绍", "工商信息", "职位描述", "相似职位"])
        address = clean_text("\n".join(address.splitlines()[:3]))

    return {
        "detail_job_name": clean_text(data.get("jobName")),
        "detail_salary": clean_text(data.get("salary")),
        "description": description,
        "address": address,
        "detail_boss_name": clean_text(data.get("bossName")),
        "detail_boss_title": clean_text(data.get("bossTitle")),
        "detail_company": clean_text(data.get("company")),
        "detail_tags": clean_text(data.get("tags")),
        "detail_page_title": clean_text(data.get("pageTitle")),
    }


def enrich_details(context: BrowserContext, jobs: list[dict[str, Any]], delay_min: float, delay_max: float) -> None:
    detail_page = context.new_page()
    try:
        for idx, job in enumerate(jobs, start=1):
            url = job.get("detail_url", "")
            if not url:
                job["detail_status"] = "missing detail url"
                continue
            log(f"抓取详情 {idx}/{len(jobs)}：{job.get('job_name')} - {job.get('company')}")
            try:
                detail_page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                detail_page.wait_for_timeout(random.randint(1600, 3200))
                if is_login_page(detail_page):
                    job["detail_status"] = "redirected to login"
                    log("详情页跳到登录页，停止详情抓取，保留已抓列表数据。")
                    break
                parsed = parse_detail_dom(detail_page)
                if parsed.get("description"):
                    job["description"] = parsed["description"]
                if parsed.get("address"):
                    job["address"] = parsed["address"]
                if parsed.get("detail_tags") and not job.get("tags"):
                    job["tags"] = parsed["detail_tags"]
                if parsed.get("detail_boss_name") and not job.get("boss_name"):
                    job["boss_name"] = parsed["detail_boss_name"]
                if parsed.get("detail_boss_title") and not job.get("boss_title"):
                    job["boss_title"] = parsed["detail_boss_title"]
                if parsed.get("detail_company") and not job.get("company"):
                    job["company"] = parsed["detail_company"]
                if parsed.get("detail_salary") and not job.get("salary"):
                    job["salary"] = parsed["detail_salary"]
                job["detail_status"] = "ok" if job.get("description") or job.get("address") else "parsed without description/address"
            except Exception as exc:
                job["detail_status"] = f"error: {type(exc).__name__}: {exc}"
            time.sleep(random.uniform(delay_min, delay_max))
    finally:
        detail_page.close()


def write_json(output_dir: Path, query: str, jobs: list[dict[str, Any]], meta: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", query).strip("_")
    path = output_dir / f"BOSS直聘_{safe_query}_深圳招聘_{stamp}.json"
    payload = {"meta": meta, "jobs": jobs}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest = output_dir / "BOSS直聘_芯片销售_深圳招聘_latest.json"
    latest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def run(args: argparse.Namespace) -> Path:
    profile_dir = Path(args.profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    output_dir = Path(args.output_dir)
    chrome_path = Path(args.chrome_path)
    if not chrome_path.exists():
        raise FileNotFoundError(f"找不到 Chrome：{chrome_path}")

    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            executable_path=str(chrome_path),
            headless=False,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            viewport={"width": 1500, "height": 920},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--start-maximized",
            ],
        )
        context.add_init_script(STEALTH_SCRIPT)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            wait_for_login_and_search(page, args.query, args.city, args.login_timeout, args.require_login or args.details)
            jobs, meta = scrape_job_pages(page, args.query, args.city, args.max_pages, args.page_size)
            log(f"列表抓取完成，共 {len(jobs)} 条去重职位。")
            if args.details and jobs:
                enrich_details(context, jobs, args.delay_min, args.delay_max)
            json_path = write_json(output_dir, args.query, jobs, meta)
            log(f"JSON 已保存：{json_path}")
            return json_path
        finally:
            context.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抓取 BOSS直聘深圳芯片销售招聘信息，并保存 JSON。")
    parser.add_argument("--query", default="芯片销售", help="搜索关键词")
    parser.add_argument("--city", default="101280600", help="城市编码，深圳为 101280600")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="JSON 输出目录")
    parser.add_argument("--profile-dir", default=str(DEFAULT_PROFILE_DIR), help="浏览器登录资料目录")
    parser.add_argument("--chrome-path", default=str(DEFAULT_CHROME), help="Chrome 可执行文件路径")
    parser.add_argument("--max-pages", type=int, default=50, help="最多抓取列表页数")
    parser.add_argument("--page-size", type=int, default=30, help="每页数量")
    parser.add_argument("--login-timeout", type=int, default=900, help="等待扫码登录秒数")
    parser.add_argument("--details", action=argparse.BooleanOptionalAction, default=True, help="是否逐条抓取详情页")
    parser.add_argument("--require-login", action=argparse.BooleanOptionalAction, default=False, help="抓取前是否强制等待账号登录")
    parser.add_argument("--delay-min", type=float, default=1.8, help="详情页最小间隔秒数")
    parser.add_argument("--delay-max", type=float, default=3.8, help="详情页最大间隔秒数")
    return parser.parse_args()


if __name__ == "__main__":
    try:
        result_path = run(parse_args())
        print(str(result_path), flush=True)
    except KeyboardInterrupt:
        log("已手动中断。")
        sys.exit(130)
    except Exception as exc:
        log(f"失败：{type(exc).__name__}: {exc}")
        sys.exit(1)
