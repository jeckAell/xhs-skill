#!/usr/bin/env python3
"""
小红书自动发布工具
用法: python3 xhs_publisher.py <主题>
"""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path.home() / ".xhs-skill"
COOKIES_FILE = BASE_DIR / "cookies_creator.json"

CREATOR_URL = "https://creator.xiaohongshu.com"

async def main():
    topic = sys.argv[1] if len(sys.argv) > 1 else "咖啡探店"

    content = {
        "title": f"关于{topic}的分享",
        "content": f"今天想和大家分享一些关于{topic}的心得...\n\n1. 第一点\n2. 第二点\n3. 第三点\n\n希望对大家有帮助！",
        "tags": [topic, "分享", "日常"]
    }

    print(f"主题: {topic}")
    print(f"标题: {content['title']}")

    # 启动浏览器
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

    # 加载cookies
    if COOKIES_FILE.exists():
        with open(COOKIES_FILE) as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        print("已加载cookies")

    page = await context.new_page()

    # 打开创作平台
    print("打开创作平台...")
    await page.goto(f"{CREATOR_URL}/publish/publish?source=official", wait_until='domcontentloaded')
    await asyncio.sleep(5)

    # 检查登录状态
    if 'login' in page.url.lower():
        print("需要登录，请在浏览器中扫码...")
        for i in range(300):
            await asyncio.sleep(1)
            if 'login' not in page.url.lower():
                print(f"登录成功！({i+1}秒)")
                break
        await asyncio.sleep(3)

    # 进入写长文
    print("1. 点击写长文")
    await page.click('text="写长文"')
    await asyncio.sleep(2)

    print("2. 再次点击写长文")
    await page.click('text="写长文"')
    await asyncio.sleep(5)

    print("3. 点击新的创作")
    await page.click('text="新的创作"')
    await asyncio.sleep(5)

    # 输入标题
    print("4. 输入标题")
    try:
        title_input = await page.wait_for_selector('textarea[placeholder="输入标题"]', timeout=10000)
        await title_input.fill(content['title'])
        print(f"   {content['title']}")
    except Exception as e:
        print(f"   失败: {e}")

    # 输入正文
    print("5. 输入正文")
    try:
        editor = await page.wait_for_selector('.ProseMirror', timeout=10000)
        await editor.click()
        await editor.fill(content['content'])
        print(f"   长度: {len(content['content'])}")
    except Exception as e:
        print(f"   失败: {e}")

    # 点击一键排版
    print("6. 点击一键排版")
    try:
        await page.click('text="一键排版"')
    except: pass
    await asyncio.sleep(2)

    # 点击发布
    print("7. 点击发布")
    try:
        await page.click('text="发布"')
    except: pass

    print("\n发布请求已发送，请在浏览器中确认！")

    # 等待用户确认
    await asyncio.sleep(10)

    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
