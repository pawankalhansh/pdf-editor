import re

# 1. Update index.html
with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_cat_bar_start = html.find('<div class="category-bar"')
old_cat_bar_end = html.find('</div>', old_cat_bar_start) + 6

new_cat_bar = """        <div class="category-bar" id="categoryBar" style="flex-wrap:wrap; margin-bottom: 30px;">
            <button class="cat-tab active" data-cat="all">All</button>
            <button class="cat-tab" data-cat="organize">Organize</button>
            <button class="cat-tab" data-cat="optimize">Optimize</button>
            <button class="cat-tab" data-cat="to-pdf">Convert to PDF</button>
            <button class="cat-tab" data-cat="from-pdf">Convert from PDF</button>
            <button class="cat-tab" data-cat="edit">Edit</button>
            <button class="cat-tab" data-cat="security">Security</button>
            <button class="cat-tab" data-cat="intelligence">Intelligence</button>
        </div>"""

html = html[:old_cat_bar_start] + new_cat_bar + html[old_cat_bar_end:]

grids_start = html.find('<div class="tool-grid-container">')
workspace_start = html.find('<!-- WORKSPACE VIEW -->')
# We replace between grids_start and workspace_start
grid_html = html[grids_start:workspace_start]

new_grid = '        <div class="tool-grid-container">\n            <div class="tool-grid active" id="mainGrid">\n'

categories = re.findall(r'<div class="tool-grid[^>]*id="grid-([^"]+)">([\s\S]*?)</div>', grid_html)
for cat_name, buttons_html in categories:
    buttons = re.findall(r'<button[^>]*>[\s\S]*?</button>', buttons_html)
    for btn in buttons:
        btn_mod = btn.replace('class="tool-card"', f'class="tool-card" data-category="{cat_name}"')
        new_grid += f'                {btn_mod}\n'

new_grid += '            </div>\n        </div>\n\n'

html = html[:grids_start] + new_grid + html[workspace_start:]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. Update app.js
with open('static/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

old_logic = """  tab.addEventListener('click', () => {
    $$('.cat-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    $$('.tool-grid').forEach(g => g.classList.remove('active'));
    $(`#grid-${tab.dataset.cat}`).classList.add('active');
  });"""

new_logic = """  tab.addEventListener('click', () => {
    $$('.cat-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const cat = tab.dataset.cat;
    $$('.tool-card').forEach(card => {
       if (cat === 'all' || card.dataset.category === cat) {
           card.style.display = 'flex';
       } else {
           card.style.display = 'none';
       }
    });
  });"""

if old_logic in js:
    js = js.replace(old_logic, new_logic)
else:
    # If indentation is slightly different, do a regex replace
    js = re.sub(r"tab\.addEventListener\('click', \(\) => \{\s*\$\$\('\.cat-tab'\)\.forEach[^\}]+\}\);", new_logic, js)

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("UI Fixed.")
