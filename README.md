# tab2md

**Tab to Markdown.**

A minimal utility that connects to your open browser window, captures the active tab (including logged-in content, SPAs), and converts it into clean Markdown for LLMs.

Powered by `Crawl4AI` & `Playwright`.

## Prerequisites

1.  **Browser:** Chrome, Edge, Brave, or any Chromium-based browser.
2.  **Environment:** Python 3.9+ with `uv` installed.

## Quick Start

1.  **Install & Sync:**

    ```bash
    git clone <repo> tab2md
    cd tab2md
    uv sync
    uv run playwright install chromium
    ```

2.  **Launch Browser (Debug Mode):**
    Close all browser instances first. Then run:

    _Windows (Run dialog Win+R):_

    ```cmd
    chrome.exe --remote-debugging-port=9222
    # OR
    msedge.exe --remote-debugging-port=9222
    ```

3.  **Run:**
    Navigate to the page you want to capture, then:
    ```bash
    uv run tab2md
    ```

## Output

Files are saved in the `./exports` folder.
