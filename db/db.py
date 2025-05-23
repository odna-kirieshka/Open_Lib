import json
import sqlite3
from pathlib import Path
from db.models import BookShare

DB_PATH = Path(__file__).parent / "db.sqlite3"


def get_db():
  return sqlite3.connect(DB_PATH)


def init_db():
  conn = get_db()
  cur = conn.cursor()

  cur.execute("""CREATE TABLE IF NOT EXISTS authors(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  date_birth TEXT,
  date_death TEXT,
  photo TEXT,
  country TEXT,
  place_birth TEXT,
  place_death TEXT,
  biography TEXT
  )""")

  cur.execute("""CREATE TABLE IF NOT EXISTS books(
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT,
  author_id INTEGER,
  cover TEXT,
  year TEXT,
  genre TEXT,
  rating TEXT,
  age TEXT,
  language TEXT,
  pages INTEGER,
  pdf_link TEXT,
  FOREIGN KEY (author_id) REFERENCES authors (id)
  )""")

  conn.commit()
  conn.close()


def load_data():
  conn = get_db()
  cur = conn.cursor()

  with open(Path(__file__).parent / "authors.json", "r", encoding="utf-8") as f:
    authors = json.load(f)
    for author in authors:
      cur.execute("""INSERT OR REPLACE INTO authors(id, name, date_birth, date_death, photo, country, place_birth, place_death, biography)VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
          author["id"],
          author["name"],
          author["date_birth"],
          author["date_death"],
          author["photo"],
          author["country"],
          author["place_birth"],
          author["place_death"],
          author["biography"],
        ),
      )

  with open(Path(__file__).parent / "books.json", "r", encoding="utf-8") as f:
    books = json.load(f)
    for book in books:
      author_name = book['author']
      author_id = None
      author_row = cur.execute('SELECT id FROM authors WHERE name = ?', (author_name,)).fetchone()
      if author_row:
        author_id = author_row[0]

      cur.execute("""INSERT OR REPLACE INTO books(id, title, author, author_id, cover, year, genre, rating, age, language, pages, pdf_link)VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
          book["id"],
          book["title"],
          book["author"],
          author_id,
          book["cover_link"],
          book["year"],
          book["genre"],
          book["rating"],
          book["age"],
          book["language"],
          book["pages"],
          book.get('pdf_link', None)
        )
      )

  conn.commit()
  conn.close()


def get_all_books():
  conn = get_db()
  cur = conn.cursor()
  books = cur.execute("SELECT * FROM books").fetchall()

  cur.execute("PRAGMA table_info(books)")
  columns = [column[1] for column in cur.fetchall()]

  result = [dict(zip(columns, book)) for book in books]
  conn.close()
  return result


def get_books_by_genre(books_genre):
  conn = get_db()
  cur = conn.cursor()
  books = cur.execute("SELECT * FROM books WHERE genre = ?", (books_genre,)).fetchall()
  if books:
    cur.execute("PRAGMA table_info(books)")
    columns = [column[1] for column in cur.fetchall()]
    result = [dict(zip(columns, book)) for book in books]
  else:
    result = None

  conn.close
  return result


def get_book(book_id):
  conn = get_db()
  cur = conn.cursor()
  book = cur.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

  if book:
    cur.execute("PRAGMA table_info(books)")
    columns = [column[1] for column in cur.fetchall()]
    result = dict(zip(columns, book))
  else:
    result = None

  conn.close()

  # book_shares = BookShare.query.filter_by(book_id=book_id).count()
  result["book_shares"] = BookShare.query.filter_by(book_id=book_id).count()
  return result


def get_all_authors():
  conn = get_db()
  cur = conn.cursor()

  cur.execute("PRAGMA table_info(authors)")
  columns = [column[1] for column in cur.fetchall()]

  authors = cur.execute("SELECT * FROM authors").fetchall()

  result = []
  for author in authors:
    author_dict = {}
    for i, column in enumerate(columns):
      author_dict[column] = author[i]
    result.append(author_dict)

  conn.close()
  return result


def get_authors(author_id):
  conn = get_db()
  cur = conn.cursor()

  cur.execute("PRAGMA table_info(authors)")
  columns = [column[1] for column in cur.fetchall()]

  author = cur.execute("SELECT * FROM authors WHERE id = ?", (author_id,)).fetchone()

  if author:
    result = {}
    for i, column in enumerate(columns):
      result[column] = author[i]
  else:
    result = None

  conn.close()
  print("это в db.py:", result)
  return result


if __name__ == "__main__":
  init_db()
  load_data()
  print("База данных инициализированна")