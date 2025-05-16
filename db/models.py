from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Author(db.Model):
  __tablename__ = 'authors'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  date_birth = db.Column(db.String(50))
  date_death = db.Column(db.String(50))
  photo = db.Column(db.String(200))
  country = db.Column(db.String(100))
  place_birth = db.Column(db.String(100))
  place_death = db.Column(db.String(100))
  biography = db.Column(db.Text)

  def __str__(self):
    return self.name


class Book(db.Model):
  __tablename__ = 'books'
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(200), nullable=False)
  author = db.Column(db.String(100), nullable=False)
  author_id = db.Column(db.ForeignKey('authors.id'))
  cover = db.Column(db.String(250))
  year = db.Column(db.String)
  genre = db.Column(db.String(50))
  rating = db.Column(db.Float)
  age = db.Column(db.Integer)
  language = db.Column(db.String(50))
  pages = db.Column(db.Integer)
  pdf_link = db.Column(db.String(250))

  def __str__(self):
    return self.title
  
  def __repr__(self):
    return f'<Book {self.title}>'
     
  
  
class BookShare(db.Model):
    __tablename__ = 'book_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    network = db.Column(db.String(20), nullable=False)  # vk, telegram, whatsapp, copy
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Связь с книгой
    book = db.relationship('Book', backref=db.backref('shares_rel', lazy='dynamic'))
    
    def __repr__(self):
        return f'<BookShare {self.book_id} - {self.network}>'