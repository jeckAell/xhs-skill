#!/usr/bin/env python3
"""
小红书自动发布工具
用法: python3 xhs_publisher.py [内容文件路径]
"""
import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path.home() / ".xhs-skill"
COOKIES_FILE = BASE_DIR / "cookies_creator.json"

CREATOR_URL = "https://creator.xiaohongshu.com"

def load_content_from_file(file_path):
    """从JSON文件加载内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # 支持多种JSON格式
    title = data.get('标题') or data.get('title') or data.get('Title', '无标题')
    body = data.get('正文') or data.get('content') or data.get('Content', '')
    tags = data.get('标签') or data.get('tags') or data.get('Tags', [])
    # 清理标签格式
    clean_tags = []
    for tag in tags:
        tag = str(tag).strip()
        if tag and not tag.startswith('#'):
            tag = '#' + tag
        clean_tags.append(tag.lstrip('#'))
    return title, body, clean_tags

async def main():
    content_file = sys.argv[1] if len(sys.argv) > 1 else None

    if content_file:
        print(f"从文件加载内容: {content_file}")
        title, body, tags = load_content_from_file(content_file)
    else:
        topic = sys.argv[1] if len(sys.argv) > 1 else "咖啡探店"
        tags_input = input("请输入标签（多个标签用逗号分隔，直接回车使用默认标签）：").strip()
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else [topic, "分享", "日常"]
        title = f"关于{topic}的分享"
        body = f"今天想和大家分享一些关于{topic}的心得...\n\n1. 第一点\n2. 第二点\n3. 第三点\n\n希望对大家有帮助！"

    content = {
        "title": title,
        "content": body,
        "tags": tags
    }

    print(f"标题: {content['title']}")
    print(f"正文长度: {len(content['content'])}")
    print(f"标签: {content['tags']}")

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

    # 点击下一步
    print("7. 点击下一步")
    try:
        await page.click('text="下一步"')
    except: pass
    await asyncio.sleep(3)

    # 在发布页面填写标题
    print("8. 填写发布标题")
    try:
        title_input = await page.wait_for_selector('input[placeholder*="标题"]', timeout=10000)
        await title_input.fill(content['title'])
    except:
        try:
            title_input = await page.wait_for_selector('input', timeout=5000)
            await title_input.fill(content['title'])
        except Exception as e:
            print(f"   填写标题失败: {e}")

    # 在正文描述中填写标签
    print("9. 填写标签")
    tags_text = " ".join([f"#{tag}" for tag in content['tags']])
    try:
        desc_input = await page.wait_for_selector('textarea[placeholder*="描述"]', timeout=10000)
        await desc_input.fill(tags_text)
    except:
        try:
            desc_input = await page.wait_for_selector('textarea', timeout=5000)
            await desc_input.fill(tags_text)
        except Exception as e:
            print(f"   填写标签失败: {e}")
            # 尝试其他选择器
            try:
                # 尝试查找id或class包含tag/desc/content的input或textarea
                selectors = [
                    'input[id*="tag"]',
                    'input[class*="tag"]',
                    'input[placeholder*="标签"]',
                    'textarea[id*="content"]',
                    'textarea[class*="content"]',
                    'div[contenteditable="true"]',
                ]
                for sel in selectors:
                    el = await page.query_selector(sel)
                    if el:
                        await el.fill(tags_text)
                        print(f"   使用选择器 {sel} 成功")
                        break
                else:
                    # 最后一个input通常是标签输入
                    inputs = await page.query_selector_all('input')
                    if len(inputs) > 3:
                        await inputs[3].fill(tags_text)
                        print(f"   使用 inputs[3] 填写标签")
            except Exception as e2:
                print(f"   备用选择器也失败: {e2}")

    await asyncio.sleep(1)

    # 点击发布
    print("10. 点击发布")
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
