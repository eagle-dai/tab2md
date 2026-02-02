from abc import ABC, abstractmethod
from pathlib import Path
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig


class BaseStrategy(ABC):
    """
    所有网页转换策略的基类。
    """

    def inject_base_tag(self, html: str, url: str) -> str:
        """注入 <base> 标签以修复相对链接 (Common Utility)。"""
        base_tag = f'<base href="{url}">'
        if "<head>" in html:
            return html.replace("<head>", f"<head>\n{base_tag}", 1)
        return f"<html><head>{base_tag}</head>" + html

    async def execute(self, url: str, raw_html: str) -> str:
        """
        执行转换逻辑。
        1. 处理 HTML (注入 base tag)
        2. 保存临时文件
        3. 调用 Crawl4AI 进行提取
        """
        # 1. 预处理
        html_with_base = self.inject_base_tag(raw_html, url)
        temp_file = Path("temp_snapshot.html").resolve()
        temp_file.write_text(html_with_base, encoding="utf-8")

        # Windows 路径兼容性
        local_file_uri = f"file://{temp_file.as_posix()}"

        # 2. 获取配置 (由子类实现)
        browser_cfg = BrowserConfig(headless=True, verbose=False)
        run_cfg = self.get_run_config()

        print(f"🚀 正在使用策略 [{self.__class__.__name__}] 运行提取引擎...")

        # 3. 运行提取
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=local_file_uri, config=run_cfg)

            # 清理临时文件 (可选)
            # try: temp_file.unlink()
            # except: pass

            if result.success:
                return result.markdown
            else:
                raise Exception(f"转换失败: {result.error_message}")

    @abstractmethod
    def get_run_config(self) -> CrawlerRunConfig:
        """
        子类必须实现此方法，返回针对该类型网页的 Crawl4AI 配置。
        """
        pass

    @classmethod
    def match(cls, url: str) -> bool:
        """
        判断该策略是否适用于给定的 URL。
        默认返回 False，需要在子类中覆盖逻辑 (除了 BasicStrategy)。
        """
        return False
