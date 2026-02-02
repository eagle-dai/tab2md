# tab2md

**Tab to Markdown.**

一个极简的网页抓取工具。它连接到你打开的浏览器窗口，捕获当前激活的标签页（包括需登录内容、SPA），并将其转换为 Markdown。

本项目采用**策略模式 (Strategy Pattern)** 构建，支持针对不同网站定制提取逻辑。

## 前置要求 (Prerequisites)

1.  **浏览器:** Chrome, Edge, Brave 或任何 Chromium 内核浏览器。
2.  **环境:** Python 3.9+，已安装 `uv`。

## 快速开始 (Quick Start)

1.  **安装与同步:**

    ```bash
    git clone <repo> tab2md
    cd tab2md
    uv sync
    uv run playwright install chromium
    ```

2.  **启动浏览器 (调试模式):**
    请先完全关闭现有的浏览器实例，然后运行：

    _Windows (运行对话框 Win+R):_

    ```cmd
    chrome.exe --remote-debugging-port=9222
    # 或者
    msedge.exe --remote-debugging-port=9222
    ```

3.  **运行:**
    在浏览器中打开你想抓取的页面，然后运行：
    ```bash
    uv run tab2md
    ```

## 输出 (Output)

转换后的文件将保存在 `./exports` 文件夹中。

---

## 开发指南 (Developer Guide)

本项目结构旨在方便扩展。核心逻辑与特定网页的解析逻辑已分离。

### 项目结构

```text
tab2md/
├── main.py                  # 主入口：负责策略路由与流程编排
├── browser_ops.py           # 浏览器操作层：处理 CDP 连接与快照抓取
└── strategies/              # 策略包：存放网页解析逻辑
    ├── __init__.py
    ├── base.py              # 策略基类 (BaseStrategy)
    ├── basic.py             # 默认兜底策略
    └── wiki.py              # (示例) 针对 Wikipedia 的优化策略
```

### 如何添加新网站支持

如果你需要优化某个特定网站（例如 `example.com`）的提取效果，请遵循以下步骤：

1.  在 `strategies/` 目录下创建一个新文件，例如 `example.com.py`。
2.  继承 `BaseStrategy` 并实现 `get_run_config` 和 `match` 方法。

    ```python
    from .base import BaseStrategy
    from crawl4ai.async_configs import CrawlerRunConfig, CacheMode

    class ExampleStrategy(BaseStrategy):
        @classmethod
        def match(cls, url: str) -> bool:
            return "example.com" in url

        def get_run_config(self) -> CrawlerRunConfig:
            return CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                excluded_tags=["nav", "footer", ".ads-banner"], # 定制排除项
                css_selector="main.content" # 仅提取特定区域
            )
    ```

3.  在 `main.py` 的 `get_strategy_for_url` 函数中注册你的新策略。
