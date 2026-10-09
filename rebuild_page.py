#!/usr/bin/env python3
"""
政策监控页面重建脚本 v1.0

从日更生成的源 HTML 中提取三个模块（TH/全球/APP）的数据，
用干净的 CSS + JS 重新构建完整页面。

用法：
  python3 rebuild_page.py [source_path] [output_path]

默认：
  source = policy-monitor-github/index.html (日更源文件)
  output = github-pages-staging/policy-monitor/index.html (部署文件)
"""

import sys
import re
import os


def simple_clean_collapsed(html):
    """移除 class 属性中的 collapsed"""
    def replacer(m):
        classes = m.group(1)
        classes = re.sub(r'\s*collapsed\b', '', classes).strip()
        return f'class="{classes}"'
    return re.sub(r'class="([^"]*collapsed[^"]*)"', replacer, html)


def fix_broken_quotes(html):
    """修复 class 属性缺少闭合引号（如 class="xxx> → class="xxx">）"""
    # [^"<>]* 确保不越过 > 或 < 边界
    return re.sub(r'class="([^"<>]*)>', r'class="\1">', html)


def fix_unclosed_divs(html):
    """修复未闭合的 div 标签：在末尾补齐缺少的 </div>"""
    opens = len(re.findall(r'<div[\s>]', html))
    closes = len(re.findall(r'</div>', html))
    diff = opens - closes
    if diff > 0:
        # 在末尾补齐
        html = html + '\n' + ('</div>\n' * diff)
    return html


def extract_module_sections(source):
    """用注释边界提取三个模块的原始 HTML"""
    m1 = source.find('<!--  MODULE 1:')
    m2 = source.find('<!--  MODULE 2:')
    m3 = source.find('<!--  MODULE 3:')
    
    # 找到 JAVASCRIPT 注释或 <script> 标签
    js_marker = source.find('<!--  JAVASCRIPT')
    if js_marker < 0:
        js_marker = source.find('<script>')
    
    sections = {}
    
    # Module 1: from first module div to MODULE 2 comment
    m1_div = source.find('<div', m1)
    if m1_div >= 0 and m2 > m1_div:
        sections['module-thai'] = source[m1_div:m2].rstrip()
    
    # Module 2: from second module div to MODULE 3 comment
    m2_div = source.find('<div', m2)
    if m2_div >= 0 and m3 > m2_div:
        sections['module-global'] = source[m2_div:m3].rstrip()
    
    # Module 3: from third module div to JS marker
    m3_div = source.find('<div', m3)
    if m3_div >= 0 and js_marker > m3_div:
        sections['module-app'] = source[m3_div:js_marker].rstrip()
    
    return sections


def extract_head_meta(source):
    """提取 head 中的 title 和 meta/link 标签"""
    head_start = source.find('<head>')
    head_end = source.find('</head>')
    if head_start < 0 or head_end < 0:
        return '政策监控面板', '', ''
    
    head = source[head_start:head_end]
    
    title_m = re.search(r'<title>(.*?)</title>', head)
    title = title_m.group(1) if title_m else '政策监控面板'
    
    return title


