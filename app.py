import os
import random
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, url_for, request, jsonify, flash, redirect, send_from_directory, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from db.db import get_all_authors, get_all_books, get_authors, get_book, get_books_by_genre
from db.models import Author, Book, db, BookShare
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'db' / 'db.sqlite3'


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'


class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key = True)
  username = db.Column(db.String(80), unique = True, nullable = False)
  password_hash = db.Column(db.String(120), nullable = False)

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)
  

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))


class SecureModelView(ModelView):
  def is_accesible(self):
    return current_user.is_authenticated
  
  def inaccesible_callback(self, name, **kwargs):
    return redirect(url_for('admin_login', next = request.url))
  
class AuthorModelView(SecureModelView):
  column_list = ['id', 'name', 'country', 'date_birth', 'date_death']
  column_searchable_list = ['name', 'country', 'biography']
  column_filters = ['country']
  form_columns = ['name', 'date_birth', 'date_death', 'photo', 'country', 'place_birth', 'place_death', 'biography']
  column_tabels = {
    'name': 'Имя',
    'date_birth': 'Дата рождения',
    'date_death': 'Дата смерти',
    'photo': 'Фото',
    'country': 'Страна',
    'place_birth': 'Место рождения',
    'place_death': 'Место смерти',
    'biography': 'Биография'
  }
  page_size = 20
  can_view_details = True
  can_export = True
  column_formatters = {'photo': lambda v, c, m, p: m.photo[:30] + '...' if m.photo and len(m.photo) > 30 else m.photo}


class BookModelView(SecureModelView):
  column_list = ['id', 'title', 'author', 'year', 'genre', 'rating']
  column_searchable_list = ['title', 'author', 'genre']
  column_filters = ['genre', 'language', 'year']
  form_columns = ['title', 'author', 'author_id', 'cover', 'year', 'genre', 'rating', 'age', 'language', 'pages', 'pdf_link']
  column_tabels = {
    'title': 'Название',
    'author': 'Автор',
    'author_id': 'ID автора',
    'cover': 'Обложка',
    'year': 'Год',
    'genre': 'Жанр',
    'rating': 'Рейтинг',
    'age': 'Возрастное ограничение',
    'language': 'Язык',
    'pages': 'Количество страниц',
    'pdf_link': 'Ссылка на PDF'
  }
  page_size = 20
  can_view_details = True
  can_export = True
  column_formatters = {
    'cover': lambda v, c, m, p: m.cover[:30] + '...' if m.cover and len(m.cover) > 30 else m.cover,
    'author_id': lambda v, c, m, p: m.aythor_rel.name if m.aythor_rel else '',
    'pdf_link': lambda v, c, m, p: m.pdf_link[:30] + '...' if m.pdf_link and len(m.pdf_link) > 30 else m.pdf_link
  }


  @expose('/upload_pdf/<book_id>', methods = ['GET', 'POST'])
  def upload_pdf_view(self, book_id):
    book = Book.query.get(book_id)
    if not book:
      flash('Книга не найдена', 'error')
      return redirect(url_for('book.index_view'))
    pdf_path = os.path.join(app.static_folder, 'books', f'{book_id}.pdf')
    pdf_exists = os.path.exists(pdf_path)
    return render_template('admin/upload_pdf.html', book = book, pdf_exists = pdf_exists, pdf_url = url_for('static_file', filename = f'books/{book_id}.pdf') if pdf_exists else None)
  
  def _list_entry_action(seld, context, row_id, row):
    actions = super()._list_entry_actoion(context, row_id, row)
    actions.append({
      'url': url_for('.upload_pdf_view', book_id = row_id),
      'title': 'Загрузить PDF',
      'icon_class': 'fa fa-upload'
    })
    return actions


class SecureAdminIndexView(AdminIndexView):
  def is_accessible(self):
    return current_user.is_authenticated

  def inaccessible_callback(self, name, **kwargs):
    return redirect(url_for('admin_login', next = request.url))


with app.app_context():
  db.create_all()
  if not User.query.filter_by(username = 'admin').first():
    admin_user = User(username = 'admin')
    admin_user.set_password('admin')
    db.session.add(admin_user)
    db.session.commit()


