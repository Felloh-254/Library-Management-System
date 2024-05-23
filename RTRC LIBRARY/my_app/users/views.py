from flask import Flask, Blueprint, render_template, request, url_for, flash, redirect, jsonify, abort, current_app
from random import sample #For generating random books for the user at the recommended books section
from flask_login import current_user, login_user, login_required
from my_app import db
import os
from my_app.models import User, Books, Category, Favourites, User_Library, Requested_books, Borrowed_books, Issued_book_requests, Hold_books
from my_app.auth import verified_required
from datetime import datetime
from sqlalchemy import and_, or_

user_view_blueprint = Blueprint('userView', __name__, url_prefix='/')

# @app.context_processor
# def utility_processor():
#     def file_exists(filepath):
#         return os.path.exists(os.path.join(current_app.static_folder, filepath))
    
#     return dict(file_exists=file_exists)


@user_view_blueprint.route('/')
def homePage():
    return render_template('shared/home.html')


@user_view_blueprint.route('/home', methods=['GET', 'POST'])
@login_required
@verified_required
def home():
    authenticate()
    
    # Initialize filtered_books as an empty list
    filtered_books = []

    # Check if it's a POST request and call search_books function
    if request.method == 'POST':
        filtered_books = search_books()
        
        # Convert Books objects to dictionaries
        filtered_books_dict = [
            {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'ISBN': book.ISBN,
                'issued': book.issued,
                'copies': book.copies,
                'book_preview_name': book.book_preview_name
            }
            for book in filtered_books
        ]

        print(filtered_books)
        
        # Return filtered books as JSON
        return render_template(
            'partials/searched_books.html',
            filtered_books=filtered_books,
            user=current_user
        )

    # Fetch random books, categories, and all books
    random_books = fetch_random_books()
    categories = Category.query.all()
    books = Books.query.all()
    
    # Fetch favorite books and library books of the current user
    favorite_books = Favourites.query.filter_by(user_id=current_user.id).all()
    library_books = User_Library.query.filter_by(user_id=current_user.id).all()
    
    # Get the IDs of favorite books and library books
    favorite_book_ids = [favorite.book_id for favorite in favorite_books]
    library_book_ids = [library.book_id for library in library_books]

    total_library_books = User_Library.query.count() #.filter(user_id=user)
    total_favourite_books = Favourites.query.count() #.filter(user_id=user)
    total_issued_books = Issued_book_requests.query.count() #.filter(user_id=user)
    total_pending_requests = Requested_books.query.count() #.filter(user_id=user, status='pending')

    if total_issued_books == 0:
        total_issued_books = 0

    if total_library_books == 0:
        total_library_books = 0

    if total_favourite_books == 0:
        total_favourite_books = 0

    if total_pending_requests == 0:
        total_pending_requests = 0

    return render_template(
        'user/home.html',
        user=current_user,
        random_books=random_books,
        books=books,
        total_issued_books=total_issued_books,
        total_library_books=total_library_books,
        total_favourite_books=total_favourite_books,
        total_pending_requests=total_pending_requests,
        categories=categories,
        favorite_book_ids=favorite_book_ids,
        library_book_ids=library_book_ids,
        filtered_books=filtered_books
    )


# @user_view_blueprint.route('/search_books', methods=['POST'])
def search_books():
    search_criteria = request.form.get('search_book_criteria')
    search_content = request.form.get('search_field_content').lower()

    # Create a base query
    base_query = Books.query

    print("Criteria: ", search_criteria)
    print("content: ", search_content)

    # Filter books based on search criteria
    if search_content:
        if search_criteria == 'Title':
            base_query = base_query.filter(Books.title.ilike(f'%{search_content}%'))
        elif search_criteria == 'Author':
            base_query = base_query.filter(Books.author.ilike(f'%{search_content}%'))
        elif search_criteria == 'ISBN':
            base_query = base_query.filter(Books.ISBN.ilike(f'%{search_content}%'))
        elif search_criteria == 'Category':
            base_query = base_query.join(Category).filter(Category.name.ilike(f'%{search_content}%'))

    # Fetch filtered books
    filtered_books = base_query.all()
    print("Filtered from base: ", filtered_books)
    return filtered_books



