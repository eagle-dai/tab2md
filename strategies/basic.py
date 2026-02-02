from crawl4ai.async_configs import CrawlerRunConfig, CacheMode
from .base import BaseStrategy


class BasicStrategy(BaseStrategy):
    """
    通用兜底策略，适用于未特定优化的网页。
    """

    def get_run_config(self) -> CrawlerRunConfig:
        return CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            magic=True,
            word_count_threshold=5,
            # 通用的排除列表
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

    @classmethod
    def match(cls, url: str) -> bool:
        # BasicStrategy 作为最后的兜底，通常不参与自动匹配，或者总是返回 True (取决于你的路由逻辑)
        return True
