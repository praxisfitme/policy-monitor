#!/usr/bin/env python3
"""
跨境支付情报页面后处理脚本 v5.0
应用统一设计规范：橙色配色、白底浅色主题、底部导航、访客统计
移除浮动按钮(fab-stack)、反馈弹窗(feedback)、暗色主题、主题切换
每次日更后调用此脚本，确保设计不被覆盖

v5.0 改动：
- 新增暗色→白底转换：替换 :root CSS 变量和内联暗色背景
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


def convert_dark_to_light(html):
    """将暗色主题转换为白底浅色主题"""
    
    # ── :root CSS 变量替换 ──
    # 背景
    html = html.replace('--bg:#070A14', '--bg:#ffffff')
    html = html.replace('--bg2:#0D1225', '--bg2:#f8fafc')
    # 玻璃效果（暗底上的白色半透明 → 白底上的黑色半透明）
    html = html.replace('--glass:rgba(255,255,255,.06)', '--glass:rgba(0,0,0,.03)')
    html = html.replace('--glass-hover:rgba(255,255,255,.1)', '--glass-hover:rgba(0,0,0,.06)')
    # 边框
    html = html.replace('--border:rgba(255,255,255,.08)', '--border:rgba(0,0,0,.08)')
    html = html.replace('--border-hover:rgba(255,255,255,.15)', '--border-hover:rgba(0,0,0,.15)')
    # 文字（暗底亮字 → 白底暗字）
    html = html.replace('--text:#F7FAFF', '--text:#0f172a')
    html = html.replace('--text2:#9AA7C7', '--text2:#475569')
    html = html.replace('--text3:#6B7A99', '--text3:#94a3b8')
    # 成功色略加深以适应白底
    html = html.replace('--success:#62FAD3', '--success:#10b981')
    
    # ── 内联暗色背景替换（CSS 和 style 属性中的）──
    html = html.replace('rgba(7,10,20', 'rgba(255,255,255')
    html = html.replace('rgba(13,18,37', 'rgba(248,250,252')
    html = html.replace('rgba(15,23,42', 'rgba(241,245,249')  # #0f172a based
    html = html.replace('#070A14', '#ffffff')
    html = html.replace('#0D1225', '#f8fafc')
    
    # ── 渐变背景中的暗色替换 ──
    # body::before 的 radial-gradient
    html = html.replace('rgba(249,115,22,.08)', 'rgba(249,115,22,.04)')
    html = html.replace('rgba(251,146,60,.05)', 'rgba(251,146,60,.03)')
    
    # ── 文字颜色补偿（确保在白底上可读）──
    # header 等深色背景上的白色文字已在变量中处理
    # a:hover 原来变白，现在改为深色
    html = re.sub(r'a:hover\{color:#fff\}', 'a:hover{color:#ea580c}', html)
    
    return html


def apply_design(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # 0. 暗色 → 白底浅色主题转换
    html = convert_dark_to_light(html)
    
    # 1. 颜色替换：紫色 → 橙色
    html = html.replace('#7C5CFF', '#f97316')  # primary
    html = html.replace('#69E7FF', '#fb923c')  # accent
    html = html.replace('#6C4CE6', '#ea580c')  # light primary
    html = html.replace('#0891B2', '#f97316')  # light accent
    html = html.replace('rgba(124,92,255', 'rgba(249,115,22')
    html = html.replace('rgba(105,231,255', 'rgba(251,146,60')
    html = html.replace('rgba(8,145,178', 'rgba(251,146,60')
    
    # 2. 移除 fab-stack 浮动按钮（无论嵌套在哪一层）
    html = remove_element_by_class(html, 'fab-stack')
    
    # 3. 移除 feedback 弹窗
    html = remove_element_by_class(html, 'feedback-overlay')
    
    # 3b. 移除包含 Floating Components / Feedback Modal 的整个 <script> 块
    html = re.sub(
        r'<script>\s*//\s*─+\s*Floating Components.*?</script>',
        '', html, flags=re.DOTALL)
    html = re.sub(
        r'<script>\s*//\s*─+\s*Feedback Modal.*?</script>',
        '', html, flags=re.DOTALL)
    # 移除包含 fab-feedback 或 feedbackOverlay 引用的残留 script 块
    def _remove_script_if(html, keyword):
        while True:
            idx = html.find(keyword)
            if idx < 0:
                break
            s_start = html.rfind('<script', 0, idx)
            s_end = html.find('</script>', idx)
            if s_start < 0 or s_end < 0:
                break
            html = html[:s_start] + html[s_end + len('</script>'):]
        return html
    html = _remove_script_if(html, 'fab-feedback')
    html = _remove_script_if(html, 'feedbackOverlay')
    html = _remove_script_if(html, "getAttribute('data-theme')")
    html = _remove_script_if(html, 'applyTheme')
    
    # 4. 移除所有 [data-theme="dark"] CSS 规则
    html = re.sub(r'\[data-theme="dark"\][^{]*\{[^}]*\}\s*', '', html)
    html = re.sub(r"\[data-theme=.dark.\][^{]*\{[^}]*\}\s*", '', html)
    
    # 5. 移除所有 [data-theme="light"] CSS 规则（不再需要，默认就是浅色）
    html = re.sub(r'\[data-theme="light"\][^{]*\{[^}]*\}\s*', '', html)
    html = re.sub(r"\[data-theme=.light.\][^{]*\{[^}]*\}\s*", '', html)
    
    # 6. 移除 fab 相关 CSS 规则
    for sel in [
        r'\.fab-stack',
        r'\.fab(?![-\w])',
        r'\.fab:active',
        r'\.fab-theme',
        r'\.fab-theme:active',
        r'\.fab-feedback',
        r'\.fab-feedback\s+\.fab-badge',
        r'\.fab-portal',
        r'\.fab-portal:active',
        r'\.fab-back',
        r'\.fab-back\.visible',
        r'\.panel-global\s*~\s*\.fab-stack',
        r'\.panel-app\s*~\s*\.fab-stack',
        r'\.fab-badge',
    ]:
        html = re.sub(sel + r'\s*\{[^}]*\}\s*', '', html)
    
    # 7. 移除 @media 中的 fab-stack 规则
    html = re.sub(r'@media[^{]*\{\s*\.fab-stack\s*\{[^}]*\}\s*\}\s*', '', html)
    
    # 8. 移除 feedback-overlay CSS
    for sel in [
        r'\.feedback-overlay',
        r'\.feedback-overlay\.visible',
        r'\.feedback-overlay\.visible\s+\.feedback-modal',
        r'\.feedback-modal',
        r'\.feedback-modal\s+h3',
        r'\.feedback-modal\s+textarea',
        r'\.feedback-modal\s+\.feedback-hint',
        r'\.feedback-modal\s+\.feedback-note',
        r'\.feedback-actions',
        r'\.feedback-actions\s+button',
        r'\.feedback-btn',
        r'\.feedback-btn-secondary',
        r'\.feedback-btn-close',
        r'\.feedback-close',
        r'\.feedback-type',
        r'\.feedback-type-btn',
        r'\.feedback-hint',
    ]:
        html = re.sub(sel + r'\s*\{[^}]*\}\s*', '', html)
    
    # 9. 移除源文件中的主题切换 JS 代码
    html = re.sub(r'var\s+themeBtn\s*=\s*document\.querySelector\([^)]+\);\s*', '', html)
    html = re.sub(r'function\s+applyTheme\s*\([^)]*\)\s*\{[^}]*\}\s*', '', html, flags=re.DOTALL)
    html = re.sub(r'applyTheme\s*\([^)]*\)\s*;\s*', '', html)
    html = re.sub(r'var\s+currentTheme\s*=\s*[^;]+;\s*', '', html)
    html = re.sub(r'var\s+savedTheme\s*=\s*[^;]+;\s*', '', html)
    html = re.sub(r'var\s+prefersDark\s*=\s*[^;]+;\s*', '', html)
    html = re.sub(r'if\s*\(themeBtn\)\s*\{[^}]*\}\s*', '', html, flags=re.DOTALL)
    html = re.sub(r'<button[^>]*class="fab fab-theme"[^>]*>[^<]*</button>\s*', '', html)
    html = re.sub(r"document\.documentElement\.setAttribute\('data-theme'[^;]*;\s*\n?", '', html)
    html = re.sub(r"document\.documentElement\.removeAttribute\('data-theme'\);\s*\n?", '', html)
    html = re.sub(r"localStorage\.[gs]etItem\(['\"][^'\"]*theme['\"][^)]*\);\s*\n?", '', html)
    # 移除整个 theme toggle IIFE 块
    html = re.sub(
        r'\(function\s*\(\)\s*\{\s*var\s+theme\s*=\s*localStorage.*?apply\(theme\);\s*\}\)\(\);\s*',
        '', html, flags=re.DOTALL)
    # 移除 theme toggle 的 click listener
    html = re.sub(
        r"document\.querySelector\(['\"]\.fab-theme['\"]\)\.addEventListener\('click'.*?\}\);",
        '', html, flags=re.DOTALL)
    
    # 10. 移除 back-to-top 相关代码
    html = re.sub(r'var\s+backBtn\s*=\s*document\.querySelector\([^)]+\);\s*', '', html)
    html = re.sub(r'if\s*\(backBtn\)\s*\{[^}]*\}\s*', '', html, flags=re.DOTALL)
    
    # 11. 移除 CSS 中的注释标记
    html = re.sub(r'/\*\s*─.*?[Tt]heme.*?─\s*\*/\s*', '', html)
    html = re.sub(r'/\*\s*─.*?[Ff]loating.*?─\s*\*/\s*', '', html)
    html = re.sub(r'/\*\s*─.*?[Ff]eedback.*?─\s*\*/\s*', '', html)
    html = re.sub(r'/\*\s*─.*?[Dd]ark.*?─\s*\*/\s*', '', html)
    html = re.sub(r'/\*\s*Dark\s+[Mm]ode.*?\*/\s*', '', html)
    
    # 12. 添加底部导航栏 CSS（如果不存在）
    bottom_nav_css = """
