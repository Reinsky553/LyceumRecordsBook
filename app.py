import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from private import ADMIN_USER, ADMIN_PASS_HASH, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # 1. Категории
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT NOT NULL, 
                       display_order INTEGER DEFAULT 0)''')
    # 2. Страницы
    cursor.execute('''CREATE TABLE IF NOT EXISTS pages 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       category_id INTEGER, 
                       title TEXT, 
                       content TEXT, 
                       page_order INTEGER DEFAULT 0,
                       FOREIGN KEY(category_id) REFERENCES categories(id))''')
    # 3. Предложения
    cursor.execute('''CREATE TABLE IF NOT EXISTS submissions 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT, contact TEXT, category TEXT, 
                       content TEXT, status TEXT DEFAULT 'pending')''')
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USER and check_password_hash(ADMIN_PASS_HASH, password):
            session['logged_in'] = True
            session.permanent = True 
            return redirect(url_for('admin'))
        
        flash("Неверные учетные данные")
    return render_template('login.html')

@app.route('/api/get_categories')
def get_categories():
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY display_order ASC")
        return jsonify([row['name'] for row in cursor.fetchall()])

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if request.method == 'POST':
            if 'add_cat' in request.form:
                cursor.execute("INSERT INTO categories (name, display_order) VALUES (?, ?)",
                               (request.form['cat_name'], request.form['cat_order']))
            elif 'delete_cat' in request.form:
                cat_id = request.form['cat_id']
                cursor.execute("DELETE FROM pages WHERE category_id = ?", (cat_id,))
                cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            elif 'add_page' in request.form:
                img = request.form.get('p_image')
                content = request.form['p_content']
                if img:
                    content = f'<div class="photo-page"><img src="{img}"><p>{content}</p></div>'
                cursor.execute("INSERT INTO pages (category_id, title, content, page_order) VALUES (?, ?, ?, ?)",
                               (request.form['cat_id'], request.form['p_title'], content, request.form['p_order']))
            elif 'delete_page' in request.form:
                cursor.execute("DELETE FROM pages WHERE id = ?", (request.form['page_id'],))
            elif 'delete_sub' in request.form:
                cursor.execute("DELETE FROM submissions WHERE id = ?", (request.form['sub_id'],))
            conn.commit()
            return redirect(url_for('admin'))

        cursor.execute("SELECT * FROM categories ORDER BY display_order ASC")
        cats = cursor.fetchall()
        cursor.execute("""SELECT pages.*, categories.name as cat_name FROM pages 
                          JOIN categories ON pages.category_id = categories.id 
                          ORDER BY categories.display_order, pages.page_order""")
        all_pages = cursor.fetchall()
        cursor.execute("SELECT * FROM submissions ORDER BY id DESC")
        subs = cursor.fetchall()
    return render_template('admin.html', categories=cats, pages=all_pages, submissions=subs)

@app.route('/api/get_pages')
def get_pages():
    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Заглавная страница
        book_pages = [{"title": "Книга рекордов Лицея", "html": "<div class='cover-page'><h1>2026</h1><p>Книга рекордов Лицея</p></div>"}]
        
        cursor.execute("SELECT id, name FROM categories ORDER BY display_order ASC")
        categories = cursor.fetchall()
        
        current_page_num = 3 
        toc_entries = []
        category_data = []

        for cat in categories:
            toc_entries.append({"name": cat['name'], "page": current_page_num})
            
            # Считает страницы для каждой категории
            cursor.execute("SELECT title, content FROM pages WHERE category_id = ? ORDER BY page_order ASC", (cat['id'],))
            pages = cursor.fetchall()
            
            category_data.append({"name": cat['name'], "pages": pages})
            current_page_num += 1 + len(pages)

        toc_html = "<div class='toc-page'><ul class='toc-list'>"
        for entry in toc_entries:
            toc_html += f"<li class='toc-link' data-target='{entry['name']}'>{entry['name']} <span class='toc-page-num'>{entry['page']}</span></li>"
        toc_html += "</ul></div>"
        
        book_pages.append({"title": "Содержание", "html": toc_html})
        
        for cat_item in category_data:
            book_pages.append({"title": "", "html": f"<div class='category-title-page'><h1>{cat_item['name']}</h1></div>"})
            for p in cat_item['pages']:
                book_pages.append({"title": p['title'], "html": p['content']})
                
        return jsonify(book_pages)

@app.route('/submit_entry', methods=['POST'])
def submit_entry():
    name, contact = request.form.get('name'), request.form.get('contact')
    category = request.form.get('category')
    if category == "other": category = request.form.get('custom_category')
    content = request.form.get('content')
    with sqlite3.connect('database.db') as conn:
        conn.execute("INSERT INTO submissions (name, contact, category, content) VALUES (?, ?, ?, ?)",
                     (name, contact, category, content))
    return jsonify({"status": "success", "message": "Submitted for review!"})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)