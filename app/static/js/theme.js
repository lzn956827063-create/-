/**
 * theme.js — Dark/light theme toggle with localStorage persistence.
 * Runs before paint to prevent FOUC (Flash of Unstyled Content).
 */
(function () {
    var stored = localStorage.getItem('theme');
    if (stored) {
        document.documentElement.setAttribute('data-theme', stored);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }

    // After DOM ready, wire up the toggle button
    function init() {
        var toggle = document.getElementById('theme-toggle');
        if (!toggle) return;

        toggle.addEventListener('click', function () {
            var current = document.documentElement.getAttribute('data-theme');
            var next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('theme', next);

            // Toggle highlight.js theme if present
            var lightSheet = document.getElementById('hljs-light');
            var darkSheet = document.getElementById('hljs-dark');
            if (lightSheet && darkSheet) {
                lightSheet.disabled = (next === 'dark');
                darkSheet.disabled = (next === 'light');
            }
        });

        // Set initial highlight.js theme
        var current = document.documentElement.getAttribute('data-theme');
        var lightSheet = document.getElementById('hljs-light');
        var darkSheet = document.getElementById('hljs-dark');
        if (lightSheet && darkSheet) {
            lightSheet.disabled = (current === 'dark');
            darkSheet.disabled = (current === 'light');
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
