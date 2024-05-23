from my_app import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey, delete




class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(50))
    national_id = db.Column(db.String(8), unique=True, nullable=False)
    phone = db.Column(db.String(20))

#creating the database for storing the information about our system users
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50))
    role = db.Column(db.String(10), default='user')
    verified = db.Column(db.Boolean, default=False)
    user_image = db.Column(db.LargeBinary)#For storing the image data directly into the database
    user_image_filename = db.Column(db.String(255))#For storing the image file name
    creation_date = db.Column(db.DateTime(timezone=True), default=func.now())
    status = db.Column(db.String(10), default='Active')

    # Additional fields
    phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    membership_type = db.Column(db.String(20))
    verification_code = db.Column(db.String(50))
    verification_code_expires = db.Column(db.DateTime)

    #Establishing relationships between users table and other tables in the database
    favourites = db.relationship('Favourites', backref='user', cascade="all, delete-orphan")
    library = db.relationship('User_Library', backref='user', cascade="all, delete-orphan")
    requested_books = db.relationship('Requested_books', backref='user', cascade="all, delete-orphan")
    issued_books = db.relationship('Issued_book_requests', backref='user', cascade="all, delete-orphan")
    returned = db.relationship('Returned_books', backref='user', cascade='all, delete-orphan')





#A database to store the information about all the books that we have in our libarary
class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100))
    author = db.Column(db.String(100))
    copies = db.Column(db.Integer)
    issued = db.Column(db.Integer)
    ISBN = db.Column(db.String(30), unique=True, nullable=False)
    book_preview_name = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # Foreign key to Category table

    #Relationships between books tables and other tables in the database
    favourites = db.relationship('Favourites', backref='books')
    library = db.relationship('User_Library', backref='books')
    requested_books = db.relationship('Requested_books', backref='books')
    hold_books = db.relationship('Hold_books', backref='books')
    issued_books = db.relationship('Issued_book_requests', backref='books')
    acquistion_date = db.Column(db.DateTime(timezone=True), default=func.now())
    returned = db.relationship('Returned_books', backref='books', cascade='all, delete-orphan')




#A database to show the categories of books available in our library
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    creation_date = db.Column(db.DateTime(timezone=True), default=func.now())
    updation_date = db.Column(db.DateTime(timezone=True), default=func.now())

    # Relationship with books (one-to-many: one category can have multiple books)
    books = db.relationship('Books', backref='category', cascade="all, delete-orphan")



class Favourites(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))



class User_Library(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))



class Borrowed_books(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    issued_id = db.Column(db.Integer, db.ForeignKey('issued_book_requests.id'))
    



class Requested_books(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    request_date = db.Column(db.DateTime(timezone=True), default=func.now())
    status = db.Column(db.String(20), default='pending')
    canceled_requests = db.relationship('Canceled_book_requests', backref='request')
    

class Hold_books(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    hold_date = db.Column(db.DateTime(timezone=True), default=func.now())
    status = db.Column(db.String(20), default='pending')
    canceled_hold_requests = db.relationship('Canceled_hold_requests', backref='hold')



class Issued_book_requests(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    issued_date = db.Column(db.DateTime(timezone=True), default=func.now())
    return_date = db.Column(db.DateTime(timezone=True))
    issued = db.relationship('Borrowed_books', uselist=False, backref='issued_request')



class Canceled_book_requests(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requested_books.id'), unique=True)
    cancel_date = db.Column(db.DateTime(timezone=True), default=func.now())


class Canceled_hold_requests(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hold_id = db.Column(db.Integer, db.ForeignKey('hold_books.id'), unique=True)
    cancel_date = db.Column(db.DateTime(timezone=True), default=func.now())



class Returned_books(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    return_date = db.Column(db.DateTime(timezone=True), default=func.now())
    overdue_days = db.Column(db.Integer)
    overdue_amount = db.Column(db.Integer)



# This class will be used to keep track of all the sent messages
class Sent_messages(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    receiver = db.Column(db.String(50), nullable=False)
    sending_date = db.Column(db.DateTime(timezone=True), default=func.now())
    subject = db.Column(db.String(100))
    email_content = db.Column(db.Text)