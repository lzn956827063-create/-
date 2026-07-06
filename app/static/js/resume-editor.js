/**
 * resume-editor.js — Full AI-powered resume editor with live preview, auto-save,
 * template switching, and PDF export.
 *
 * Depends on: AIHelpers (ai-helpers.js), html2pdf.js (CDN)
 */
(function () {
    // ==================================================================
    // State
    // ==================================================================
    var resumeData = null;
    var currentTemplate = 'professional';
    var autoSaveTimer = null;
    var AUTO_SAVE_DELAY = 800;

    // ==================================================================
    // Init
    // ==================================================================
    function init() {
        if (!document.getElementById('resume-app')) return;

        loadResumeData().then(function () {
            bindEvents();
            refreshPreview();
        });
    }

    function loadResumeData() {
        return fetch('/api/resume')
            .then(function (r) { return r.json(); })
            .then(function (data) {
                resumeData = data;
                populateForms();
                return data;
            })
            .catch(function (err) {
                console.error('Failed to load resume:', err);
                showToast('Failed to load resume data.', 'error');
            });
    }

    // ==================================================================
    // Bind events
    // ==================================================================
    function bindEvents() {
        // Tab switching
        document.querySelectorAll('.form-tab').forEach(function (tab) {
            tab.addEventListener('click', function () {
                document.querySelectorAll('.form-tab').forEach(function (t) { t.classList.remove('active'); });
                document.querySelectorAll('.tab-panel').forEach(function (p) { p.classList.remove('active'); });
                tab.classList.add('active');
                var panel = document.getElementById('tab-' + tab.dataset.tab);
                if (panel) panel.classList.add('active');
            });
        });

        // Template switching
        var templateSelect = document.getElementById('template-select');
        if (templateSelect) {
            templateSelect.addEventListener('change', function () {
                currentTemplate = this.value;
                refreshPreview();
            });
        }

        // PDF Export
        var exportBtn = document.getElementById('btn-export-pdf');
        if (exportBtn) {
            exportBtn.addEventListener('click', exportPdf);
        }

        // Add buttons
        var addSkillGroup = document.getElementById('btn-add-skill-group');
        if (addSkillGroup) addSkillGroup.addEventListener('click', function () { addSkillGroupFn(); });
        var addExp = document.getElementById('btn-add-experience');
        if (addExp) addExp.addEventListener('click', function () { addExperience(); });
        var addEdu = document.getElementById('btn-add-education');
        if (addEdu) addEdu.addEventListener('click', function () { addEducation(); });
        var addProj = document.getElementById('btn-add-project');
        if (addProj) addProj.addEventListener('click', function () { addProject(); });

        // AI buttons
        document.querySelectorAll('.ai-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var field = this.dataset.field;
                var action = this.dataset.action;
                var source = document.querySelector('[data-field="' + field + '"]');
                if (!source) return;
                var text = source.value.trim();
                if (!text) { showToast('Enter some text first.', 'info'); return; }

                this.classList.add('loading');
                this.textContent = '⏳';

                AIHelpers.optimizeText(text, action)
                    .then(function (result) {
                        source.value = result.optimized_text;
                        collectFormData();
                        refreshPreview();
                        saveResume();
                        showToast('Text optimized!', 'success');
                    })
                    .catch(function (err) {
                        showToast(err.fallbackText ? 'AI unavailable — kept original text.' : err.message, 'error');
                    })
                    .finally(function () {
                        btn.classList.remove('loading');
                        btn.textContent = action === 'polish' ? '✨' : action === 'proofread' ? '🔍' : '✨';
                    });
            });
        });

        // Form field change → auto-save
        document.getElementById('resume-app').addEventListener('input', function (e) {
            if (e.target.closest('.resume-field') || e.target.closest('.skill-items-row') ||
                e.target.closest('.experience-block') || e.target.closest('.education-block') ||
                e.target.closest('.project-block') || e.target.closest('.skill-group-block')) {
                scheduleAutoSave();
            }
        });
    }

    // ==================================================================
    // Populate forms from loaded data
    // ==================================================================
    function populateForms() {
        if (!resumeData) return;

        // Basic Info
        var bi = resumeData.basic_info || {};
        setFieldValue('basic_info.name', bi.name);
        setFieldValue('basic_info.title', bi.title);
        setFieldValue('basic_info.email', bi.email);
        setFieldValue('basic_info.phone', bi.phone);
        setFieldValue('basic_info.location', bi.location);
        setFieldValue('basic_info.website', bi.website);
        setFieldValue('basic_info.summary', bi.summary);

        // Skills
        renderSkills(resumeData.skills || []);
        // Experience
        renderExperience(resumeData.experience || []);
        // Education
        renderEducation(resumeData.education || []);
        // Projects
        renderProjects(resumeData.projects || []);
    }

    function setFieldValue(field, value) {
        var el = document.querySelector('[data-field="' + field + '"]');
        if (el) el.value = value || '';
    }

    // ==================================================================
    // Skills rendering
    // ==================================================================
    function renderSkills(skills) {
        var container = document.getElementById('skills-container');
        if (!container) return;
        container.innerHTML = '';

        skills.forEach(function (group, gi) {
            var block = document.createElement('div');
            block.className = 'skill-group-block';
            block.innerHTML =
                '<div class="block-header">' +
                '<input type="text" class="form-input skill-group-category" value="' + escapeHtml(group.category || '') + '" placeholder="Category name (e.g., Frontend)" style="flex:1">' +
                '<button class="btn-remove" title="Remove">&times;</button>' +
                '</div>' +
                '<div class="skill-items-container"></div>' +
                '<button class="btn btn-outline btn-sm btn-add-skill-item" style="margin-top:8px">+ Add Skill</button>';

            var itemsContainer = block.querySelector('.skill-items-container');
            (group.items || []).forEach(function (item, ii) {
                itemsContainer.appendChild(createSkillItemRow(item, gi, ii));
            });

            block.querySelector('.btn-add-skill-item').addEventListener('click', function () {
                itemsContainer.appendChild(createSkillItemRow({ name: '', level: 3 }, gi, itemsContainer.children.length));
                scheduleAutoSave();
            });

            block.querySelector('.btn-remove').addEventListener('click', function () {
                block.remove();
                scheduleAutoSave();
            });

            block.addEventListener('input', scheduleAutoSave);
            container.appendChild(block);
        });
    }

    function createSkillItemRow(item, gi, ii) {
        var row = document.createElement('div');
        row.className = 'skill-items-row';
        row.innerHTML =
            '<input type="text" class="form-input skill-item-name" value="' + escapeHtml(item.name || '') + '" placeholder="Skill name">' +
            '<select class="form-select skill-item-level">' +
            [1, 2, 3, 4, 5].map(function (l) {
                return '<option value="' + l + '"' + (item.level === l ? ' selected' : '') + '>' + l + '</option>';
            }).join('') +
            '</select>' +
            '<button class="btn btn-sm btn-danger btn-remove-skill" title="Remove">×</button>';
        row.querySelector('.btn-remove-skill').addEventListener('click', function () {
            row.remove();
            scheduleAutoSave();
        });
        return row;
    }

    function addSkillGroupFn() {
        var skills = collectSkills();
        skills.push({ category: '', items: [] });
        renderSkills(skills);
        scheduleAutoSave();
    }

    function collectSkills() {
        var groups = [];
        document.querySelectorAll('.skill-group-block').forEach(function (block) {
            var category = block.querySelector('.skill-group-category').value.trim();
            var items = [];
            block.querySelectorAll('.skill-items-row').forEach(function (row) {
                var name = row.querySelector('.skill-item-name').value.trim();
                var level = parseInt(row.querySelector('.skill-item-level').value);
                if (name) items.push({ name: name, level: level });
            });
            groups.push({ category: category, items: items });
        });
        return groups;
    }

    // ==================================================================
    // Experience rendering
    // ==================================================================
    function renderExperience(experiences) {
        var container = document.getElementById('experience-container');
        if (!container) return;
        container.innerHTML = '';

        experiences.forEach(function (exp, ei) {
            var block = createEntryBlock('experience', exp, ei);
            container.appendChild(block);
        });
    }

    function addExperience() {
        var exps = collectExperience();
        exps.push({ title: '', company: '', start: '', end: '', description: '', highlights: [] });
        renderExperience(exps);
        scheduleAutoSave();
    }

    function collectExperience() {
        var items = [];
        document.querySelectorAll('.experience-block').forEach(function (block) {
            items.push(collectEntryBlock(block));
        });
        return items;
    }

    // ==================================================================
    // Education rendering
    // ==================================================================
    function renderEducation(eduList) {
        var container = document.getElementById('education-container');
        if (!container) return;
        container.innerHTML = '';

        eduList.forEach(function (edu, ei) {
            var block = createEntryBlock('education', edu, ei);
            container.appendChild(block);
        });
    }

    function addEducation() {
        var items = collectEducation();
        items.push({ school: '', degree: '', field: '', start: '', end: '' });
        renderEducation(items);
        scheduleAutoSave();
    }

    function collectEducation() {
        var items = [];
        document.querySelectorAll('.education-block').forEach(function (block) {
            items.push(collectEntryBlock(block));
        });
        return items;
    }

    // ==================================================================
    // Projects rendering
    // ==================================================================
    function renderProjects(projects) {
        var container = document.getElementById('projects-container');
        if (!container) return;
        container.innerHTML = '';

        projects.forEach(function (proj, pi) {
            var block = createEntryBlock('project', proj, pi);
            container.appendChild(block);
        });
    }

    function addProject() {
        var items = collectProjects();
        items.push({ name: '', description: '', tech: '', url: '', highlights: [] });
        renderProjects(items);
        scheduleAutoSave();
    }

    function collectProjects() {
        var items = [];
        document.querySelectorAll('.project-block').forEach(function (block) {
            items.push(collectEntryBlock(block));
        });
        return items;
    }

    // ==================================================================
    // Generic entry block helpers
    // ==================================================================
    function createEntryBlock(type, data, index) {
        var block = document.createElement('div');
        block.className = type + '-block';

        var fields = getEntryFields(type);
        var html = '<div class="block-header"><h4>' + type.charAt(0).toUpperCase() + type.slice(1) + ' #' + (index + 1) + '</h4>' +
            '<button class="btn-remove-entry" title="Remove">&times;</button></div>';

        fields.forEach(function (f) {
            html += '<div class="form-group"><label>' + f.label + '</label>' +
                '<input type="text" class="form-input" data-entry-field="' + f.key + '" value="' + escapeHtml(data[f.key] || '') + '" placeholder="' + f.label + '"></div>';
        });

        // Description textarea
        html += '<div class="form-group"><label>Description <button class="ai-btn" data-entry-action="expand">✨ Expand</button></label>' +
            '<textarea class="form-input" data-entry-field="description" rows="3" placeholder="Describe your ' + type + '...">' + escapeHtml(data.description || '') + '</textarea></div>';

        // Highlights for experience & projects
        if (type === 'experience' || type === 'project') {
            html += '<div class="highlights-container"></div>' +
                '<button class="btn btn-outline btn-sm btn-add-highlight" style="margin-top:4px">+ Add Bullet Point</button>';
        }

        block.innerHTML = html;

        // Highlights
        if (type === 'experience' || type === 'project') {
            var hlContainer = block.querySelector('.highlights-container');
            (data.highlights || []).forEach(function (h) {
                hlContainer.appendChild(createHighlightRow(h));
            });
            block.querySelector('.btn-add-highlight').addEventListener('click', function () {
                hlContainer.appendChild(createHighlightRow(''));
                scheduleAutoSave();
            });
        }

        // AI expand button for description
        var aiExpandBtn = block.querySelector('[data-entry-action="expand"]');
        if (aiExpandBtn) {
            aiExpandBtn.addEventListener('click', function () {
                var textarea = block.querySelector('[data-entry-field="description"]');
                if (!textarea || !textarea.value.trim()) { showToast('Enter a brief description first.', 'info'); return; }
                aiExpandBtn.classList.add('loading');
                aiExpandBtn.textContent = '⏳';
                AIHelpers.optimizeText(textarea.value.trim(), 'expand')
                    .then(function (result) {
                        textarea.value = result.optimized_text;
                        collectFormData();
                        refreshPreview();
                        saveResume();
                        showToast('Description expanded!', 'success');
                    })
                    .catch(function (err) {
                        showToast(err.message, 'error');
                    })
                    .finally(function () {
                        aiExpandBtn.classList.remove('loading');
                        aiExpandBtn.textContent = '✨ Expand';
                    });
            });
        }

        block.querySelector('.btn-remove-entry').addEventListener('click', function () {
            block.remove();
            scheduleAutoSave();
        });

        block.addEventListener('input', scheduleAutoSave);
        return block;
    }

    function getEntryFields(type) {
        switch (type) {
            case 'experience':
                return [
                    { key: 'title', label: 'Job Title' },
                    { key: 'company', label: 'Company' },
                    { key: 'start', label: 'Start Date' },
                    { key: 'end', label: 'End Date (leave blank for Present)' },
                ];
            case 'education':
                return [
                    { key: 'school', label: 'School' },
                    { key: 'degree', label: 'Degree' },
                    { key: 'field', label: 'Field of Study' },
                    { key: 'start', label: 'Start Date' },
                    { key: 'end', label: 'End Date' },
                ];
            case 'project':
                return [
                    { key: 'name', label: 'Project Name' },
                    { key: 'tech', label: 'Technologies Used' },
                    { key: 'url', label: 'Project URL' },
                ];
            default: return [];
        }
    }

    function collectEntryBlock(block) {
        var data = { highlights: [] };
        block.querySelectorAll('[data-entry-field]').forEach(function (el) {
            data[el.dataset.entryField] = el.value.trim();
        });
        block.querySelectorAll('.highlight-row input').forEach(function (input) {
            var val = input.value.trim();
            if (val) data.highlights.push(val);
        });
        return data;
    }

    function createHighlightRow(value) {
        var row = document.createElement('div');
        row.className = 'highlight-row skill-items-row';
        row.innerHTML =
            '<input type="text" class="form-input" value="' + escapeHtml(value || '') + '" placeholder="Bullet point...">' +
            '<button class="btn btn-sm btn-danger btn-remove-skill" title="Remove">×</button>';
        row.querySelector('.btn-remove-skill').addEventListener('click', function () { row.remove(); scheduleAutoSave(); });
        row.querySelector('input').addEventListener('input', scheduleAutoSave);
        return row;
    }

    // ==================================================================
    // Form data collection
    // ==================================================================
    function collectFormData() {
        resumeData = resumeData || {};
        resumeData.basic_info = resumeData.basic_info || {};
        resumeData.skills = resumeData.skills || [];
        resumeData.experience = resumeData.experience || [];
        resumeData.education = resumeData.education || [];
        resumeData.projects = resumeData.projects || [];

        // Basic info
        document.querySelectorAll('.resume-field[data-field^="basic_info."]').forEach(function (el) {
            var key = el.dataset.field.replace('basic_info.', '');
            resumeData.basic_info[key] = el.value.trim();
        });

        // Skills
        resumeData.skills = collectSkills();
        // Experience
        resumeData.experience = collectExperience();
        // Education
        resumeData.education = collectEducation();
        // Projects
        resumeData.projects = collectProjects();
    }

    // ==================================================================
    // Auto-save
    // ==================================================================
    function scheduleAutoSave() {
        clearTimeout(autoSaveTimer);
        var status = document.getElementById('save-status');
        if (status) { status.textContent = 'Saving...'; status.className = 'save-status saving'; }
        autoSaveTimer = setTimeout(function () {
            collectFormData();
            saveResume();
        }, AUTO_SAVE_DELAY);
    }

    function saveResume() {
        if (!resumeData) return;
        fetch('/api/resume', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(resumeData)
        })
            .then(function () {
                var status = document.getElementById('save-status');
                if (status) { status.textContent = 'Saved ✓'; status.className = 'save-status'; }
                refreshPreview();
            })
            .catch(function (err) {
                console.error('Auto-save failed:', err);
                var status = document.getElementById('save-status');
                if (status) { status.textContent = 'Save failed'; status.className = 'save-status saving'; }
            });
    }

    // ==================================================================
    // Preview
    // ==================================================================
    function refreshPreview() {
        collectFormData();
        var preview = document.getElementById('resume-preview');
        if (!preview) return;

        fetch('/api/resume/preview/' + currentTemplate, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(resumeData)
        })
            .then(function (r) { return r.text(); })
            .then(function (html) {
                preview.innerHTML = html;
            })
            .catch(function (err) {
                console.error('Preview failed:', err);
                preview.innerHTML = '<p class="loading-text">Preview unavailable.</p>';
            });
    }

    // ==================================================================
    // PDF Export
    // ==================================================================
    function exportPdf() {
        var preview = document.getElementById('resume-preview');
        if (!preview || !preview.innerHTML.trim()) { showToast('Nothing to export.', 'error'); return; }

        if (typeof html2pdf === 'undefined') {
            showToast('PDF library not loaded. Check your internet connection.', 'error');
            return;
        }

        var btn = document.getElementById('btn-export-pdf');
        var origText = btn.textContent;
        btn.textContent = '⏳ Generating...';
        btn.disabled = true;

        var opt = {
            margin: [0.5, 0.5, 0.5, 0.5],
            filename: 'resume-' + currentTemplate + '.pdf',
            image: { type: 'jpeg', quality: 0.95 },
            html2canvas: { scale: 2, useCORS: true, backgroundColor: '#ffffff' },
            jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
        };

        html2pdf().set(opt).from(preview).save()
            .then(function () {
                showToast('PDF downloaded!', 'success');
            })
            .catch(function (err) {
                console.error('PDF export failed:', err);
                showToast('PDF generation failed. Try a different template.', 'error');
            })
            .finally(function () {
                btn.textContent = origText;
                btn.disabled = false;
            });
    }

    // ==================================================================
    // Utility
    // ==================================================================
    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    }

    function showToast(msg, type) {
        var toast = document.getElementById('toast');
        if (!toast) { alert(msg); return; }
        toast.textContent = msg;
        toast.className = 'toast toast-' + (type || 'info');
        toast.style.display = 'block';
        clearTimeout(toast._timeout);
        toast._timeout = setTimeout(function () { toast.style.display = 'none'; }, 3000);
    }

    // ==================================================================
    // Start
    // ==================================================================
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
