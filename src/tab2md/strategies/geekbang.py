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
            // 1. 处理代码块
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

            // 2. 智能列表修复 v4
            (function() {
                // 触发词：你将能够、主要包括、学习目标等
                const triggers = ['你将能够：', '你将能够:', '主要包括：', '通过本节课的学习'];
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
                
                let node;
                let activeTrigger = false; 
                let itemsCount = 0;
                
                while(node = walker.nextNode()) {
                    const text = node.nodeValue.trim();
                    if (!text) continue;
                    
                    // A. 发现路标：开启列表模式
                    if (triggers.some(t => text.includes(t))) {
                        activeTrigger = true;
                        itemsCount = 0;
                        continue; 
                    }
                    
                    // B. 处于列表区域中，进行智能判断
                    if (activeTrigger) {
                        // 1. 找到承载文本的容器
                        let container = node.parentElement;
                        // 跳过行内元素，找到真正的“行”容器
                        while (container && ['SPAN', 'STRONG', 'B', 'EM', 'I', 'A', 'CODE'].includes(container.tagName)) {
                            container = container.parentElement;
                        }
                        if (!container || container === document.body) continue;

                        // 2. [关键修改] 刹车机制：遇到标题或长段落，立即结束列表模式
                        const isHeader = ['H1','H2','H3','H4'].includes(container.tagName);
                        const isLongText = text.length > 80; // 阈值：超过80字通常是正文
                        const isCode = container.closest('pre');

                        if (isHeader || isLongText || isCode) {
                            activeTrigger = false; // 关闭开关
                            continue; // 这一行作为普通正文处理
                        }

                        // 3. 避免重复处理
                        if (!container.getAttribute('data-fix-bullet')) {
                            // 排除无意义的短语
                            if (text.startsWith('你好') || text.includes('欢迎来到')) continue;

                            // 4. [修改] 添加圆点
                            if (!text.match(/^[-*]|\d+\./)) {
                                const bullet = document.createElement('span');
                                bullet.textContent = '- '; 
                                bullet.style.fontWeight = 'bold';
                                if (container.firstChild) {
                                    container.insertBefore(bullet, container.firstChild);
                                } else {
                                    container.appendChild(bullet);
                                }
                            }
                            
                            // 5. [关键修改] 强制换行隔离！
                            // 极客时间很多 div 是紧挨着的，Markdownify 容易把它们拼成一行
                            // 我们给它加一个不可见的块级分隔，或者直接追加 br
                            const br = document.createElement('br');
                            container.appendChild(br);
                            
                            // 或者强制设为块级显示
                            container.style.display = 'block';
                            container.style.marginBottom = '10px'; // 视觉上分开，辅助转换器识别

                            // 标记并计数
                            container.setAttribute('data-fix-bullet', 'true');
                            itemsCount++;
                            
                            // 安全阀：最多修 6 行
                            if (itemsCount >= 6) activeTrigger = false;
                        }
                    }
                }
            })();
            
            // 3. 全局段落粘连修复 (针对正文)
            // 如果所有正文都粘连，说明 div 之间没有空行。
            // 我们可以给所有 slate-paragraph 强制加下边距或换行
            document.querySelectorAll('div[data-slate-type="paragraph"]').forEach(p => {
                p.appendChild(document.createElement('br'));
                p.appendChild(document.createTextNode('\\n')); // 显式添加换行符文本
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
