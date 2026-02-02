import subprocess
from playwright.async_api import async_playwright

# 强制使用 IPv4 127.0.0.1 避免 Windows 下的 IPv6 问题
DEBUG_PORT_URL = "http://127.0.0.1:9222"


def ensure_chromium_installed():
    """检查并自动安装 Chromium（如果需要）。"""
    try:
        subprocess.run(
            ["playwright", "install", "chromium"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass


async def get_active_tab_snapshot():
    """
    连接到运行中的浏览器 (Edge/Chrome) 并抓取当前激活 Tab 的 DOM。
    返回: (url, raw_html_content)
    """
    try:
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp(DEBUG_PORT_URL)
            except Exception:
                print(f"❌ 连接失败: 无法连接到 {DEBUG_PORT_URL}")
                print("⚠️  请确保浏览器已启动且带有参数: --remote-debugging-port=9222")
                return None, None

            if not browser.contexts:
                print("❌ 未找到浏览器上下文 (Browser Context)。")
                await browser.close()
                return None, None

            pages = []
            for ctx in browser.contexts:
                pages.extend(ctx.pages)

            if not pages:
                print("❌ 浏览器中没有打开的页面。")
                await browser.close()
                return None, None

            target_page = None
            fallback_page = None

            print(f"🔍 正在扫描 {len(pages)} 个标签页以寻找激活页...")

            for page in pages:
                if page.url == "about:blank" or page.url.startswith("devtools://"):
                    continue

                if fallback_page is None:
                    fallback_page = page

                try:
                    visibility = await page.evaluate("document.visibilityState")
                    has_focus = await page.evaluate("document.hasFocus()")
                    if has_focus:
                        target_page = page
                        print("✅ 找到激活的标签页 (hasFocus)。")
                        break
                    if visibility == "visible":
                        target_page = page
                        print("✅ 找到激活的标签页 (visible)。")
                        break
                except Exception:
                    continue

            if not target_page:
                if fallback_page:
                    print("⚠️ 未找到可见标签页，使用第一个有效标签页作为兜底。")
                    target_page = fallback_page
                else:
                    print("❌ 未找到有效网页。")
                    await browser.close()
                    return None, None

            title = await target_page.title()
            url = target_page.url
            print(f"🔗 目标标签页: {title}")
            print(f"🔗 URL: {url}")

            content = await target_page.content()
            await browser.close()

            return url, content

    except Exception as e:
        print(f"🔥 快照抓取期间发生错误: {e}")
        return None, None