#For fetching random books from the database and displaying them on the recommended section
def fetch_random_books():
    # Fetch all books from the database
    all_books = Books.query.all()

    # We use the sample() to limit the number of random books to be fetched
    num_random_books = 5
    random_books = sample(all_books, num_random_books)

    # Construct a list of dictionaries containing book details
    books_list = []
    for book in random_books:
        books_list.append({
            'ISBN': book.ISBN,
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'preview': book.book_preview_name 
        })

    return books_list 


# @user_view_blueprint.route('/autocomplete', methods=['GET'])
# def autocomplete():
#     search_term = request.args.get('term').lower()
    
#     # Fetch book titles that match the search term
#     books = Books.query.filter(Books.title.ilike(f'%{search_term}%')).limit(10).all()
    
#     # Extract book titles
#     suggestions = [book.title for book in books]
    
#     return jsonify({'suggestions': suggestions})





@user_view_blueprint.route('/request_book', methods=['POST'])
@login_required
@verified_required
def request_book():
    authenticate()
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        existing_request = Requested_books.query.filter(
            Requested_books.book_id == book_id,
            Requested_books.user_id == current_user.id,
            Requested_books.status.in_(['issued', 'pending'])
        ).first()

        if existing_request:
            # flash('Book already requested by you and pending or issued!!', category='error')
            return jsonify({"message": "Book already requested by you and pending or issued!!"}), 400
        else:
            new_request = Requested_books(book_id=book_id, user_id=current_user.id)
            db.session.add(new_request)
            db.session.commit()
            # flash('Book request was successful!!')
            return jsonify({"message": "Book request was successful!!"}), 200



# @user_view_blueprint.route('/hold_book', methods=['POST'])
# @login_required
# @verified_required
# def hold_book():
#     authenticate()
#     if request.method == 'POST':
#         book_id = request.form.get('book_id')
#         existing_hold = Hold_books.query.filter(
#             Hold_books.book_id == book_id,
#             Hold_books.user_id == current_user.id,
#             Requested_books.status.in_(['issued', 'pending'])
#         ).first()

#         if existing_hold:
#             return jsonify({"message": "Book already put on hold by you and pending or issued"}), 400
#         else:
#             new_hold = Hold_books(book_id=book_id, user_id=current_user.id)
#             db.session.add(new_hold)
#             db.session.commit()
#             return jsonify({"message": "Book Reservation is successful. Please Remeber to pick within one week"}), 200




@user_view_blueprint.route('/toggle_favorite', methods=['POST'])
@login_required
@verified_required
def toggle_favorite():
    authenticate()
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        favorite_entry = Favourites.query.filter_by(user_id=current_user.id, book_id=book_id).first()

        if favorite_entry:
            db.session.delete(favorite_entry)
            db.session.commit()
            return jsonify({"message": "Book removed from favorites successfully"}), 200
        else:
            new_favorite_entry = Favourites(user_id=current_user.id, book_id=book_id)
            db.session.add(new_favorite_entry)
            db.session.commit()
            return jsonify({"message": "Book added to favorites successfully"}), 200



@user_view_blueprint.route('/toggle_library', methods=['POST'])
@login_required
@verified_required
def toggle_library():
    authenticate()
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        library_entry = User_Library.query.filter_by(user_id=current_user.id, book_id=book_id).first()

        if library_entry:
            db.session.delete(library_entry)
            db.session.commit()
            return jsonify({"message": "Book removed from library successfully"}), 200
        else:
            new_library_entry = User_Library(user_id=current_user.id, book_id=book_id)
            db.session.add(new_library_entry)
            db.session.commit()
            return jsonify({"message": "Book added to library successfully"}), 200