admin = Admin(app, name = 'OpenLib Admin', template_mode = 'bootstrap4', index_view = SecureAdminIndexView(), base_template = 'admin/master.html')
admin.add_view(AuthorModelView(Author, db.session, name = 'Авторы', endpoint = 'author'))
admin.add_view(BookModelView(Book, db.session, name = 'Книги', endpoint = 'book'))


@app.route('/admin/login', methods = ['GET', 'POST'])
def admin_login():
  if current_user.is_authenticated:
    return redirect(url_for('admin.index'))
  
  form_errors = []
  if request.method == 'POST':
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
      form_errors.append('Пожалуйста, заполните все поля')
    else:
      user = User.query.filter_by(username = username).first()
      if user and user.check_password(password):
        login_user(user)
        next_page = request.args.get('next')
        if next_page:
          return redirect(next_page)
        return redirect(url_for('admin.index'))
      else:
        form_errors.append('Неверное имя пользователя или пароль')
    for error in form_errors:
      flash(error, 'danger')
  return render_template('admin/login.html', title = 'Вход в админ-панель', form_errors = form_errors, admin_view={'admin': admin})


@app.route('/admin/logout')
@login_required
def admin_logout():
  logout_user()
  return redirect(url_for('index_view'))


@app.route("/")
def index_view():
  random_placeholder = random.choice(["крутая книга", "современный автор", "в топе"])
  return render_template("pages/index.html", title="главная", random_placeholder=random_placeholder)


@app.route("/static/<filename>")
def static_file(filename):
  return app.send_static_file(filename)


@app.route("/books")
def books_view():
  books = get_all_books()
  genres = set()
  for book in books:
    if book['genre']:
      genres.add(book['genre'])
  genres = sorted(list(genres))
  return render_template("pages/books.html", title = "Книги", books = books, genres = genres)


@app.route("/books/genre/<string:genre>")
def books_genre_view(genre):
  books = get_books_by_genre(genre)
  if not books:
    return "Oops! There are no books with that genre"
  return render_template("pages/books.html", title="Книги по жанру " + genre, books=books)


@app.route("/books/<id>")
def book_view(id):
  book = get_book(id)
  if not book:
    return 'Oops! Book not found', 404
  
  if 'author_id' not in book or not book['author_id']:
    author_name = book['author']
    author = Author.query.filter(Author.name == author_name).first()
    if author:
      book['author_id'] = author.id
    else:
      book['author_id'] = None
  
  print(f"Book data: {book}")
  print(f"Author ID: {book['author_id']}, type: {type(book['author_id'])}")

  random_books = random.sample(get_all_books(), min(3, len(get_all_books())))

  if book.get('pdf_link'):
    book_link = book['pdf_link']
  else:
    book_link = url_for('static_file', filename = 'books/' + str(book['id']) + '.pdf')
  
  pdf_exist = os.path.exists(os.path.join(app.static_folder, 'books', f"{book['id']}.pdf"))

  return render_template('pages/book.html', title = book['title'], book = book, random_books = random_books, book_link = book_link, pdf_exist = pdf_exist)


@app.route('/api/share', methods=['POST'])
def register_share():
  """API для регистрации статистики 'поделиться'"""
  if not request.is_json:
    return jsonify({'success': False, 'error': 'Invalid request'}), 400
  
  data = request.get_json()
  book_id = data.get('book_id')
  network = data.get('network')
  
  if not book_id or not network:
    return jsonify({'success': False, 'error': 'Missing data'}), 400
  
  # Проверяем, что книга существует
  book = Book.query.get(book_id)
  if not book:
    return jsonify({'success': False, 'error': 'Book not found'}), 404
  
  # Создаем запись о поделиться
  share = BookShare(book_id=book_id, network=network, timestamp=datetime.now())
  db.session.add(share)
  db.session.commit()
  
  # Получаем общее количество поделиться для этой книги
  share_count = BookShare.query.filter_by(book_id=book_id).count()
  
  return jsonify({
  'success': True, 
    'book_id': book_id, 
    'share_count': share_count
  })


