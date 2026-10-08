#!/usr/bin/env python3
"""
泰国政策监控页面后处理脚本 v3.0
应用统一设计规范：蓝色配色、底部导航、访客统计
移除浮动按钮(fab-stack)、反馈弹窗(feedback)、主题切换
仅保留浅色主题
每次日更后调用此脚本，确保设计不被覆盖

v3.0 改动：
- 不再注入 fab-stack、feedback modal、theme toggle
- 移除源文件中的 dark mode CSS 和 JS
- 仅保留底部导航栏
"""
import sys
import re


def remove_element_by_class(html, class_name, tag='div'):
    """移除指定 class 的完整元素（含嵌套子元素），按标签深度精确匹配。"""
    marker = f'<{tag} class="{class_name}"'
    while True:
        start = html.find(marker)
        if start < 0:
            break
        gt = html.find('>', start)
        if gt < 0:
            break
        depth = 1
        i = gt + 1
        while i < len(html) and depth > 0:
            if html[i] == '<':
                if html[i:i+2+len(tag)] == f'</{tag}':
                    close_end = html.find('>', i)
                    if close_end < 0:
                        break
                    depth -= 1
                    if depth == 0:
                        end = close_end + 1
                        comment_start = html.rfind('<!--', 0, start)
                        if comment_start >= 0 and start - comment_start < 100:
                            start = comment_start
                        html = html[:start] + html[end:]
                        break
                    i = close_end + 1
                elif html[i:i+1+len(tag)] == f'<{tag}' and html[i+1+len(tag)] in (' ', '>', '\n', '\r', '\t'):
                    close_end = html.find('>', i)
                    if close_end < 0:
                        break
                    depth += 1
                    i = close_end + 1
                else:
                    i += 1
            else:
                i += 1
        else:
            break
    return html


def remove_nav_by_class(html, class_name):
    """移除 <nav class="...">...</nav> 元素"""
    marker = f'<nav class="{class_name}"'
    while True:
        start = html.find(marker)
        if start < 0:
            break
        end = html.find('</nav>', start)
        if end < 0:
            break
        end += len('</nav>')
        comment_start = html.rfind('<!--', 0, start)
        if comment_start >= 0 and start - comment_start < 100:
            start = comment_start
        html = html[:start] + html[end:]
    return html


def remove_old_injections(html):
    """移除已注入的 fab-stack / feedback-overlay / bottom-nav（无论在哪一层），按标签深度精确匹配。"""
    html = remove_element_by_class(html, 'fab-stack')
    html = remove_element_by_class(html, 'feedback-overlay')
    html = remove_nav_by_class(html, 'bottom-nav')
    # 清理残留注释
    html = re.sub(r'<!--\s*=+\s*-->\s*<!--\s*FLOATING BUTTONS.*?-->\s*', '', html, flags=re.DOTALL)
    html = re.sub(r'<!--\s*Feedback Modal\s*-->\s*', '', html, flags=re.DOTALL)
    html = re.sub(r'<!--\s*Bottom Navigation v2\s*-->\s*', '', html, flags=re.DOTALL)
    return html


def close_unclosed_divs(html):
    """在 </body> 前补充缺失的 </div> 闭合标签"""
    body_end = html.rfind('</body>')
    if body_end < 0:
        return html
    body_start = html[:body_end].rfind('<body')
    if body_start < 0:
        return html
    segment = html[body_start:body_end]
    opens = len(re.findall(r'<div[\s>]', segment))
    closes = len(re.findall(r'</div>', segment))
    unclosed = opens - closes
    if unclosed > 0:
        closing = '\n'.join(['</div>'] * unclosed)
        html = html[:body_end] + closing + '\n' + html[body_end:]
        print(f"  闭合了 {unclosed} 个未关闭的 </div>")
    return html


def remove_old_bottom_nav_css(html):
    """移除旧版 bottom-nav CSS（幂等）"""
    html = re.sub(
        r'/\* ── Bottom Navigation v2 ── \*/.*?@media \(min-width: 768px\) \{[^}]*\.bottom-nav[^}]*\{[^}]*\}[^}]*\}\s*',
        '', html, flags=re.DOTALL)
    return html


