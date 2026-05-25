from __future__ import annotations

import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from scrape_boss_chip_sales import (
    DEFAULT_OUTPUT_DIR,
    enrich_details,
    is_logged_in,
    log,
    scrape_job_pages,
    search_url,
    write_json,
)


def pick_page(context, query: str, city: str):
    wanted = search_url(query, city)
    for page in context.pages:
        if "/web/geek/jobs" in page.url and "zhipin.com" in page.url:
            return page
    for page in context.pages:
        if "zhipin.com" in page.url and not page.is_closed():
            return page
    page = context.new_page()
    page.goto(wanted, wait_until="domcontentloaded", timeout=60_000)
    return page


def run(args: argparse.Namespace) -> Path:
    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(args.cdp_url)
        if not browser.contexts:
            raise RuntimeError("没有找到可用的 Chrome 上下文，请先运行 open_login_browser.py。")
        context = browser.contexts[0]
        page = pick_page(context, args.query, args.city)

        if not is_logged_in(page):
            log("未检测到登录态。请先在打开的 Chrome 窗口完成扫码登录，再重新运行本脚本。")
            raise RuntimeError("not logged in")

        url = search_url(args.query, args.city)
        log(f"进入搜索页：{url}")
        if "/web/geek/jobs" not in page.url:
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(3000)
        else:
            page.wait_for_timeout(1000)

        jobs, meta = scrape_job_pages(page, args.query, args.city, args.max_pages, args.page_size)
        log(f"列表抓取完成，共 {len(jobs)} 条去重职位。")

        if args.details and jobs:
            enrich_details(context, jobs, args.delay_min, args.delay_max)

        json_path = write_json(Path(args.output_dir), args.query, jobs, meta)
        log(f"JSON 已保存：{json_path}")
        browser.close()
        return json_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="连接已登录 Chrome，抓取 BOSS直聘芯片销售招聘信息。")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--query", default="芯片销售")
    parser.add_argument("--city", default="101280600")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--page-size", type=int, default=30)
    parser.add_argument("--details", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--delay-min", type=float, default=1.8)
    parser.add_argument("--delay-max", type=float, default=3.8)
    return parser.parse_args()


if __name__ == "__main__":
    try:
        print(str(run(parse_args())), flush=True)
    except Exception as exc:
        log(f"失败：{type(exc).__name__}: {exc}")
        sys.exit(1)
