import asyncio
import re
from pathlib import Path

# 导入自定义模块
from .browser_ops import ensure_chromium_installed, get_active_tab_snapshot
from .strategies.basic import BasicStrategy
# 将来可以在这里导入更多策略，例如: from strategies.wiki import WikiStrategy

OUTPUT_DIR = "exports"


def get_strategy_for_url(url: str):
    """
    简单的策略路由工厂。
    遍历所有已知策略，找到第一个匹配的；如果没找到，返回 BasicStrategy。
    """
    # 注册你的特定策略类 (优先匹配特定策略)
    # known_strategies = [WikiStrategy, CsdnStrategy, ...]
    known_strategies = []

    for strategy_cls in known_strategies:
        if strategy_cls.match(url):
            return strategy_cls()

    return BasicStrategy()


async def process_conversion():
    # 1. 获取快照
    url, raw_html = await get_active_tab_snapshot()
    if not raw_html:
        return

    # 2. 选择策略
    strategy = get_strategy_for_url(url)

    try:
        # 3. 执行转换
        markdown_content = await strategy.execute(url, raw_html)

        # 4. 保存结果
        slug = re.sub(r"[^a-zA-Z0-9]", "_", url.split("//")[-1])
        safe_name = f"{slug[:50]}"

        output_path = Path(OUTPUT_DIR)
        output_path.mkdir(exist_ok=True)

        md_file = output_path / f"{safe_name}.md"
        md_file.write_text(markdown_content, encoding="utf-8")

        print("\n✅ 转换完成!")
        print(f"📂 已保存至: {md_file}")

    except Exception as e:
        print(f"❌ 处理过程中发生错误: {e}")


def entry_point():
    ensure_chromium_installed()
    asyncio.run(process_conversion())


if __name__ == "__main__":
    entry_point()
