/* Progressive enhancement only; every workflow remains readable without JS. */
const filters = document.querySelector('.filters');
if (filters) {
  const search = document.getElementById('search');
  const category = document.getElementById('category');
  const rows = [...document.querySelectorAll('[data-workflow]')];
  const update = () => {
    const words = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const row of rows) {
      const text = row.textContent.toLowerCase();
      const match = words.every(word => text.includes(word)) && (!category.value || row.dataset.category === category.value);
      row.hidden = !match;
      if (match) count += 1;
    }
    document.getElementById('result-count').textContent = `${count} ${count === 1 ? 'workflow' : 'workflows'}`;
    document.getElementById('empty').hidden = count !== 0;
  };
  filters.hidden = false;
  search.addEventListener('input', update);
  category.addEventListener('change', update);
  update();
}

for (const tools of document.querySelectorAll('.copy-tools')) {
  tools.hidden = false;
  const button = tools.querySelector('[data-copy]');
  const status = tools.querySelector('.copy-status');
  const text = document.getElementById(button.dataset.copy);
  button.addEventListener('click', async () => {
    status.textContent = '';
    try {
      await navigator.clipboard.writeText(text.value);
      status.textContent = 'Copied. Review the skill before giving it to your agent.';
    } catch {
      text.closest('details').open = true;
      text.focus();
      text.select();
      status.textContent = 'Select and copy the highlighted text manually.';
    }
  });
}
