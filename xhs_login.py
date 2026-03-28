#!/usr/bin/env python3
"""
小红书创作平台登录
用法: python3 xhs_login.py
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path.home() / ".xhs-skill"
COOKIES_FILE = BASE_DIR / "cookies_creator.json"
CREATOR_URL = "https://creator.xiaohongshu.com"

async def main():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,
        executable_path='/usr/bin/chromium-browser',
        args=['--no-first-run', '--disable-dev-shm-usage']
    )
    context = await browser.new_context(
        locale='zh-CN',
        viewport={'width': 1280, 'height': 800},
    )
    page = await context.new_page()

    print("打开创作平台...")
    await page.goto(f"{CREATOR_URL}/publish/publish?source=official", wait_until='domcontentloaded')
    await asyncio.sleep(3)

    if 'login' in page.url.lower():
        print("需要登录，请在浏览器中扫码...")
        for i in range(300):
            await asyncio.sleep(1)
            if 'login' not in page.url.lower():
                print(f"登录成功！({i+1}秒)")
                break
        await asyncio.sleep(3)

    print("保存cookies...")
    cookies = await context.cookies()
    xhs_cookies = [c for c in cookies if 'xiaohongshu.com' in c['domain']]

    with open(COOKIES_FILE, 'w') as f:
        json.dump(xhs_cookies, f, ensure_ascii=False, indent=2)

    print(f"已保存 {len(xhs_cookies)} 个cookies")

    has_token = any('access-token' in c['name'] or 'galaxy' in c['name'] for c in xhs_cookies)
    print(f"包含认证token: {has_token}")

    await browser.close()
    await playwright.stop()

    if has_token:
        print("\n登录成功！可以运行 python3 xhs_publisher.py <主题> 发布内容了。")
    else:
        print("\n警告: 可能未登录成功，请重试。")

if __name__ == "__main__":
    asyncio.run(main())