# ─── 干净 CSS ───
CLEAN_CSS = r"""
/* ── Reset & Base ── */
* { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; -webkit-touch-callout: none; }
:root {
    --primary: #2563eb; --primary-dark: #1e3a8a; --primary-light: #bfdbfe; --primary-lighter: #eff6ff;
    --accent: #7c3aed; --accent-dark: #581c87; --accent-light: #c4b5fd; --accent-lighter: #f5f3ff;
    --bg: #f8fafc; --bg-secondary: #f1f5f9; --card: #ffffff;
    --text: #0f172a; --text-secondary: #64748b; --text-tertiary: #94a3b8;
    --border: #e2e8f0; --border-light: #f1f5f9;
    --danger: #dc2626; --danger-bg: #fef2f2; --danger-text: #991b1b;
    --warning: #ea580c; --warning-bg: #fff7ed; --warning-text: #9a3412;
    --success: #16a34a; --success-bg: #f0fdf4; --success-text: #166534;
    --info: #2563eb; --info-bg: #eff6ff;
    --shadow-xs: 0 1px 2px rgba(0,0,0,0.03);
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
    --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.04);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
    --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px;
    --max-width: 920px;
    --safe-top: env(safe-area-inset-top, 0px); --safe-bottom: env(safe-area-inset-bottom, 0px);
    --t: 0.2s ease;
}
html { font-size: 16px; scroll-behavior: smooth; -webkit-text-size-adjust: 100%; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg); color: var(--text); line-height: 1.6;
    overscroll-behavior-y: contain; padding-bottom: 70px;
    -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;
}

/* Module Nav */
.module-nav { display: flex; gap: 0; background: var(--card); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; box-shadow: var(--shadow-sm); padding-top: var(--safe-top); }
.module-tab { flex: 1; text-align: center; padding: 14px 12px; font-size: 0.8125rem; font-weight: 600; cursor: pointer; color: var(--text-secondary); border-bottom: 3px solid transparent; transition: var(--t); background: transparent; border-top: none; border-left: none; border-right: none; min-height: 48px; display: flex; align-items: center; justify-content: center; user-select: none; }
.module-tab:active { background: var(--bg-secondary); }
.module-tab.active { color: var(--primary); border-bottom-color: var(--primary); background: var(--primary-lighter); }
.module-tab.global.active { color: var(--accent); border-bottom-color: var(--accent); background: var(--accent-lighter); }
.module-tab.app.active { color: #ea580c; border-bottom-color: #ea580c; background: #fff7ed; }

/* Module Panel */
.module-panel { display: none; }
.module-panel.active { display: block; animation: panelFadeIn 0.3s ease forwards; }
@keyframes panelFadeIn { from { opacity: 0; } to { opacity: 1; } }

/* Header */
.header { padding: 10px 20px; border-radius: 0 0 var(--radius-lg) var(--radius-lg); color: white; cursor: pointer; box-shadow: 0 4px 15px rgba(37,99,235,0.10); background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); transition: padding 0.3s, box-shadow 0.3s; }
.header.global { background: linear-gradient(135deg, #581c87 0%, #7c3aed 100%); box-shadow: 0 4px 15px rgba(124,58,237,0.10); }
.header.app { background: linear-gradient(135deg, #92400e 0%, #ea580c 100%); box-shadow: 0 4px 15px rgba(234,88,12,0.12); }
.header .header-inner { display: flex; align-items: center; gap: 10px; user-select: none; min-height: 44px; }
.header .header-inner h1 { font-size: 1rem; font-weight: 700; margin: 0; flex: 1; line-height: 1.4; }
.header .header-inner .toggle-arrow { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; font-size: 0.875rem; opacity: 0.8; transition: transform 0.3s; flex-shrink: 0; }
.header.expanded .header-inner .toggle-arrow { transform: rotate(180deg); }
.header .header-body { max-height: 0; overflow: hidden; transition: max-height 0.35s ease, opacity 0.25s ease, margin 0.3s; opacity: 0; }
.header.expanded .header-body { max-height: 50000px; opacity: 1; }
.header .subtitle { font-size: 0.875rem; opacity: 0.92; line-height: 1.7; }
.header .meta { margin-top: 12px; font-size: 0.8125rem; opacity: 0.85; display: flex; gap: 20px; flex-wrap: wrap; }
.header.expanded { padding: 16px 20px; box-shadow: var(--shadow-lg); }

/* Container */
.container { max-width: var(--max-width); margin: 0 auto; padding: 20px 16px; padding-bottom: calc(24px + var(--safe-bottom)); }

/* Sub Tabs */
.tabs { display: flex; gap: 8px; margin-bottom: 16px; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; padding-bottom: 2px; }
.tabs::-webkit-scrollbar { display: none; }
.tab { padding: 10px 16px; border-radius: 100px; font-size: 0.8125rem; font-weight: 600; cursor: pointer; background: var(--card); color: var(--text-secondary); border: 1px solid var(--border); transition: var(--t); white-space: nowrap; min-height: 40px; display: flex; align-items: center; user-select: none; }
.tab:active { transform: scale(0.96); }
.tab:hover { background: var(--primary-lighter); border-color: var(--primary-light); }
.tab.active { background: var(--primary); color: white; border-color: var(--primary); box-shadow: 0 2px 8px rgba(37,99,235,0.22); }
.panel-global .tab:hover { background: var(--accent-lighter); border-color: var(--accent-light); }
.panel-global .tab.active { background: var(--accent); color: white; border-color: var(--accent); box-shadow: 0 2px 8px rgba(124,58,237,0.22); }
.panel-app .tab:hover { background: #fff7ed; border-color: #fed7aa; }
.panel-app .tab.active { background: #ea580c; color: white; border-color: #ea580c; box-shadow: 0 2px 8px rgba(234,88,12,0.22); }

/* Stats */
.stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
.stat-card { background: var(--card); border-radius: var(--radius-md); padding: 14px 12px; text-align: center; box-shadow: var(--shadow-xs); border: 1px solid var(--border-light); transition: var(--t); }
.stat-card:hover { transform: translateY(-1px); box-shadow: var(--shadow-sm); }
.stat-card .number { font-size: 1.375rem; font-weight: 700; line-height: 1.2; }
.stat-card .label { font-size: 0.6875rem; color: var(--text-secondary); margin-top: 4px; }
.stat-card.info .number { color: var(--info); }
.stat-card.high .number { color: var(--danger); }
.stat-card.medium .number { color: var(--warning); }
.stat-card.low .number { color: var(--text-secondary); }
.stat-card.warn .number { color: var(--warning); }
.stat-card.warn-orange .number { color: #ea580c; }

/* Filters */
.filters { background: var(--card); border-radius: var(--radius-md); margin-bottom: 16px; box-shadow: var(--shadow-xs); border: 1px solid var(--border-light); }
.filters-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; cursor: pointer; font-size: 0.875rem; font-weight: 600; color: var(--text-secondary); border-bottom: 1px solid var(--border-light); }
.filters-header .arrow { transition: transform 0.3s; font-size: 0.75rem; }
.filters.expanded .filters-header .arrow { transform: rotate(180deg); }
.filters-body { max-height: 0; overflow-y: hidden; overflow-x: visible; padding: 0 16px; transition: max-height 0.35s ease, padding 0.3s ease; }
.filters.expanded .filters-body { max-height: 2000px; padding: 16px; overflow-y: visible; }
.filter-row { display: flex; align-items: flex-start; margin-bottom: 12px; flex-wrap: wrap; gap: 8px; }
.filter-row:last-child { margin-bottom: 0; }
.filter-label { font-size: 0.75rem; font-weight: 600; color: var(--text-secondary); min-width: 64px; padding-top: 6px; flex-shrink: 0; }
.filter-options { display: flex; flex-wrap: wrap; gap: 6px; flex: 1; }
.chip { padding: 5px 12px; border-radius: 100px; font-size: 0.75rem; font-weight: 500; cursor: pointer; background: var(--bg-secondary); color: var(--text-secondary); border: 1px solid transparent; transition: var(--t); white-space: nowrap; user-select: none; }
.chip:active { transform: scale(0.95); }
.chip.active { background: var(--primary); color: white; border-color: var(--primary); }
.panel-global .chip.active { background: var(--accent); border-color: var(--accent); }
.panel-app .chip.active { background: #ea580c; border-color: #ea580c; }

/* Search & Sort */
.search-box { margin-bottom: 12px; }
.search-box input { width: 100%; padding: 10px 16px; border-radius: 100px; border: 1px solid var(--border); background: var(--card); font-size: 0.875rem; color: var(--text); outline: none; transition: var(--t); }
.search-box input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(37,99,235,0.08); }
.sort-row { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.sort-row label { font-size: 0.75rem; color: var(--text-secondary); font-weight: 600; white-space: nowrap; }
.sort-select { padding: 6px 12px; border-radius: var(--radius-sm); border: 1px solid var(--border); background: var(--card); font-size: 0.75rem; color: var(--text); outline: none; cursor: pointer; }
.expand-btn { padding: 6px 14px; border-radius: 100px; border: 1px solid var(--border); background: var(--card); font-size: 0.75rem; color: var(--text-secondary); cursor: pointer; margin-left: auto; }

/* Timeline */
.timeline { position: relative; }
.month-section { margin-bottom: 24px; }
.month-section.hidden { display: none; }
.month-title { font-size: 0.875rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border-light); }
.policy-item { background: var(--card); border-radius: var(--radius-md); padding: 16px; margin-bottom: 12px; box-shadow: var(--shadow-xs); border: 1px solid var(--border-light); transition: var(--t); }
.policy-item:hover { box-shadow: var(--shadow-sm); }
.policy-item.hidden { display: none; }
.policy-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 8px; }
.tags { display: flex; flex-wrap: wrap; gap: 4px; }
.tag { padding: 2px 8px; border-radius: 4px; font-size: 0.6875rem; font-weight: 600; white-space: nowrap; }
.tag-urgency-high { background: var(--danger-bg); color: var(--danger-text); }
.tag-urgency-medium { background: var(--warning-bg); color: var(--warning-text); }
.tag-urgency-low { background: var(--bg-secondary); color: var(--text-tertiary); }
.tag-category { background: var(--info-bg); color: var(--info); }
.tag-region { background: #f0f9ff; color: #0369a1; }
.tag-status-proposed { background: #faf5ff; color: #7c3aed; }
.tag-status-confirmed { background: #f0fdf4; color: #16a34a; }
.tag-status-implemented { background: #ecfdf5; color: #059669; }
.tag-status-developing { background: #fffbeb; color: #d97706; }
.tag-unverified { background: #fef3c7; color: #92400e; }
.tag-impact { background: #f0f9ff; color: #0284c7; }
.tag-tag { background: var(--bg-secondary); color: var(--text-secondary); }
.policy-date { font-size: 0.75rem; color: var(--text-tertiary); white-space: nowrap; flex-shrink: 0; }
.policy-source { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 6px; }
.policy-title { font-size: 0.9375rem; font-weight: 700; color: var(--text); line-height: 1.5; margin-bottom: 8px; }
.policy-desc { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.7; }
.policy-tags { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 4px; }
.policy-links { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px; }
.policy-links a { font-size: 0.6875rem; color: var(--primary); text-decoration: none; padding: 3px 8px; border-radius: 4px; background: var(--primary-lighter); border: 1px solid var(--primary-light); transition: var(--t); }
.policy-links a:hover { background: var(--primary); color: white; }
.panel-global .policy-links a { background: var(--accent-lighter); color: var(--accent); border-color: var(--accent-light); }
.panel-global .policy-links a:hover { background: var(--accent); color: white; }
.timeline.collapsed .policy-desc { display: none; }

/* Footer Note */
.footer-note { margin-top: 24px; padding: 14px 16px; border-radius: var(--radius-md); background: var(--info-bg); color: var(--primary-dark); font-size: 0.75rem; line-height: 1.6; border: 1px solid var(--primary-light); }
.panel-global .footer-note { background: var(--accent-lighter); color: var(--accent-dark); border-color: var(--accent-light); }

/* App Grid & Cards */
.app-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; margin-bottom: 16px; }
.app-card { background: var(--card); border-radius: var(--radius-md); padding: 12px; text-align: center; box-shadow: var(--shadow-xs); border: 1px solid var(--border-light); cursor: pointer; transition: var(--t); }
.app-card:hover { box-shadow: var(--shadow-sm); transform: translateY(-1px); }
.app-card .app-icon { font-size: 1.5rem; margin-bottom: 6px; }
.app-card .app-name { font-size: 0.8125rem; font-weight: 600; color: var(--text); }
.app-card .app-company { font-size: 0.6875rem; color: var(--text-secondary); margin-top: 2px; }

/* Collapsible Content */
.collapsible-content { transition: max-height 0.35s ease, opacity 0.25s ease; overflow: hidden; }
.collapsible-content.collapsed { max-height: 0 !important; opacity: 0 !important; margin: 0 !important; padding: 0 !important; }

/* Ranking */
.ranking-panel { display: none; }
.ranking-panel.active { display: block; }
.jump-to-ranking { display: flex; align-items: center; gap: 8px; padding: 10px 16px; border-radius: var(--radius-md); background: var(--accent-lighter); color: var(--accent); font-size: 0.8125rem; font-weight: 600; text-decoration: none; margin-bottom: 16px; transition: var(--t); }
.jump-to-ranking:hover { background: var(--accent-light); }

/* Bottom Nav */
.bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; background: #fff; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-around; padding: 8px 0; padding-bottom: max(8px, env(safe-area-inset-bottom)); z-index: 1000; box-shadow: 0 -2px 10px rgba(0,0,0,0.05); }
.nav-item { display: flex; flex-direction: column; align-items: center; gap: 4px; text-decoration: none; color: #64748b; font-size: 0.65rem; font-weight: 500; padding: 4px 12px; border-radius: 12px; transition: color 0.2s, background 0.2s; }
.nav-item.active { color: #3b82f6; background: rgba(59,130,246,0.12); }
.nav-icon { font-size: 1.2rem; }

/* Responsive */
@media (max-width: 768px) {
    .stats-grid { grid-template-columns: repeat(3, 1fr); }
    .stat-card .number { font-size: 1.125rem; }
    .filter-row { flex-direction: column; gap: 6px; }
    .filter-label { min-width: auto; padding-top: 0; }
}
@media (max-width: 380px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } .stat-card .number { font-size: 1.125rem; } }
@media (min-width: 768px) { .bottom-nav { max-width: 430px; left: 50%; transform: translateX(-50%); } }
"""


