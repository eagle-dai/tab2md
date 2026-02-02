import asyncio
import os
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode

# === Configuration ===
DEBUG_PORT_URL = "http://localhost:9222"
OUTPUT_DIR = "exports"

async def get_active_tab_snapshot():
    """
    Connect to the running browser (Chrome/Edge/Brave) via CDP
    and capture the DOM of the active tab.
    """
    try:
        async with async_playwright() as p:
            try:
                # 尝试连接到调试端口
                browser = await p.chromium.connect_over_cdp(DEBUG_PORT_URL)
            except Exception:
                print(f"❌ Connection Failed: Could not connect to {DEBUG_PORT_URL}")
                print("⚠️  Ensure your browser is started with: --remote-debugging-port=9222")
                return None, None

            if not browser.contexts:
                print("❌ No browser context found.")
                await browser.disconnect()
                return None, None
            
            # 获取当前上下文
            ctx = browser.contexts[0]
            
            # 智能寻找激活的页面
            # 排除 devtools 和空白页
            target_page = None
            for page in ctx.pages:
                if page.url != "about:blank" and not page.url.startswith("devtools://"):
                    target_page = page 
                    break 
            
            if not target_page:
                print("❌ No active web page found.")
                await browser.disconnect()
                return None, None

            title = await target_page.title()
            print(f"🔗 Targeted Tab: {title}")
            print(f"🔗 URL: {target_page.url}")
            
            # 抓取完整渲染后的 HTML
            content = await target_page.content()
            url = target_page.url
            
            await browser.disconnect()
            return url, content

    except Exception as e:
        print(f"🔥 Error during snapshot: {e}")
        return None, None

def inject_base_tag(html: str, url: str) -> str:
    """
    Inject <base> tag to fix relative links in local files.
    """
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
    local_file_uri = temp_file.as_uri()

    print("🚀 Running extraction engine (Crawl4AI)...")

    # 3. Configure Extraction
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        magic=True,  # 核心智能去噪
        word_count_threshold=5,
        # 通用去噪标签
        excluded_tags=["nav", "footer", "aside", "script", "style", "iframe", "form", "noscript", "svg"],
    )

    # 4. Run Conversion
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=local_file_uri, config=run_cfg)

        if result.success:
            # Generate Safe Filename
            domain = url.split('//')[-1].split('/')[0]
            slug = re.sub(r'[^a-zA-Z0-9]', '_', url.split('//')[-1])
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
    asyncio.run(process_conversion())

if __name__ == "__main__":
    entry_point()
