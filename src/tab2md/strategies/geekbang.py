from urllib.parse import urlparse

from .basic import BasicStrategy


class GeekbangColumnStrategy(BasicStrategy):
    """
    极客邦专栏文章策略。
    复用通用基础实现，仅提供 URL 匹配逻辑。
    """

    @classmethod
    def match(cls, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc != "time.geekbang.org":
            return False
        return parsed.path.startswith("/column/article/")
