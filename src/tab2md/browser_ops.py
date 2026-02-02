import subprocess
import asyncio
import platform
import sys
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


def get_process_titles():
    """
    直接询问操作系统：当前运行的浏览器进程的主窗口标题是什么？
    这直接对应当前激活的 Tab 标题。
    """
    titles = []
    system = platform.system()

    try:
        if system == "Windows":
            # 关键修改：强制 PowerShell 输出 UTF-8，防止中文标题乱码导致匹配失败
            cmd = (
                "$OutputEncoding = [System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
                'Get-Process chrome, msedge, brave, "Arc" -ErrorAction SilentlyContinue | '
                "Where-Object { $_.MainWindowTitle } | "
                "Select-Object -ExpandProperty MainWindowTitle"
            )

            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                encoding="utf-8",  # 配合上面的 UTF-8 命令
            )

            if result.stdout:
                titles = [
                    line.strip() for line in result.stdout.splitlines() if line.strip()
                ]

        elif system == "Darwin":  # macOS 兼容
            script = """
            tell application "System Events"
                set procs to processes whose name is "Microsoft Edge" or name is "Google Chrome" or name is "Brave Browser"
                set titleList to {}
                repeat with proc in procs
                    try
                        set titleList to titleList & (name of every window of proc)
                    end try
                end repeat
                return titleList
            end tell
            """
            result = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True
            )
            if result.stdout:
                titles = [t.strip() for t in result.stdout.strip().split(",")]

    except Exception as e:
        print(f"⚠️  获取系统窗口标题失败: {e}")

    return titles


async def get_active_tab_snapshot():
    try:
        async with async_playwright() as p:
            # 1. 连接浏览器 CDP
            try:
                browser = await p.chromium.connect_over_cdp(DEBUG_PORT_URL)
            except Exception:
                print(
                    f"❌ 无法连接到浏览器。请确认已运行: chrome/msedge --remote-debugging-port=9222"
                )
                return None, None

            if not browser.contexts:
                return None, None
            pages = browser.contexts[0].pages
            if not pages:
                return None, None

            # 2. 获取操作系统层面的进程标题
            os_process_titles = get_process_titles()

            # 调试信息：打印系统识别到的标题，方便排查
            if not os_process_titles:
                print("⚠️  未能获取到任何系统窗口标题 (可能权限不足或无窗口)。")
            else:
                # 仅打印前3个避免刷屏
                print(f"🪟 系统检测到的激活窗口标题: {os_process_titles[:3]}...")

            print(f"🔍 正在扫描 {len(pages)} 个标签页进行匹配...")

            target_page = None

            # 3. 核心逻辑：比对 Playwright 的 Tab 标题 和 OS 的进程标题
            # 倒序遍历 (reversed)，优先检查最新的标签页
            for page in reversed(pages):
                try:
                    p_title = await page.title()
                    p_url = page.url

                    if not p_title or "devtools://" in p_url:
                        continue

                    # 匹配逻辑：检查 Tab 标题是否包含在某个 OS 窗口标题中
                    # 例如：Tab="02 | 强化学习"  vs  OS="02 | 强化学习 - Microsoft Edge"
                    for os_title in os_process_titles:
                        # 使用宽松的包含匹配，并忽略大小写
                        if p_title.lower() in os_title.lower():
                            print(
                                f"✅ 命中匹配!\n   Tab标题: {p_title}\n   OS 标题: {os_title}"
                            )
                            target_page = page
                            break

                    if target_page:
                        break
                except:
                    continue

            # 4. 兜底逻辑
            if not target_page:
                print("⚠️  未找到标题完全匹配的页面，尝试使用最新的有效标签页作为兜底。")
                valid_pages = [
                    p
                    for p in pages
                    if "devtools://" not in p.url and p.url != "about:blank"
                ]
                if valid_pages:
                    target_page = valid_pages[-1]
                    t = await target_page.title()
                    print(f"👉 兜底选择: {t}")

            if not target_page:
                print("❌ 无法锁定任何有效页面。")
                return None, None

            # 5. 输出结果
            final_title = await target_page.title()
            final_url = target_page.url
            print(f"🚀 最终锁定: {final_title}")
            print(f"🔗 URL: {final_url}")

            content = await target_page.content()
            await browser.close()
            return final_url, content

    except Exception as e:
        print(f"🔥 运行错误: {e}")
        return None, None
