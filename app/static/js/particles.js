/**
 * particles.js — Interactive Canvas particle background.
 * Zero dependencies. Theme-aware. Respects prefers-reduced-motion.
 */
(function () {
    var canvas = document.getElementById('particle-canvas');
    if (!canvas) return;

    var ctx = canvas.getContext('2d');
    var particles = [];
    var mouse = { x: -9999, y: -9999, active: false };
    var animationId = null;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);

    // ── Color palettes ──────────────────────────────────────────
    function getColors() {
        var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return isDark ? [
            'rgba(108,131,247,0.18)',
            'rgba(108,131,247,0.12)',
            'rgba(32,191,107,0.1)',
            'rgba(247,183,49,0.1)',
            'rgba(52,152,219,0.1)',
        ] : [
            'rgba(67,97,238,0.15)',
            'rgba(67,97,238,0.1)',
            'rgba(32,191,107,0.08)',
            'rgba(247,183,49,0.1)',
            'rgba(52,152,219,0.08)',
        ];
    }

    var colors = getColors();
    var LINE_COLOR_LIGHT = 'rgba(67,97,238,0.08)';
    var LINE_COLOR_DARK = 'rgba(108,131,247,0.07)';

    function getLineColor() {
        return document.documentElement.getAttribute('data-theme') === 'dark'
            ? LINE_COLOR_DARK : LINE_COLOR_LIGHT;
    }

    var lineColor = getLineColor();

    // ── Particle factory ─────────────────────────────────────────
    function createParticle() {
        return {
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            size: Math.random() * 2 + 1,
            opacity: Math.random() * 0.3 + 0.1,
            color: colors[Math.floor(Math.random() * colors.length)],
        };
    }

    function initParticles() {
        var area = canvas.width * canvas.height;
        var count = Math.min(80, Math.max(40, Math.floor(area / 12000)));
        particles = [];
        for (var i = 0; i < count; i++) {
            particles.push(createParticle());
        }
    }

    // ── Resize ───────────────────────────────────────────────────
    function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = window.innerWidth * dpr;
        canvas.height = window.innerHeight * dpr;
        canvas.style.width = window.innerWidth + 'px';
        canvas.style.height = window.innerHeight + 'px';
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.scale(dpr, dpr);
        initParticles();
    }

    // ── Animation loop ───────────────────────────────────────────
    var MAX_DIST = 130;
    var MOUSE_FORCE = 0.015;
    var MOUSE_RADIUS = 180;

    function animate() {
        ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr);

        var w = canvas.width / dpr;
        var h = canvas.height / dpr;

        for (var i = 0; i < particles.length; i++) {
            var p = particles[i];

            // Mouse attraction (gentle pull toward cursor)
            if (mouse.active) {
                var dx = mouse.x - p.x;
                var dy = mouse.y - p.y;
                var dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < MOUSE_RADIUS && dist > 1) {
                    var force = (MOUSE_RADIUS - dist) / MOUSE_RADIUS * MOUSE_FORCE;
                    p.vx += (dx / dist) * force;
                    p.vy += (dy / dist) * force;
                }
            }

            // Apply velocity
            p.x += p.vx;
            p.y += p.vy;

            // Damping
            p.vx *= 0.998;
            p.vy *= 0.998;

            // Add gentle random drift
            p.vx += (Math.random() - 0.5) * 0.02;
            p.vy += (Math.random() - 0.5) * 0.02;

            // Speed limit
            var speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
            if (speed > 0.8) {
                p.vx = (p.vx / speed) * 0.8;
                p.vy = (p.vy / speed) * 0.8;
            }

            // Wrap around edges
            if (p.x < -20) p.x = w + 20;
            if (p.x > w + 20) p.x = -20;
            if (p.y < -20) p.y = h + 20;
            if (p.y > h + 20) p.y = -20;

            // Draw particle
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = p.color;
            ctx.fill();

            // Draw connections to nearby particles
            for (var j = i + 1; j < particles.length; j++) {
                var p2 = particles[j];
                var cdx = p.x - p2.x;
                var cdy = p.y - p2.y;
                var cdist = Math.sqrt(cdx * cdx + cdy * cdy);
                if (cdist < MAX_DIST) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = lineColor;
                    ctx.lineWidth = 0.6;
                    ctx.globalAlpha = (1 - cdist / MAX_DIST) * 0.5;
                    ctx.stroke();
                    ctx.globalAlpha = 1;
                }
            }
        }

        animationId = requestAnimationFrame(animate);
    }

    // ── Event listeners ──────────────────────────────────────────
    function onMouseMove(e) {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
        mouse.active = true;
    }

    function onMouseLeave() {
        mouse.active = false;
    }

    // ── Theme observer ───────────────────────────────────────────
    var themeObserver = new MutationObserver(function () {
        colors = getColors();
        lineColor = getLineColor();
        // Update existing particles with new colors
        for (var i = 0; i < particles.length; i++) {
            particles[i].color = colors[Math.floor(Math.random() * colors.length)];
        }
    });

    // ── Reduced motion check ─────────────────────────────────────
    var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)');

    function startOrStop() {
        if (prefersReduced.matches) {
            if (animationId) {
                cancelAnimationFrame(animationId);
                animationId = null;
            }
            // Draw a static frame
            ctx.clearRect(0, 0, canvas.width / dpr, canvas.height / dpr);
            for (var i = 0; i < particles.length; i++) {
                var p = particles[i];
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = p.color;
                ctx.fill();
            }
        } else {
            if (!animationId) {
                animate();
            }
        }
    }

    // ── Init ─────────────────────────────────────────────────────
    resize();
    startOrStop();

    window.addEventListener('resize', resize);
    document.addEventListener('mousemove', onMouseMove, { passive: true });
    document.addEventListener('mouseleave', onMouseLeave);
    themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    prefersReduced.addEventListener('change', startOrStop);
})();