@app.route("/authors")
def authors_view():
  authors = get_all_authors()
  return render_template("pages/authors.html", authors=authors, title='Авторы')


@app.route("/authors/<int:id>")
def author_view(id):
  author = get_authors(id)
  if not author:
    return 'Oops! Author not found', 404
  
  books = []
  all_books = get_all_books()
  for book in all_books:
    if book['author_id'] and isinstance(book["author_id"], int) and book['author_id'] == id:
      books.append(book)

  similar_authors = random.sample(get_all_authors(), min(3, len(get_all_authors())))
  similar_authors_list = []

  for author_id in similar_authors:
    for aut in get_all_authors():
      if aut["id"] == author_id and author['id'] != id:
        similar_authors_list.append(author)

  return render_template("pages/author.html", author=author, similar_authors=similar_authors_list, title=author['name'], author_books = books)


@app.route('/contacts')
def contacts_view():
  return render_template('pages/contacts.html', title='Контакты')


@app.route('/dcma')
def dcma_view():
  return render_template('pages/dcma.html', title='Правообладателям')


@app.route('/search')
def search_view():
  query = request.args.get('q', '').strip()
  if not query:
    return render_template('pages/search.html', query='', books=[], authors=[])
  
  books = Book.query.filter(
    db.or_(Book.title.ilike(f'%{query}%'), Book.author.ilike(f'%{query}%'),Book.genre.ilike(f'%{query}%'))).all()

  authors = Author.query.filter(
    db.or_(Author.name.ilike(f'%{query}%'), Author.country.ilike(f'%{query}%'), Author.biography.ilike(f'%{query}%'))).all()

  return render_template('pages/search.html', query=query, books=books, authors=authors)

def migrate_data():
  from db.db import get_all_authors, get_all_books
  
  with app.app_context():
    db.create_all()
    Book.query.delete()
    Author.query.delete()
    author = get_all_authors()
    authors_dict = {}
    authors = get_all_authors()

    for author_data in authors:
      author = Author(**author_data)
      db.session.add(author)
      authors_dict[author.name] = author.id

    books = get_all_books()
    for book_data in books:
      book_data_copy = book_data.copy()
      if 'author_id' in book_data_copy:
        del book_data_copy['author_id']

      book = Book(**book_data_copy)
      author_name = book_data['author']
      if author_name in authors_dict:
        book.author_id = authors_dict[author_name]

      db.session.add(book)

    db.session.commit()
    print("Данные успешно перенесены в новую базу данных")


@app.route('/admin/upload_pdf', methods=['POST'])
@login_required
def upload_pdf():
  if 'pdf_file' not in request.files:
    flash('Файл не выбран', 'error')
    return redirect(request.referrer)
  file = request.files['pdf_file']
  book_id = request.form.get('book_id')

  if file.filename == '':
    flash('Файл не выбран', 'error')
    return redirect(request.referrer)

  if not book_id:
    flash('ID книги не указан', 'error')
    return redirect(request.referrer)

  pdf_dir = os.path.join(app.static_folder, 'books')
  
  if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)

  filename = f"{book_id}.pdf"
  file_path = os.path.join(pdf_dir, filename)
  file.save(file_path)
  book = Book.query.get(book_id)

  if book:
    book.pdf_link = url_for('static_file', filename=f'books/{filename}')
    db.session.commit()
    flash('PDF файл успешно загружен', 'success')
  else:
    flash('Книга не найдена', 'error')

  return redirect(request.referrer)


@app.route('/read/<int:book_id>')
def read_pdf(book_id):
  book = get_book(book_id)
  if not book:
    return "Oops! Book not found", 404
  
  if book.get('pdf_link'):
    return redirect(book['pdf_link'])
  
  pdf_path = os.path.join(app.static_folder, 'books', f'{book_id}.pdf')
  if os.path.exist(pdf_path):
    return send_from_directory(os.path.join(app.static_folder, 'books'), f'{book_id}.pdf')
  
  return "Oops! PDF not found", 404

if __name__ == '__main__':
  migrate_data()
  app.run(debug=True)