# ─── 干净 JS ───
CLEAN_JS = r"""
(function() {
    function debounce(fn, delay) {
        var timer;
        return function() {
            var ctx = this, args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function() { fn.apply(ctx, args); }, delay);
        };
    }

    document.querySelectorAll('.module-tab').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.module-tab').forEach(function(b) { b.classList.remove('active'); });
            document.querySelectorAll('.module-panel').forEach(function(p) { p.classList.remove('active'); });
            this.classList.add('active');
            document.getElementById('module-' + this.dataset.module).classList.add('active');
        });
    });

    document.querySelectorAll('.policy-item').forEach(function(item) {
        var raw = item.dataset.sourceLinks;
        if (!raw) return;
        try {
            var links = JSON.parse(raw);
            if (!links.length) return;
            var linksDiv = document.createElement('div');
            linksDiv.className = 'policy-links';
            links.forEach(function(link) {
                var a = document.createElement('a');
                a.href = link.url; a.target = '_blank'; a.rel = 'noopener';
                a.textContent = ' ' + link.label;
                linksDiv.appendChild(a);
            });
            item.appendChild(linksDiv);
        } catch(e) {}
    });

    function bindFilters(panelSelector) {
        var panel = document.querySelector(panelSelector);
        if (!panel) return;
        var moduleType = panelSelector.indexOf('thai') >= 0 ? 'thai'
                       : panelSelector.indexOf('global') >= 0 ? 'global'
                       : panelSelector.indexOf('app') >= 0 ? 'app' : 'other';
        var tabsContainer = panel.querySelector('.tabs');
        var filtersContainer = panel.querySelector('.filters');
        var searchInput = panel.querySelector('.search-input');
        var sortSelect = panel.querySelector('.sort-select');
        var statsContainer = panel.querySelector('.stats-grid');
        var timelineEl = panel.querySelector('.timeline');
        if (!timelineEl) return;

        if (tabsContainer) {
            tabsContainer.querySelectorAll('.tab').forEach(function(t) {
                t.addEventListener('click', function() {
                    tabsContainer.querySelectorAll('.tab').forEach(function(x) { x.classList.remove('active'); });
                    this.classList.add('active');
                    runFilter();
                });
            });
        }
        if (filtersContainer) {
            filtersContainer.querySelectorAll('.filter-options').forEach(function(group) {
                group.querySelectorAll('.chip').forEach(function(chip) {
                    chip.addEventListener('click', function() {
                        group.querySelectorAll('.chip').forEach(function(c) { c.classList.remove('active'); });
                        this.classList.add('active');
                        runFilter();
                    });
                });
            });
        }
        if (searchInput) { searchInput.addEventListener('input', debounce(runFilter, 300)); }
        if (sortSelect) { sortSelect.addEventListener('change', runFilter); }
        var expandBtn = panel.querySelector('.expand-btn');
        if (expandBtn) {
            expandBtn.addEventListener('click', function() {
                var isCollapsed = timelineEl.classList.toggle('collapsed');
                expandBtn.textContent = isCollapsed ? '全部展开' : '全部收起';
            });
        }

        function getActiveChipValue(filterAttr) {
            var group = filtersContainer ? filtersContainer.querySelector('[data-filter="' + filterAttr + '"]') : null;
            if (!group) return 'all';
            var active = group.querySelector('.chip.active');
            return active ? active.dataset.value : 'all';
        }
        function getActiveTab() {
            if (!tabsContainer) return 'all';
            var active = tabsContainer.querySelector('.tab.active');
            return active ? active.dataset.tab : 'all';
        }

        function runFilter() {
            var activeTab = getActiveTab();
            var items = Array.from(timelineEl.querySelectorAll('.policy-item'));
            var searchText = searchInput ? searchInput.value.toLowerCase() : '';
            var sortMode = sortSelect ? sortSelect.value : 'newest';
            var sT = 0, sH = 0, sM = 0, sL = 0, sU = 0, sC = 0;
            items.forEach(function(item) {
                var region = item.dataset.region || '', categories = item.dataset.categories || '';
                var urgency = item.dataset.urgency || '', status = item.dataset.status || '';
                var verified = item.dataset.verified || '', dataApp = item.dataset.app || '';
                var text = item.innerText.toLowerCase(), tabMatch = true;
                if (moduleType === 'global') {
                    if (activeTab === 'sea') tabMatch = /印尼|菲律宾|越南/.test(region);
                    else if (activeTab === 'latam') tabMatch = /墨西哥|巴西|阿根廷/.test(region);
                    else if (activeTab === 'africa') tabMatch = /尼日利亚|肯尼亚|埃及/.test(region);
                    else if (activeTab === 'sasia') tabMatch = /巴基斯坦|孟加拉/.test(region);
                    else if (activeTab === 'cross') tabMatch = /跨市场/.test(region);
                } else if (moduleType === 'thai') {
                    if (activeTab === 'bnpl') tabMatch = (item.dataset.business || '').includes('BNPL');
                    else if (activeTab === 'ploan') tabMatch = (item.dataset.business || '').includes('Personal Loan');
                    else if (activeTab === 'pico') tabMatch = (item.dataset.business || '').includes('Pico Loan') || (item.dataset.business || '').includes('Nano Finance');
                    else if (activeTab === 'license') tabMatch = categories.includes('牌照政策');
                    else if (activeTab === 'relief') tabMatch = categories.includes('债务纾困');
                } else if (moduleType === 'app') {
                    if (activeTab === 'complaint') tabMatch = categories.includes('客户投诉');
                    else if (activeTab === 'social') tabMatch = categories.includes('社媒讨论');
                    else if (activeTab === 'regulatory') tabMatch = categories.includes('监管政策');
                    else if (activeTab === 'warning') tabMatch = categories.includes('风险预警');
                    else if (activeTab === 'baseline') tabMatch = categories.includes('基础档案');
                }
                var rF = getActiveChipValue('region'), cF = getActiveChipValue('category');
                var uF = getActiveChipValue('urgency'), sF = getActiveChipValue('status');
                var vF = getActiveChipValue('verified'), aF = getActiveChipValue('app');
                var stF = getActiveChipValue('signalType');
                if (tabMatch
                    && (rF === 'all' || region === rF)
                    && (cF === 'all' || categories.includes(cF))
                    && (uF === 'all' || urgency === uF)
                    && (sF === 'all' || status === sF)
                    && (vF === 'all' || verified === vF)
                    && (aF === 'all' || dataApp === aF)
                    && (stF === 'all' || categories.includes(stF))
                    && (!searchText || text.includes(searchText))) {
                    item.classList.remove('hidden'); sT++;
                    if (urgency === '高') sH++; else if (urgency === '中') sM++; else if (urgency === '低') sL++;
                    if (verified === 'unverified') sU++;
                    if (categories.includes('客户投诉')) sC++;
                } else { item.classList.add('hidden'); }
            });
            if (statsContainer) {
                var t = statsContainer.querySelector('.stat-total'); if (t) t.textContent = sT;
                var h = statsContainer.querySelector('.stat-high'); if (h) h.textContent = sH;
                var m2 = statsContainer.querySelector('.stat-medium'); if (m2) m2.textContent = sM;
                var l = statsContainer.querySelector('.stat-low'); if (l) l.textContent = sL;
                var u = statsContainer.querySelector('.stat-unverified'); if (u) u.textContent = sU;
                var c = statsContainer.querySelector('.stat-complaint'); if (c) c.textContent = sC;
            }
            timelineEl.querySelectorAll('.month-section').forEach(function(section) {
                var vItems = Array.from(section.querySelectorAll('.policy-item:not(.hidden)'));
                vItems.sort(function(a, b) {
                    var ad = a.dataset.date, bd = b.dataset.date;
                    if (sortMode === 'newest') return bd.localeCompare(ad);
                    if (sortMode === 'oldest') return ad.localeCompare(bd);
                    if (sortMode === 'urgency') { var map = {'高':3,'中':2,'低':1}; return (map[b.dataset.urgency]||0) - (map[a.dataset.urgency]||0); }
                    return 0;
                });
                vItems.forEach(function(item) { section.appendChild(item); });
                var title = section.querySelector('.month-title');
                var base = title.textContent.split('(')[0].trim();
                if (vItems.length === 0) section.classList.add('hidden');
                else { section.classList.remove('hidden'); title.textContent = base + ' (' + vItems.length + ' 条)'; }
            });
        }
        runFilter();
    }

    // APP grid click
    (function() {
        var mp = document.getElementById('module-app');
        if (!mp) return;
        mp.querySelectorAll('.app-card[data-app]').forEach(function(card) {
            card.addEventListener('click', function() {
                var appName = card.getAttribute('data-app');
                var tc = mp.querySelector('.tabs');
                if (tc) tc.querySelectorAll('.tab').forEach(function(t) { t.classList.toggle('active', t.dataset.tab === 'all'); });
                var g = mp.querySelector('[data-filter="app"]');
                if (g) g.querySelectorAll('.chip').forEach(function(c) { c.classList.toggle('active', c.dataset.value === appName); });
                var fw = mp.querySelector('.filters');
                if (fw) fw.classList.add('expanded');
                var si = mp.querySelector('.search-input');
                if (si) si.dispatchEvent(new Event('input', { bubbles: true }));
                var tl = mp.querySelector('.timeline');
                if (tl) tl.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });
    })();

    bindFilters('#module-thai');
    bindFilters('#module-global');
    bindFilters('#module-app');
})();
"""


