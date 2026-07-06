/**
 * blog.js — Blog listing search, category filter, and admin blog editor.
 */
(function () {
    var isAdmin = document.querySelector('.blog-editor-page');

    // ==================================================================
    // Public blog page: search + category chips
    // ==================================================================
    function initPublicBlog() {
        var searchInput = document.getElementById('blog-search');
        if (!searchInput) return;

        searchInput.addEventListener('input', debounce(function () {
            var val = this.value.trim();
            var url = new URL(window.location);
            if (val) {
                url.searchParams.set('search', val);
            } else {
                url.searchParams.delete('search');
            }
            url.searchParams.delete('page');
            window.location = url.toString();
        }, 400));
    }

    // ==================================================================
    // Admin blog editor
    // ==================================================================
    var currentPostId = null;
    var postListCache = [];

    function initAdminBlog() {
        loadPostList();
        loadCategories();

        document.getElementById('btn-new-post').addEventListener('click', newPost);
        document.getElementById('btn-save-post').addEventListener('click', savePost);
        document.getElementById('btn-delete-post').addEventListener('click', deletePost);

        // Live Markdown preview
        var contentArea = document.getElementById('post-content');
        if (contentArea) {
            contentArea.addEventListener('input', debounce(updatePreview, 300));
        }

        // Auto-generate slug from title
        var titleInput = document.getElementById('post-title');
        var slugInput = document.getElementById('post-slug');
        if (titleInput && slugInput) {
            titleInput.addEventListener('input', function () {
                if (!slugInput.dataset.manual) {
                    slugInput.value = titleInput.value
                        .toLowerCase()
                        .replace(/[^\w\s-]/g, '')
                        .replace(/[\s_]+/g, '-')
                        .replace(/^-+|-+$/g, '');
                }
            });
            slugInput.addEventListener('input', function () {
                slugInput.dataset.manual = '1';
            });
        }

        // Filter dropdowns
        document.getElementById('filter-category').addEventListener('change', loadPostList);
        document.getElementById('filter-status').addEventListener('change', loadPostList);

        // Category modal
        document.getElementById('btn-add-category').addEventListener('click', addCategory);
    }

    function loadPostList() {
        var catFilter = document.getElementById('filter-category');
        var statusFilter = document.getElementById('filter-status');
        var params = new URLSearchParams();
        params.set('per_page', '50');
        params.set('published_only', '0');
        if (catFilter && catFilter.value) params.set('category_id', catFilter.value);
        if (statusFilter && statusFilter.value === 'published') params.set('published_only', '1');
        if (statusFilter && statusFilter.value === 'draft') params.set('published_only', '0');

        fetch('/api/blog/posts?' + params.toString())
            .then(function (r) { return r.json(); })
            .then(function (data) {
                postListCache = data.posts || [];
                renderPostList(postListCache, statusFilter ? statusFilter.value : '');
            })
            .catch(function (err) {
                console.error('加载文章列表失败:', err);
            });
    }

    function renderPostList(posts, statusFilter) {
        var container = document.getElementById('post-list');
        if (!container) return;

        if (posts.length === 0) {
            container.innerHTML = '<p class="loading-text">暂无文章。</p>';
            return;
        }

        container.innerHTML = posts.map(function (p) {
            var statusBadge = p.is_published
                ? '<span class="published-badge">Published</span>'
                : '<span class="draft-badge">Draft</span>';
            return (
                '<div class="post-list-item' + (p.id === currentPostId ? ' active' : '') + '" data-id="' + p.id + '">' +
                '<div class="item-title">' + escapeHtml(p.title) + '</div>' +
                '<div class="item-meta">' +
                statusBadge +
                '<span>' + (p.created_at || '').substring(0, 10) + '</span>' +
                '<span>' + p.view_count + ' views</span>' +
                '</div></div>'
            );
        }).join('');

        container.querySelectorAll('.post-list-item').forEach(function (el) {
            el.addEventListener('click', function () { editPost(parseInt(this.dataset.id)); });
        });
    }

    function editPost(id) {
        var post = postListCache.find(function (p) { return p.id === id; });
        if (!post) return;
        currentPostId = id;

        // Fetch full post (includes content_md)
        fetch('/api/blog/posts/' + id)
            .then(function (r) { return r.json(); })
            .then(function (full) {
                document.getElementById('post-id').value = full.id;
                document.getElementById('post-title').value = full.title || '';
                document.getElementById('post-slug').value = full.slug || '';
                document.getElementById('post-excerpt').value = full.excerpt || '';
                document.getElementById('post-content').value = full.content_md || '';
                document.getElementById('post-category').value = full.category_id || '';
                document.getElementById('post-status').value = full.is_published ? '1' : '0';
                document.getElementById('editor-empty').style.display = 'none';
                document.getElementById('editor-form').style.display = 'block';
                document.getElementById('btn-delete-post').style.display = 'inline-flex';
                updatePreview();
                renderPostList(postListCache, document.getElementById('filter-status').value);
            })
            .catch(function (err) {
                console.error('加载文章失败:', err);
                showToast('加载文章失败', 'error');
            });
    }

    function newPost() {
        currentPostId = null;
        document.getElementById('post-id').value = '';
        document.getElementById('post-title').value = '';
        document.getElementById('post-slug').value = '';
        document.getElementById('post-slug').dataset.manual = '';
        document.getElementById('post-excerpt').value = '';
        document.getElementById('post-content').value = '';
        document.getElementById('post-category').value = '';
        document.getElementById('post-status').value = '0';
        document.getElementById('editor-empty').style.display = 'none';
        document.getElementById('editor-form').style.display = 'block';
        document.getElementById('btn-delete-post').style.display = 'none';
        document.getElementById('post-preview').innerHTML = '';
    }

    function savePost() {
        var data = {
            title: document.getElementById('post-title').value.trim(),
            slug: document.getElementById('post-slug').value.trim(),
            excerpt: document.getElementById('post-excerpt').value.trim(),
            content_md: document.getElementById('post-content').value,
            category_id: document.getElementById('post-category').value || null,
            is_published: document.getElementById('post-status').value === '1'
        };

        if (!data.title) { showToast('请输入标题。', 'error'); return; }
        if (!data.slug) { showToast('请输入 Slug。', 'error'); return; }

        var method, url;
        if (currentPostId) {
            method = 'PUT';
            url = '/api/blog/posts/' + currentPostId;
        } else {
            method = 'POST';
            url = '/api/blog/posts';
        }

        fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
            .then(function (r) { return r.json(); })
            .then(function (result) {
                if (result.error) { showToast(result.error, 'error'); return; }
                currentPostId = result.id;
                document.getElementById('post-id').value = result.id;
                updatePreview();
                loadPostList();
                showToast('文章保存成功！', 'success');
            })
            .catch(function (err) {
                console.error('保存失败:', err);
                showToast('保存失败: ' + err.message, 'error');
            });
    }

    function deletePost() {
        if (!currentPostId) return;
        if (!confirm('确定永久删除此文章？此操作不可撤销。')) return;

        fetch('/api/blog/posts/' + currentPostId, { method: 'DELETE' })
            .then(function (r) { return r.json(); })
            .then(function () {
                newPost();
                loadPostList();
                showToast('文章已删除。', 'success');
            })
            .catch(function (err) {
                showToast('删除失败: ' + err.message, 'error');
            });
    }

    function updatePreview() {
        var md = document.getElementById('post-content').value;
        var preview = document.getElementById('post-preview');
        if (!preview) return;
        if (typeof marked !== 'undefined') {
            preview.innerHTML = marked.parse(md || '');
            if (typeof hljs !== 'undefined') {
                preview.querySelectorAll('pre code').forEach(function (block) { hljs.highlightElement(block); });
            }
        } else {
            preview.innerHTML = '<p>Marked library not loaded.</p>';
        }
    }

    function loadCategories() {
        fetch('/api/blog/categories')
            .then(function (r) { return r.json(); })
            .then(function (cats) {
                // Populate filter dropdown
                var filter = document.getElementById('filter-category');
                if (filter) {
                    filter.innerHTML = '<option value="">All Categories</option>' +
                        cats.map(function (c) { return '<option value="' + c.id + '">' + escapeHtml(c.name) + '</option>'; }).join('');
                }
                // Populate editor dropdown
                var editorSelect = document.getElementById('post-category');
                if (editorSelect) {
                    editorSelect.innerHTML = '<option value="">No Category</option>' +
                        cats.map(function (c) { return '<option value="' + c.id + '">' + escapeHtml(c.name) + '</option>'; }).join('');
                }
                // Populate modal list
                var catList = document.getElementById('category-list');
                if (catList) {
                    catList.innerHTML = cats.map(function (c) {
                        return '<li>' + escapeHtml(c.name) + ' (' + c.post_count + ' 篇文章) <button class="btn btn-danger btn-sm" onclick="deleteCategory(' + c.id + ')">×</button></li>';
                    }).join('');
                }
            });
    }

    function addCategory() {
        var name = document.getElementById('new-cat-name').value.trim();
        var slug = document.getElementById('new-cat-slug').value.trim() || name;
        if (!name) return;

        fetch('/api/blog/categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name, slug: slug })
        })
            .then(function (r) { return r.json(); })
            .then(function (result) {
                if (result.error) { showToast(result.error, 'error'); return; }
                document.getElementById('new-cat-name').value = '';
                document.getElementById('new-cat-slug').value = '';
                loadCategories();
                showToast('分类添加成功！', 'success');
            });
    }

    window.deleteCategory = function (id) {
        if (!confirm('确定删除此分类？分类下的文章将变为未分类状态。')) return;
        fetch('/api/blog/categories/' + id, { method: 'DELETE' })
            .then(function (r) { return r.json(); })
            .then(function (result) {
                if (result.error) { showToast(result.error, 'error'); return; }
                loadCategories();
                showToast('分类已删除。', 'success');
            });
    };

    // ==================================================================
    // Utility
    // ==================================================================
    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function debounce(fn, delay) {
        var timer;
        return function () {
            var ctx = this, args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function () { fn.apply(ctx, args); }, delay);
        };
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

    // Expose to window for inline handlers
    window.showToast = showToast;

    // ==================================================================
    // Init
    // ==================================================================
    function init() {
        if (isAdmin) {
            initAdminBlog();
        }
        initPublicBlog();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
