import os
import random
from pathlib import Path
from flask import Flask, render_template, url_for, request
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from db.db import get_all_authors, get_all_books, get_authors, get_book, get_books_by_genre
from db.models import Author, Book, db
import json

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'db' / 'db.sqlite3'


app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)


with app.app_context():
	db.create_all()


admin = Admin(app, name='OpenLib Admin', template_mode='bootstrap3')
admin.add_view(ModelView(Author, db.session))
admin.add_view(ModelView(Book, db.session))


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
  return render_template("pages/books.html", title="Книги", books=books)


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
  
  random_books = random.sample(get_all_books(), 3)
  book_link = url_for('static_file', filename='books/' + str(book['id']) + '.pdf')
  return render_template('pages/book.html', title=book['title'], book=book, random_books=random_books, book_link=book_link)


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

  print('это в app.py:', author, "\nэто get_all_authors() из db.py", get_all_authors())
  return render_template("pages/author.html", author=author, similar_authors=similar_authors_list, title=author['name'])


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


if __name__ == '__main__':
  migrate_data()
  app.run(debug=True)