/* ── Bottom Navigation v2 ── */
.bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: #fff; border-top: 1px solid #e5e7eb; display: flex; justify-content: space-around; padding: 8px 0; padding-bottom: max(8px, env(safe-area-inset-bottom)); z-index: 100; }
.nav-item { display: flex; flex-direction: column; align-items: center; gap: 4px; text-decoration: none; color: #64748b; font-size: 0.6rem; font-weight: 500; padding: 4px 12px; border-radius: 12px; transition: color 0.2s, background 0.2s; }
.nav-item.active { color: #f97316; background: rgba(249,115,22,0.12); }
.nav-icon { font-size: 1.2rem; }
@media (min-width: 768px) { body { max-width: 430px; margin: 0 auto; } .bottom-nav { max-width: 430px; left: 50%; transform: translateX(-50%); } }
"""
    if '.bottom-nav' not in html:
        html = html.replace('</style>', bottom_nav_css + '\n</style>')
    
    # 13. 添加底部留白
    if 'padding-bottom:6rem' not in html and 'padding-bottom: 6rem' not in html:
        html = html.replace('padding-bottom:4rem', 'padding-bottom:6rem')
        html = html.replace('padding-bottom: 4rem', 'padding-bottom: 6rem')
    
    # 14. 添加底部导航栏 HTML（如果不存在）
    bottom_nav_html = """
<!-- Bottom Navigation v2 -->
<nav class="bottom-nav">
    <a href="/" class="nav-item"><span class="nav-icon">🏠</span><span>首页</span></a>
    <a href="/payment-intel/" class="nav-item active"><span class="nav-icon">💳</span><span>支付</span></a>
    <a href="/policy-monitor/" class="nav-item"><span class="nav-icon">🛡️</span><span>政策</span></a>
    <a href="/stock-dash/" class="nav-item"><span class="nav-icon">📈</span><span>股市</span></a>
</nav>
"""
    if 'class="bottom-nav"' not in html:
        html = html.replace('</body>', bottom_nav_html + '\n</body>')
    
    # 15. 添加访客统计脚本（如果不存在）
    visitor_scripts = """
<!-- Visitor Tracking v2 (counterapi.com) -->
<script>
(function() {
    var key = 'payment';
    fetch('https://counterapi.com/api/praxisfit.me/view/' + key + '?trackOnly=true').catch(function(){});
    fetch('https://counterapi.com/api/praxisfit.me/view/' + key).then(function(r){return r.json()}).then(function(d){
        var el = document.getElementById('visit-count');
        if(el) el.textContent = d.value || d.count || 0;
    }).catch(function(){});
})();
</script>
"""
    if 'counterapi.com/api/praxisfit.me/view/payment' not in html:
        html = html.replace('</body>', visitor_scripts + '\n</body>')
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # 验证清理结果
    remaining = []
    for term in ['fab-stack', 'fab-theme', 'fab-feedback', 'feedback-overlay', 'data-theme', 'applyTheme', 'themeBtn']:
        count = html.count(term)
        if count > 0:
            remaining.append(f"  {term}: {count}")
    
    # 验证白底
    has_dark_bg = '--bg:#070A14' in html or '--bg: #070A14' in html
    
    print(f"✅ Design applied to {html_path}")
    if remaining:
        print(f"⚠️ 仍有残留:\n" + "\n".join(remaining))
    else:
        print("✅ 所有 fab/feedback/theme 残留已清除")
    if has_dark_bg:
        print("⚠️ 暗色背景仍存在！")
    else:
        print("✅ 已转换为白底浅色主题")
    return True

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '/Coze/Drive/Blake的Token工作间/github-pages-staging/payment-intel/index.html'
    apply_design(path)
