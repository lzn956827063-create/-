/**
 * charts.js — ECharts radar and pie chart initialization for the portfolio homepage.
 * Depends on: echarts (loaded via CDN <script> tag before this file).
 */
(function () {
    var radarChart = null;
    var pieChart = null;

    function getCSSVar(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || '';
    }

    // ── Radar chart options (theme-reactive) ─────────────────────
    function getRadarOption() {
        var textColor = getCSSVar('--color-text') || '#333';
        var textSecondary = getCSSVar('--color-text-secondary') || '#666';
        var primary = '#4361ee';
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (isDark) primary = '#6c83f7';

        var skillDescriptions = {
            '前端': 'HTML/CSS/JS, Vue, React',
            '后端': 'Python Flask, REST API',
            '运维': 'Linux, Docker, Nginx',
            '数据库': 'MySQL, Redis, MongoDB',
            'AI/ML': 'Prompt 工程, LLM 应用',
            '系统设计': '架构模式, 性能优化',
        };

        return {
            tooltip: {
                trigger: 'item',
                backgroundColor: isDark ? 'rgba(26,29,39,0.95)' : 'rgba(255,255,255,0.95)',
                borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
                textStyle: { color: isDark ? '#e4e6eb' : '#212529', fontSize: 13 },
                formatter: function (params) {
                    var name = params.name;
                    var value = params.value;
                    var filled = Math.round(value / 10);
                    var empty = 10 - filled;
                    var bar = '';
                    for (var i = 0; i < filled; i++) bar += '█';
                    for (var j = 0; j < empty; j++) bar += '░';
                    var desc = skillDescriptions[name] || '';
                    return '<strong style="font-size:14px">' + name + '</strong><br/>' +
                           '熟练度: <b>' + value + '%</b><br/>' +
                           '<span style="font-family:monospace;font-size:11px">' + bar + '</span><br/>' +
                           '<span style="color:#999;font-size:11px">' + desc + '</span>';
                },
            },
            legend: {
                bottom: 0,
                textStyle: { color: textColor },
            },
            radar: {
                center: ['50%', '45%'],
                radius: '65%',
                indicator: [
                    { name: '前端', max: 100 },
                    { name: '后端', max: 100 },
                    { name: '运维', max: 100 },
                    { name: '数据库', max: 100 },
                    { name: 'AI/ML', max: 100 },
                    { name: '系统设计', max: 100 },
                ],
                axisName: { color: textSecondary },
                splitArea: {
                    areaStyle: {
                        color: isDark
                            ? ['rgba(108,131,247,0.02)', 'rgba(108,131,247,0.02)']
                            : ['rgba(67,97,238,0.02)', 'rgba(67,97,238,0.02)'],
                    },
                },
            },
            series: [{
                type: 'radar',
                name: '技能水平',
                animationDuration: 800,
                animationEasing: 'cubicOut',
                data: [{
                    value: [80, 85, 60, 75, 55, 65],
                    name: '掌握程度',
                    areaStyle: { color: 'rgba(67,97,238,0.15)' },
                    lineStyle: { color: primary, width: 2 },
                    itemStyle: { color: primary },
                }],
                emphasis: {
                    areaStyle: { color: 'rgba(67,97,238,0.25)' },
                    lineStyle: { width: 3 },
                },
            }],
        };
    }

    // ── Pie chart options (theme-reactive) ───────────────────────
    function getPieOption() {
        var textColor = getCSSVar('--color-text') || '#333';
        var bgColor = getCSSVar('--color-bg') || '#fff';
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';

        var langDescriptions = {
            'Python': 'Flask, 脚本, 数据分析',
            'JavaScript': 'ES6+, DOM, Canvas',
            'Go': '并发编程, CLI 工具',
            'Rust': '系统工具, WASM',
            'SQL': '查询优化, 表设计',
            '其他': 'Shell, YAML, Markdown',
        };

        return {
            tooltip: {
                trigger: 'item',
                backgroundColor: isDark ? 'rgba(26,29,39,0.95)' : 'rgba(255,255,255,0.95)',
                borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.08)',
                textStyle: { color: isDark ? '#e4e6eb' : '#212529', fontSize: 13 },
                formatter: function (params) {
                    var desc = langDescriptions[params.name] || '';
                    return '<strong style="font-size:14px">' + params.name + '</strong><br/>' +
                           '占比: <b>' + params.percent + '%</b><br/>' +
                           '<span style="color:#999;font-size:11px">' + desc + '</span>';
                },
            },
            legend: {
                bottom: 0,
                textStyle: { color: textColor },
            },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                center: ['50%', '45%'],
                avoidLabelOverlap: false,
                selectedMode: 'single',
                animationDuration: 800,
                animationEasing: 'cubicOut',
                itemStyle: {
                    borderRadius: 6,
                    borderColor: getCSSVar('--color-bg') || bgColor,
                    borderWidth: 3,
                },
                label: { show: false },
                emphasis: {
                    label: { show: true, fontSize: 14, fontWeight: 'bold' },
                    scaleSize: 12,
                },
                data: [
                    { value: 35, name: 'Python', itemStyle: { color: '#4361ee' } },
                    { value: 25, name: 'JavaScript', itemStyle: { color: '#f7b731' } },
                    { value: 15, name: 'Go', itemStyle: { color: '#20bf6b' } },
                    { value: 10, name: 'Rust', itemStyle: { color: '#e74c3c' } },
                    { value: 8, name: 'SQL', itemStyle: { color: '#3498db' } },
                    { value: 7, name: '其他', itemStyle: { color: '#9b59b6' } },
                ],
            }],
        };
    }

    // ── Init ─────────────────────────────────────────────────────
    function init() {
        var radarDom = document.getElementById('radar-chart');
        var pieDom = document.getElementById('pie-chart');

        if (!radarDom || !pieDom) return;
        if (typeof echarts === 'undefined') {
            console.warn('ECharts not loaded yet.');
            return;
        }

        radarChart = echarts.init(radarDom);
        pieChart = echarts.init(pieDom);

        radarChart.setOption(getRadarOption());
        pieChart.setOption(getPieOption());

        // ── Responsive resize ────────────────────────────────────
        window.addEventListener('resize', function () {
            if (radarChart) radarChart.resize();
            if (pieChart) pieChart.resize();
        });

        // Theme change: update options (not just resize)
        var observer = new MutationObserver(function () {
            if (radarChart) {
                radarChart.setOption(getRadarOption(), true);
                radarChart.resize();
            }
            if (pieChart) {
                pieChart.setOption(getPieOption(), true);
                pieChart.resize();
            }
        });
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
