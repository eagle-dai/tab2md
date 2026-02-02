import asyncio
import os
import re
import sys
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

# === Configuration ===
# 强制使用 IPv4 127.0.0.1 避免 Windows 下的 IPv6 问题
DEBUG_PORT_URL = "http://127.0.0.1:9222"
OUTPUT_DIR = "exports"


def ensure_chromium_installed():
    """Check and auto-install Chromium if needed."""
    try:
        subprocess.run(
            ["playwright", "install", "chromium"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass  # Silently fail or rely on user manual install


async def get_active_tab_snapshot():
    """
    Connect to the running browser (Edge/Chrome) via CDP
    and capture the DOM of the active tab.
    """
    try:
        async with async_playwright() as p:
            try:
                # 尝试连接到调试端口
                browser = await p.chromium.connect_over_cdp(DEBUG_PORT_URL)
            except Exception:
                print(f"❌ Connection Failed: Could not connect to {DEBUG_PORT_URL}")
                print(
                    "⚠️  Ensure your browser is started with: --remote-debugging-port=9222"
                )
                return None, None

            if not browser.contexts:
                print("❌ No browser context found.")
                await browser.close()
                return None, None

            ctx = browser.contexts[0]

            # 智能寻找激活的页面
            target_page = None
            for page in ctx.pages:
                if page.url != "about:blank" and not page.url.startswith("devtools://"):
                    target_page = page
                    break

            if not target_page:
                print("❌ No active web page found.")
                await browser.close()
                return None, None

            title = await target_page.title()
            print(f"🔗 Targeted Tab: {title}")
            print(f"🔗 URL: {target_page.url}")

            # 抓取完整渲染后的 HTML
            content = await target_page.content()
            url = target_page.url

            # 使用 close() 断开连接 (不会关闭 Edge 窗口)
            await browser.close()

            return url, content

    except Exception as e:
        print(f"🔥 Error during snapshot: {e}")
        return None, None


def inject_base_tag(html: str, url: str) -> str:
    """Inject <base> tag to fix relative links."""
    base_tag = f'<base href="{url}">'
    if "<head>" in html:
        return html.replace("<head>", f"<head>\n{base_tag}", 1)
    return f"<html><head>{base_tag}</head>" + html


async def process_conversion():
    # 1. Capture Snapshot
    url, raw_html = await get_active_tab_snapshot()
    if not raw_html:
        return

    # 2. Prepare Local File
    html_with_base = inject_base_tag(raw_html, url)
    temp_file = Path("temp_snapshot.html").resolve()
    temp_file.write_text(html_with_base, encoding="utf-8")

    # === [关键修复] Windows 路径兼容性 ===
    # 强制生成 "file://C:/path/to/file" 格式 (双斜杠)
    # 而不是 "file:///C:/path/to/file" (三斜杠，as_uri() 的默认行为)
    # 这样 Crawl4AI 切片 url[7:] 后才能得到正确的 "C:/path..."
    local_file_uri = f"file://{temp_file.as_posix()}"

    print("🚀 Running extraction engine (Crawl4AI)...")

    # 3. Configure Extraction
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        magic=True,
        word_count_threshold=5,
        excluded_tags=[
            "nav",
            "footer",
            "aside",
            "script",
            "style",
            "iframe",
            "form",
            "noscript",
            "svg",
        ],
    )

    # 4. Run Conversion
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=local_file_uri, config=run_cfg)

        if result.success:
            # Generate Safe Filename
            slug = re.sub(r"[^a-zA-Z0-9]", "_", url.split("//")[-1])
            safe_name = f"{slug[:50]}"

            output_path = Path(OUTPUT_DIR)
            output_path.mkdir(exist_ok=True)

            md_file = output_path / f"{safe_name}.md"
            md_file.write_text(result.markdown, encoding="utf-8")

            print(f"\n✅ Conversion Complete!")
            print(f"📂 Saved to: {md_file}")

            # Cleanup
            try:
                os.remove(temp_file)
            except:
                pass

            # Auto-open (Windows)
            if sys.platform == "win32":
                os.system(f"notepad {md_file}")
        else:
            print(f"❌ Conversion Failed: {result.error_message}")


def entry_point():
    ensure_chromium_installed()
    asyncio.run(process_conversion())


if __name__ == "__main__":
    entry_point()