# 仅浅色主题的底部导航 CSS
BOTTOM_NAV_CSS = """
/* ── Bottom Navigation v2 ── */
.bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: #ffffff; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-around; padding: 8px 0; padding-bottom: max(8px, env(safe-area-inset-bottom)); z-index: 1000; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); }
.nav-item { display: flex; flex-direction: column; align-items: center; gap: 4px; text-decoration: none; color: #64748b; font-size: 0.65rem; font-weight: 500; padding: 4px 12px; border-radius: 12px; transition: color 0.2s, background 0.2s; }
.nav-item.active { color: #3b82f6; background: rgba(59,130,246,0.12); }
.nav-icon { font-size: 1.2rem; }
@media (min-width: 768px) { .bottom-nav { max-width: 430px; left: 50%; transform: translateX(-50%); } }
"""

# 仅注入底部导航 HTML（无 fab-stack、无 feedback、无 theme toggle）
BOTTOM_NAV_HTML = """<!-- Bottom Navigation v2 -->
<nav class="bottom-nav">
    <a href="/" class="nav-item"><span class="nav-icon">🏠</span><span>首页</span></a>
    <a href="/payment-intel/" class="nav-item"><span class="nav-icon">💳</span><span>支付</span></a>
    <a href="/policy-monitor/" class="nav-item active"><span class="nav-icon">🛡️</span><span>政策</span></a>
    <a href="/stock-dash/" class="nav-item"><span class="nav-icon">📈</span><span>股市</span></a>
</nav>"""


