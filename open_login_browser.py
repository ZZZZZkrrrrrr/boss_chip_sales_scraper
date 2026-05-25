from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from urllib.parse import quote


DEFAULT_PROFILE_DIR = Path(r"D:\Organized\Projects\PyCharm_Project\boss_chip_sales_scraper\browser_profile")
DEFAULT_CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
SEARCH_URL = "https://www.zhipin.com/web/geek/jobs?query=%E8%8A%AF%E7%89%87%E9%94%80%E5%94%AE&city=101280600&industry=&position="


def main() -> None:
    parser = argparse.ArgumentParser(description="打开稳定的 BOSS直聘扫码登录浏览器窗口。")
    parser.add_argument("--profile-dir", default=str(DEFAULT_PROFILE_DIR))
    parser.add_argument("--chrome-path", default=str(DEFAULT_CHROME))
    parser.add_argument("--port", type=int, default=9222)
    args = parser.parse_args()

    profile_dir = Path(args.profile_dir)
    profile_dir.mkdir(parents=True, exist_ok=True)
    chrome_path = Path(args.chrome_path)
    if not chrome_path.exists():
        raise FileNotFoundError(f"找不到 Chrome：{chrome_path}")

    login_url = f"https://www.zhipin.com/web/user/?from=passport-zp&fromUrl={quote(SEARCH_URL, safe='')}"
    command = [
        str(chrome_path),
        f"--remote-debugging-port={args.port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--new-window",
        login_url,
    ]
    subprocess.Popen(command, close_fds=True)
    print(f"已打开登录浏览器。扫码登录完成后告诉我：好了。调试地址：http://127.0.0.1:{args.port}")


if __name__ == "__main__":
    main()
