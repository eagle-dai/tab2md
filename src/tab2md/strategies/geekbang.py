from urllib.parse import urlparse
from crawl4ai.async_configs import CrawlerRunConfig
from .basic import BasicStrategy


class GeekbangColumnStrategy(BasicStrategy):
    """
    极客时间专栏文章策略 (适配 Slate.js 编辑器)
    """

    def get_run_config(self) -> CrawlerRunConfig:
        config = super().get_run_config()

        # 1. 放宽字数限制，防止短代码行被误删
        config.word_count_threshold = 1

        # 2. 精准定位正文区域
        # 极客时间新版使用 Slate.js，正文容器通常带有 data-slate-editor="true" 属性
        config.css_selector = "div[data-slate-editor='true']"

        # 3. [关键] 注入 JS 修复代码块
        # 网页原始结构是用 div 模拟代码块，Markdown 转换器无法识别。
        # 我们在提取前，用 JS 将其强制转换为标准的 <pre><code> 标签。
        config.js_code = """
            // 找到所有 Slate 伪装的代码块容器
            const blocks = document.querySelectorAll('div[data-slate-type="pre"]');
            
            blocks.forEach(block => {
                const pre = document.createElement('pre');
                const code = document.createElement('code');
                
                // 尝试提取语言标记 (如 python, java)
                const lang = block.getAttribute('data-code-language');
                if (lang) {
                    code.className = `language-${lang}`;
                }
                
                // 提取所有代码行的文本并拼接
                const lines = [];
                block.querySelectorAll('div[data-slate-type="code-line"]').forEach(line => {
                    // 使用 textContent 获取纯文本，保留缩进
                    lines.push(line.textContent);
                });
                
                // 将代码放入标准标签中
                code.textContent = lines.join('\\n');
                pre.appendChild(code);
                
                // 用标准 <pre> 替换掉原始的 <div>
                block.parentNode.replaceChild(pre, block);
            });
        """

        return config

    @classmethod
    def match(cls, url: str) -> bool:
        try:
            parsed = urlparse(url)
            return "geekbang.org" in parsed.netloc
        except Exception:
            return False