@user_view_blueprint.route('/borrowedBooks')
@login_required
@verified_required
def borrowedBooks():
    authenticate()
    borrowed_books = Issued_book_requests.query.filter_by(user_id=current_user.id).all()
    current_date = datetime.now().date()

    overdue_details = []  # List to hold overdue details for each book

    for book in borrowed_books:
        # We will be calculating the overdue days
        if current_date > book.return_date.date():  # Convert return_date to date object
            overdue_days = (current_date - book.return_date.date()).days
        else:
            overdue_days = 0

        # Calculating the overdue amount
        overdue_amount = overdue_days * 10

        # Append overdue details to the list
        overdue_details.append((overdue_days, overdue_amount))

    # Pass borrowed_books and overdue_details to the template context
    return render_template('user/borrowedBooks.html', borrowed_books=borrowed_books, user=current_user, overdue_details=overdue_details)




@user_view_blueprint.route('/borrowedBooks/sentRequests', methods=['GET'])
@login_required
@verified_required
def showSentRequests():
    return sentRequests()


def sentRequests():
    authenticate()

    requests = Requested_books.query.filter_by(status='pending').all()
    return render_template('user/sent_requests.html', requests=requests, user=current_user)



@user_view_blueprint.route('/borrowedBooks/deleteSentRequests', methods=['POST'])
@login_required
@verified_required
def processRequestDeletion():
    authenticate()
    return delete_request()


def delete_request():
    book_id = request.form.get('book_id')
    book_to_cancel = Requested_books.query.filter_by(book_id=book_id).first()
    if book_to_cancel:
        db.session.delete(book_to_cancel)
        db.session.commit()
        # db.session.refresh(book_to_cancel)
    return redirect(url_for('userView.showSentRequests'))




@user_view_blueprint.route('/library', methods=['GET'])
@login_required
@verified_required
def myLibrary():
    authenticate()
    # Fetch books from the users library
    my_library = User_Library.query.filter_by(user_id=current_user.id).all()
    return render_template('user/myLibrary.html', my_library=my_library, user=current_user)
    


@user_view_blueprint.route('/library/deleteFromLibrary', methods=['POST'])
@login_required
@verified_required
def deleteFromMyLibrary():
    book_id = request.form.get('book_id')
    book = User_Library.query.filter_by(book_id=book_id, user_id=current_user.id).first()

    if book:
        db.session.delete(book)
        db.session.commit()
        flash('Book removed form My Library successfully', category='success')
        return redirect(url_for('userView.myLibrary'))

    flash("Action can't be completed. Book does not exist your library!!", category='error')
    return redirect(url_for('userView.myLibrary'))



@user_view_blueprint.route('/favourites', methods=['GET', 'POST'])
@login_required
@verified_required
def favourites():
    authenticate()
    favourite_books = Favourites.query.filter_by(user_id=current_user.id).all()

    return render_template('user/favourites.html', favourite_books=favourite_books, user=current_user)


@user_view_blueprint.route('/favourites/deleteFromFavourites', methods=['POST'])
@login_required
@verified_required
def deleteFromMyFavourites():
    book_id = request.form.get('book_id')
    book = Favourites.query.filter_by(book_id=book_id, user_id=current_user.id).first()

    if book:
        db.session.delete(book)
        db.session.commit()
        flash('Book removed form Favourites successfully', category='success')
        return redirect(url_for('userView.favourites'))
    
    flash("Action can't be completed. Book does not exist in favorites!!", category='error')
    return redirect(url_for('userView.favourites'))



@user_view_blueprint.route('/support')
@login_required
@verified_required
def user_support():
    return render_template('user/support.html', user=current_user)



@user_view_blueprint.route('/history', methods=['GET'])
@login_required
@verified_required
def borrowing_history():
    bookHistory = Requested_books.query.filter_by(user_id=current_user.id).all()

    # Sort the bookHistory by request_date in descending order
    bookHistory = sorted(bookHistory, key=lambda x: x.request_date, reverse=True)
    
    return render_template('user/borrowingHistory.html', bookHistory=bookHistory, user=current_user)



def authenticate():
    #Only do this when the role of that particular person is admin
    if current_user.role != 'user':
        abort(403)#we will return a forbidden error if the user is not admin










