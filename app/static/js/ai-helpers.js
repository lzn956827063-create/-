/**
 * ai-helpers.js — Utility for calling the AI optimize endpoint.
 * Used by resume-editor.js for text polishing, tailoring, expansion, and proofreading.
 */
var AIHelpers = (function () {
    var API_URL = '/api/ai/optimize';

    /**
     * Optimize text using the configured AI provider.
     *
     * @param {string} text - The text to optimize
     * @param {string} action - One of: polish, tailor, expand, proofread
     * @param {string} context - Optional context (e.g., job description for tailor)
     * @returns {Promise<{optimized_text: string, action: string}>}
     */
    function optimizeText(text, action, context) {
        return fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                action: action || 'polish',
                context: context || ''
            })
        }).then(function (response) {
            return response.json().then(function (data) {
                if (!response.ok) {
                    var err = new Error(data.error || 'AI service error');
                    err.fallbackText = data.fallback_text || text;
                    throw err;
                }
                return data;
            });
        });
    }

    return {
        optimizeText: optimizeText
    };
})();
