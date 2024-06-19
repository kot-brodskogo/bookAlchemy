from datetime import datetime
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from data_models import db, Author, Book

# Create an instance of the Flask application
app = Flask(__name__)

# Configure the SQLAlchemy part of the application instance
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data/library.sqlite'

# Get the absolute path for the current directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Ensure the 'data' directory exists
data_dir = os.path.join(basedir, 'data')
os.makedirs(data_dir, exist_ok=True)

# Configure the SQLAlchemy part of the application instance
database_file = os.path.join(data_dir, 'library.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_file}'

# Initialize the SQLAlchemy app with the Flask app
db.init_app(app)


@app.route('/')
def home():
    # Get the sorting criterion from the request arguments
    sort_by = request.args.get('sort_by', 'title')  # Default to sorting by title

    # Query books and their authors with sorting
    sort_by = request.args.get('sort_by', 'title')
    if sort_by == 'author':
        books = Book.query.join(Author).order_by(Author.name).all()
    elif sort_by == 'title':
        books = Book.query.order_by(Book.title).all()
    else:
        books = Book.query.all()

    # Prepare data for rendering
    books_data = []
    for book in books:
        author_name = book.author.name if book.author else 'Unknown'
        # Get cover image URL based on ISBN
        cover_image_url = f"https://covers.openlibrary.org/b/isbn/{book.isbn}-M.jpg?default=false"

        books_data.append({
            'title': book.title,
            'author': author_name,
            'cover_image_url': cover_image_url
        })

    return render_template('home.html', books=books_data)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():
    if request.method == 'POST':
        # Get author details from the form
        name = request.form['name']
        birth_date_str = request.form['birth_date']
        date_of_death_str = request.form['date_of_death']

        # Convert date strings to date objects
        birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        date_of_death = datetime.strptime(date_of_death_str, '%Y-%m-%d').date() if date_of_death_str else None

        # Create a new Author object
        new_author = Author(name=name, birth_date=birth_date, date_of_death=date_of_death)

        # Add the new author to the database
        db.session.add(new_author)
        db.session.commit()

        # Provide feedback to the user
        message = "Author added successfully!"

        return render_template('add_author.html', message=message)

    # If it's a GET request, render the form
    return render_template('add_author.html')


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        # Get book details from the form
        isbn = request.form['isbn']
        title = request.form['title']
        publication_year = request.form['publication_year']
        author_id = request.form['author_id']

        # Create a new Book object
        new_book = Book(isbn=isbn, title=title, publication_year=publication_year, author_id=author_id)

        # Add the new book to the database
        db.session.add(new_book)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            message = "A book with that ISBN already exists."
            authors = Author.query.all()  # Fetch all authors from the database
            return render_template('add_book.html', authors=authors, message=message)

        # Redirect to the add book page to reset the form
        return redirect(url_for('add_book', message="Book added successfully!"))

    # If it's a GET request, render the form
    authors = Author.query.all()  # Fetch all authors from the database
    message = request.args.get('message', '')
    return render_template('add_book.html', authors=authors, message=message or None)


# Run the application
if __name__ == '__main__':
    # To create the tables, you need to run db.create_all() once
    # Uncomment the lines below, run the file once to create the tables, and then comment them out again.
    # with app.app_context():
    #     db.create_all()

    app.run(debug=True)