def apply_design(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. 删除 kbd-hint
    html = re.sub(r'<!-- Keyboard shortcut hint -->\s*<div class="kbd-hint"[^>]*>[^<]*</div>\s*', '', html)

    # 2. 移除旧注入组件（无论嵌套在哪一层）
    html = remove_old_injections(html)
    # 也移除旧版独立主题切换脚本
    html = re.sub(r'<script>\s*// Theme toggle.*?</script>', '', html, flags=re.DOTALL)

    # 3. 移除源文件中的 dark/light mode 相关 CSS（单条规则匹配，不跨块）
    html = re.sub(r'\[data-theme="dark"\][^{]*\{[^}]*\}\s*', '', html)
    html = re.sub(r"\[data-theme=.dark.\][^{]*\{[^}]*\}\s*", '', html)
    html = re.sub(r'\[data-theme="light"\][^{]*\{[^}]*\}\s*', '', html)
    html = re.sub(r"\[data-theme=.light.\][^{]*\{[^}]*\}\s*", '', html)
    # 移除 CSS 注释标记 —— 使用 [^*]* 防止跨注释块匹配，保护 :root 等关键块
    html = re.sub(r'/\*[^*]*[Tt]heme[^*]*\*/\s*', '', html)
    html = re.sub(r'/\*[^*]*[Ff]loating[^*]*\*/\s*', '', html)
    html = re.sub(r'/\*[^*]*[Ff]eedback[^*]*\*/\s*', '', html)
    html = re.sub(r'/\*[^*]*[Dd]ark[^*]*\*/\s*', '', html)
    # 移除 fab 相关 CSS 规则
    html = re.sub(r'\.fab-theme\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.fab-theme:active\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.fab-feedback\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.fab-feedback\s+\.fab-badge\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.fab-portal\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.fab-portal:active\s*\{[^}]*\}\s*', '', html)
    # 移除 fab-stack CSS（包括 @media 中的）
    html = re.sub(r'\.fab-stack\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'@media[^{]*\{\s*\.fab-stack\s*\{[^}]*\}\s*\}\s*', '', html)
    # 移除 fab 基础 CSS（.fab { ... } 和 .fab:active）
    html = re.sub(r'\.fab\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.fab:active\s*\{[^}]*\}\s*', '', html)
    # 移除 fab-back 和 panel-global ~ .fab-stack 规则
    html = re.sub(r'\.fab-back\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.fab-back\.visible\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.panel-global\s*~\s*\.fab-stack[^{]*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.panel-app\s*~\s*\.fab-stack[^{]*\{[^}]*\}\s*', '', html)
    # 移除 feedback-overlay CSS
    html = re.sub(r'\.feedback-overlay\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.feedback-overlay\.visible\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'\.feedback-overlay\.visible\s+\.feedback-modal\s*\{[^}]*\}\s*', '', html)

    # 6. 对主脚本块进行外科手术式清理：只移除 theme/feedback/back-to-top/scroll 段落，保留 module switching 和 filter 逻辑
    _s_tag = html.find('<script>')
    if _s_tag >= 0:
        _s_content_start = html.find('\n', _s_tag) + 1
        _s_end = html.find('</script>', _s_tag)
        if _s_content_start > 0 and _s_end > _s_content_start:
            _main_script = html[_s_content_start:_s_end]

            # 定义要移除的段落标记（从 → 到）
            _sections_to_remove = [
                ('// ── Back to top', '// ── Theme Toggle'),
                ('// ── Theme Toggle', '// ── Feedback Modal'),
                ('// ── Feedback Modal', "// Bind both modules"),
                ('// ── Scroll: passive', '// ── Stat number bump'),
            ]
            for _from_marker, _to_marker in _sections_to_remove:
                _from = _main_script.find(_from_marker)
                _to = _main_script.find(_to_marker)
                if _from >= 0 and _to > _from:
                    _main_script = _main_script[:_from] + _main_script[_to:]

            # 移除 keyboard shortcuts 中的 feedback overlay 引用
            _fb_ref = """            // Close feedback modal
            var fbOverlay = document.getElementById('feedbackOverlay');
            if (fbOverlay && fbOverlay.classList.contains('visible')) {
                fbOverlay.classList.remove('visible');
                return;
            }
"""
            if _fb_ref in _main_script:
                _main_script = _main_script.replace(_fb_ref, '')

            # 回写到 HTML
            html = html[:_s_content_start] + _main_script + html[_s_end:]

    # 移除 fab-theme 按钮 HTML
    html = re.sub(r'<button[^>]*class="fab fab-theme"[^>]*>[^<]*</button>\s*', '', html)

    # 7. 修复源文件中的 HTML 结构错误
    # 7a. 修复 global-timeline 缺少闭合引号: class="timeline global-timeline> → class="timeline global-timeline">
    html = html.replace(
        'class="timeline global-timeline>',
        'class="timeline global-timeline">'
    )
    # 7b. 移除 module-app 中 timeline 和 collapsible-content 上的 collapsed class，确保内容可见
    html = html.replace(
        'class="timeline app-timeline collapsed"',
        'class="timeline app-timeline"'
    )
    html = html.replace(
        'class="collapsible-content collapsed"',
        'class="collapsible-content"'
    )

    # 8. 清理旧 bottom-nav CSS 并注入新版（仅浅色）
    html = remove_old_bottom_nav_css(html)
    html = html.replace('</style>', BOTTOM_NAV_CSS + '\n</style>', 1)

    # 9. 闭合未关闭的 div 标签
    html = close_unclosed_divs(html)

    # 10. 在 </body> 直下级仅注入 bottom-nav（无 fab-stack、无 feedback、无 theme）
    html = html.replace('</body>', '\n' + BOTTOM_NAV_HTML + '\n\n</body>', 1)

    # 11. body padding-bottom
    if 'padding-bottom: 70px' not in html and 'padding-bottom:70px' not in html:
        html = html.replace(
            'overscroll-behavior-y: contain;',
            'padding-bottom: 70px;\n    overscroll-behavior-y: contain;', 1)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Design applied to {html_path}")
    return True

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '/Coze/Drive/Blake的Token工作间/github-pages-staging/policy-monitor/index.html'
    apply_design(path)
