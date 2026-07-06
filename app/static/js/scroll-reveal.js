/**
 * scroll-reveal.js — Intersection Observer-based scroll animations.
 * Zero dependencies. Respects prefers-reduced-motion.
 */
(function () {
    var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    if (prefersReduced.matches) return;

    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.15,
        rootMargin: '0px 0px -30px 0px',
    });

    function observeAll() {
        var targets = document.querySelectorAll('.reveal');
        for (var i = 0; i < targets.length; i++) {
            observer.observe(targets[i]);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', observeAll);
    } else {
        observeAll();
    }
})();