def extract_between_markers(html, start_marker, end_markers):
    """Extract content from start_marker to the first matching end_marker"""
    start_idx = html.find(start_marker)
    if start_idx < 0:
        return None
    
    end_idx = len(html)
    for em in end_markers:
        idx = html.find(em, start_idx + len(start_marker))
        if idx >= 0 and idx < end_idx:
            end_idx = idx
    
    return html[start_idx:end_idx]


def rebuild_page(source_path, output_path):
    print(f"📖 读取源文件: {source_path}")
    with open(source_path, 'r', encoding='utf-8') as f:
        source = f.read()
    print(f"   源文件大小: {len(source)} 字符")

    # 1. 提取 title
    title = extract_head_meta(source)
    print(f"   标题: {title}")

    # 2. 用注释边界提取三个模块的原始 HTML
    print("📦 提取模块数据（使用注释边界）...")
    
    m1_comment = source.find('<!--  MODULE 1:')
    m2_comment = source.find('<!--  MODULE 2:')
    m3_comment = source.find('<!--  MODULE 3:')
    js_comment = source.find('<!--  JAVASCRIPT')
    if js_comment < 0:
        js_comment = source.find('<script>')
    
    # 提取每个模块的 div（从 <div class="module-panel..."> 到下一个注释标记前）
    module_ranges = [
        ('module-thai', m1_comment, m2_comment),
        ('module-global', m2_comment, m3_comment),
        ('module-app', m3_comment, js_comment),
    ]
    
    modules = {}
    for mod_id, start, end in module_ranges:
        if start < 0 or end < 0:
            print(f"   ❌ {mod_id}: 边界标记未找到 (start={start}, end={end})")
            continue
        
        # 找到模块 div 起始位置
        div_start = source.find('<div', start)
        if div_start < 0 or div_start >= end:
            print(f"   ❌ {mod_id}: 未找到 div 起始")
            continue
        
        # 提取从 div 开始到下一个注释标记的内容
        raw = source[div_start:end].rstrip()
        
        # 1. 先修 broken quotes（确保后续 regex 能正确匹配）
        raw = fix_broken_quotes(raw)
        # 2. 移除 collapsed 类
        raw = simple_clean_collapsed(raw)
        # 3. 补齐未闭合的 div
        raw = fix_unclosed_divs(raw)
        
        items = raw.count('class="policy-item"')
        print(f"   ✅ {mod_id}: {len(raw)} chars, {items} items")
        modules[mod_id] = raw
    
    total_items = source.count('class="policy-item"')
    print(f"\n📊 总数据条目: {total_items}")

    # 3. 构建新页面
    print("\n🔨 构建新页面...")
    
    parts = []
    parts.append(f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="format-detection" content="telephone=no, email=no, address=no">
    <meta name="theme-color" content="#2563eb">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="description" content="实时监控泰国BNPL/Personal Loan/Pico Loan监管政策、中国出海现金贷全球监管动态、泰国头部借贷APP同业信号，每日自动更新。">
    <meta property="og:title" content="政策监控面板 — 泰国BNPL + 中国出海现金贷全球监管">
    <meta property="og:description" content="实时监控泰国BNPL/Personal Loan/Pico Loan监管政策、中国出海现金贷全球监管动态、泰国头部借贷APP同业信号。">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://praxisfit.me/">
    <meta property="og:image" content="https://praxisfit.me/og-image.png">
    <meta property="og:locale" content="zh_CN">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="政策监控面板 — 泰国BNPL + 中国出海现金贷全球监管">
    <meta name="twitter:description" content="实时监控泰国BNPL/Personal Loan/Pico Loan监管政策、中国出海现金贷全球监管动态、泰国头部借贷APP同业信号。">
    <link rel="canonical" href="https://praxisfit.me/">
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🛡️</text></svg>">
    <title>{title}</title>
    <style>{CLEAN_CSS}
    </style>
</head>
<body>

<!-- Module Navigation -->
<nav class="module-nav" role="tablist" aria-label="模块导航">
    <button class="module-tab active" data-module="thai" role="tab" aria-selected="true">TH泰国政策监控</button>
    <button class="module-tab global" data-module="global" role="tab" aria-selected="false">全球出海监控</button>
    <button class="module-tab app" data-module="app" role="tab" aria-selected="false">APP监控</button>
</nav>
''')

    # 添加每个模块
    panel_classes = {
        'module-thai': 'panel-thai',
        'module-global': 'panel-global',
        'module-app': 'panel-app',
    }
    
    for mod_id in ['module-thai', 'module-global', 'module-app']:
        if mod_id in modules:
            active = ' active' if mod_id == 'module-thai' else ''
            parts.append(f'\n<!-- {mod_id} -->\n')
            parts.append(modules[mod_id])
            parts.append('\n')

    # 底部导航 + 脚本
    parts.append('''
<!-- Bottom Navigation -->
<nav class="bottom-nav">
    <a href="/" class="nav-item"><span class="nav-icon">🏠</span><span>首页</span></a>
    <a href="/payment-intel/" class="nav-item"><span class="nav-icon">💳</span><span>支付</span></a>
    <a href="/policy-monitor/" class="nav-item active"><span class="nav-icon">🛡️</span><span>政策</span></a>
    <a href="/stock-dash/" class="nav-item"><span class="nav-icon">📈</span><span>股市</span></a>
</nav>

<script>''' + CLEAN_JS + '''</script>

<script>
(function(){
    var today = new Date().toISOString().slice(0,10);
    var key = 'policy-monitor';
    if (localStorage.getItem('pv_' + key + '_date') !== today) {
        fetch('https://counterapi.com/api/praxisfit.me/view/' + key + '?trackOnly=true').catch(function(){});
        localStorage.setItem('pv_' + key + '_date', today);
    }
})();
</script>
</body>
</html>
''')

    new_html = ''.join(parts)

    # 4. 验证
    print("🔍 验证输出...")
    body = new_html[new_html.find('<body'):new_html.find('</body>')]
    div_opens = len(re.findall(r'<div[\s>]', body))
    div_closes = len(re.findall(r'</div>', body))
    
    collapsed_count = len(re.findall(r'class="[^"]*collapsed[^"]*"', new_html))
    bad_quotes = len(re.findall(r'class="[^"]*>', new_html))
    dark_refs = new_html.count('data-theme="dark"')
    items_out = new_html.count('class="policy-item"')
    
    # JS 验证
    js_match = re.search(r'<script>(.*?)</script>', new_html, re.DOTALL)
    js_ok = True
    if js_match:
        js = js_match.group(1)
        js_clean = re.sub(r"'[^']*'", '', js)
        js_clean = re.sub(r'"[^"]*"', '', js_clean)
        js_clean = re.sub(r'//.*', '', js_clean)
        js_clean = re.sub(r'/\*.*?\*/', '', js_clean, flags=re.DOTALL)
        if js_clean.count('(') != js_clean.count(')'):
            js_ok = False
            print(f"   ⚠️ JS paren imbalance: ( {js_clean.count('(')} vs ) {js_clean.count(')')}")
        if js.count('{') != js.count('}'):
            js_ok = False
            print(f"   ⚠️ JS brace imbalance: {{ {js.count('{')} }} {js.count('}')}")

    all_ok = True
    checks = [
        (div_opens == div_closes, f"Div balance: {div_opens}/{div_closes}"),
        (collapsed_count == 0, f"Collapsed classes: {collapsed_count}"),
        (bad_quotes == 0, f"Broken quotes: {bad_quotes}"),
        (dark_refs == 0, f"Dark mode refs: {dark_refs}"),
        (items_out == total_items, f"Items: {items_out}/{total_items}"),
        (js_ok, "JS syntax"),
    ]
    
    for ok, msg in checks:
        status = "✅" if ok else "❌"
        print(f"   {status} {msg}")
        if not ok:
            all_ok = False

    # 5. 写入
    print(f"\n💾 写入: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_html)
    print(f"   输出大小: {len(new_html)} chars ({len(new_html)//1024}K)")
    
    if all_ok:
        print("\n✅ 重建完成！所有验证通过。")
    else:
        print("\n⚠️ 重建完成，但有验证未通过。")
    
    return all_ok


if __name__ == '__main__':
    base = os.path.dirname(os.path.abspath(__file__))
    source_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base, '..', '..', 'policy-monitor-github', 'index.html')
    source_path = os.path.normpath(source_path)
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(base, 'index.html')
    output_path = os.path.normpath(output_path)
    
    rebuild_page(source_path, output_path)
