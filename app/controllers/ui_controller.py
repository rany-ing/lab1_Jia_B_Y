from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["UI"])

UI_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>News Management UI</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 820px; margin: 32px auto; padding: 0 16px; background: #f8fafc; color: #0f172a; }
    h1, h2 { margin-top: 0; }
    .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px; margin-bottom: 18px; }
    label { display: block; font-weight: 600; margin-bottom: 6px; }
    input, textarea, select { width: 100%; box-sizing: border-box; padding: 8px 10px; margin-bottom: 12px; border: 1px solid #cbd5e1; border-radius: 6px; font: inherit; }
    button { background: #2563eb; color: #fff; border: none; border-radius: 6px; padding: 8px 14px; cursor: pointer; font-weight: 600; margin-right: 8px; }
    button.secondary { background: #475569; }
    button.danger { background: #dc2626; }
    .news-item { border-top: 1px solid #e2e8f0; padding: 12px 0; }
    .news-item:first-child { border-top: none; }
    .meta { color: #64748b; font-size: 0.85rem; margin-bottom: 6px; }
    .error { color: #dc2626; margin-bottom: 10px; }
  </style>
</head>
<body>
  <h1>News Management UI</h1>
  <div id="error" class="error"></div>

  <div class="card">
    <h2 id="form-heading">Create News</h2>
    <form id="news-form">
      <input type="hidden" id="editing-id" value="" />
      <label for="author-select">Author</label>
      <select id="author-select" required></select>
      <label for="news-title">Title</label>
      <input id="news-title" type="text" placeholder="Enter news title" required />
      <label for="news-content">Content</label>
      <textarea id="news-content" rows="4" placeholder="Enter news content" required></textarea>
      <button type="submit" id="submit-btn">Create News</button>
      <button type="button" id="cancel-edit-btn" class="secondary" style="display:none;">Cancel</button>
    </form>
  </div>

  <div class="card" id="detail-card" style="display:none;">
    <h2 id="detail-title"></h2>
    <div class="meta" id="detail-meta"></div>
    <p id="detail-content"></p>
  </div>

  <div class="card">
    <h2>News List</h2>
    <div id="news-list"></div>
  </div>

  <script>
    const errorEl = document.getElementById('error');
    const authorSelect = document.getElementById('author-select');
    const editingIdEl = document.getElementById('editing-id');
    const titleEl = document.getElementById('news-title');
    const contentEl = document.getElementById('news-content');
    const formHeadingEl = document.getElementById('form-heading');
    const submitBtn = document.getElementById('submit-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const newsListEl = document.getElementById('news-list');
    const detailCard = document.getElementById('detail-card');
    const detailTitle = document.getElementById('detail-title');
    const detailMeta = document.getElementById('detail-meta');
    const detailContent = document.getElementById('detail-content');

    function showError(msg) { errorEl.textContent = msg || ''; }

    function extractText(content) {
      if (!content) return '';
      if (typeof content === 'string') return content;
      return content.text || content.lead || content.body || JSON.stringify(content);
    }

    async function loadUsers() {
      const res = await fetch('/users');
      const users = await res.json();
      authorSelect.innerHTML = '';
      users.filter(u => u.is_verified_author).forEach(u => {
        const opt = document.createElement('option');
        opt.value = String(u.id);
        opt.textContent = `${u.name} (${u.email})`;
        authorSelect.appendChild(opt);
      });
    }

    async function viewNews(id) {
      const res = await fetch(`/news/${id}`);
      if (!res.ok) return;
      const item = await res.json();
      detailTitle.textContent = item.title;
      detailMeta.textContent = `News #${item.id} | Author #${item.author_id}`;
      detailContent.textContent = extractText(item.content);
      detailCard.style.display = 'block';
    }

    function startEdit(item) {
      editingIdEl.value = String(item.id);
      titleEl.value = item.title;
      contentEl.value = extractText(item.content);
      formHeadingEl.textContent = `Edit News #${item.id}`;
      submitBtn.textContent = 'Save Changes';
      cancelEditBtn.style.display = 'inline-block';
    }

    function resetForm() {
      editingIdEl.value = '';
      titleEl.value = '';
      contentEl.value = '';
      formHeadingEl.textContent = 'Create News';
      submitBtn.textContent = 'Create News';
      cancelEditBtn.style.display = 'none';
    }

    async function deleteNews(id) {
      showError('');
      const res = await fetch(`/news/${id}`, { method: 'DELETE' });
      if (!res.ok) {
        showError('Failed to delete news');
        return;
      }
      if (detailMeta.textContent.startsWith(`News #${id} `)) {
        detailCard.style.display = 'none';
      }
      await loadNews();
    }

    async function loadNews() {
      const res = await fetch('/news');
      const items = await res.json();
      newsListEl.innerHTML = '';
      if (items.length === 0) {
        newsListEl.textContent = 'No news yet.';
        return;
      }
      items.forEach(item => {
        const div = document.createElement('div');
        div.className = 'news-item';
        div.dataset.newsId = String(item.id);

        const h3 = document.createElement('h3');
        h3.textContent = item.title;
        div.appendChild(h3);

        const p = document.createElement('p');
        p.textContent = extractText(item.content);
        div.appendChild(p);

        const viewBtn = document.createElement('button');
        viewBtn.type = 'button';
        viewBtn.className = 'secondary';
        viewBtn.textContent = 'Read';
        viewBtn.addEventListener('click', () => viewNews(item.id));
        div.appendChild(viewBtn);

        const editBtn = document.createElement('button');
        editBtn.type = 'button';
        editBtn.textContent = 'Edit';
        editBtn.addEventListener('click', () => startEdit(item));
        div.appendChild(editBtn);

        const delBtn = document.createElement('button');
        delBtn.type = 'button';
        delBtn.className = 'danger';
        delBtn.textContent = 'Delete';
        delBtn.addEventListener('click', () => deleteNews(item.id));
        div.appendChild(delBtn);

        newsListEl.appendChild(div);
      });
    }

    document.getElementById('news-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      showError('');
      const editingId = editingIdEl.value;
      const title = titleEl.value.trim();
      const text = contentEl.value.trim();
      if (!title || !text) return;

      if (editingId) {
        const res = await fetch(`/news/${editingId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title, content: { text } }),
        });
        if (!res.ok) {
          showError('Failed to update news');
          return;
        }
        resetForm();
        await loadNews();
        await viewNews(editingId);
      } else {
        const res = await fetch('/news', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title,
            content: { text },
            author_id: Number(authorSelect.value),
          }),
        });
        if (!res.ok) {
          showError('Failed to create news');
          return;
        }
        const created = await res.json();
        resetForm();
        await loadNews();
        await viewNews(created.id);
      }
    });

    cancelEditBtn.addEventListener('click', resetForm);

    (async () => {
      await loadUsers();
      await loadNews();
    })();
  </script>
</body>
</html>
"""


@router.get("/ui", response_class=HTMLResponse)
def news_ui() -> HTMLResponse:
    return HTMLResponse(content=UI_HTML)
