from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from flask_login import login_required, current_user
from my_app.models import Books, Category, User, Requested_books, Returned_books, Issued_book_requests, Canceled_book_requests, Sent_messages, Favourites, User_Library, Borrowed_books
from my_app import db, mail
import json
from datetime import datetime, timedelta
from sqlalchemy import and_, func
from flask_mail import Message
from my_app.auth import verified_required
from werkzeug.utils import secure_filename
import os
import calendar

admin_blueprint = Blueprint('admin', __name__, url_prefix='/')



############..........DASHBOARD...........####################
@admin_blueprint.route('/dashboard')
@login_required
def dashboard():
    authenticate()
    #we want to display the total count of books and book categories in our library on the dashboard
    #we first start by counting the total books and book categories in the database
    total_books = Books.query.count()
    total_overdue_amount = total_overdues()
    total_category = Category.query.count()
    total_user = User.query.filter(User.role != 'admin').count()
    total_borrowed = Issued_book_requests.query.count()

    #if there are no books inside the database then the dahsboard will display zero as the count
    if total_books == 0:
        total_books=0

    if total_category == 0:
        total_category=0

    if total_user == 0:
        total_user=0

    if total_borrowed == 0:
        total_borrowed=0

    return render_template('admin/dashboard.html', total_overdue_amount=total_overdue_amount, total_books=total_books, total_category=total_category, total_user=total_user, total_borrowed=total_borrowed)


def total_overdues():    
    issued_books = Issued_book_requests.query.all()
    current_date = datetime.now().date()
    # overdue_details = []
    total_amount = 0

    for book in issued_books:
        if current_date > book.return_date.date():
            overdue_days = (current_date - book.return_date.date()).days
        else:
            overdue_days = 0

        overdue_amount = overdue_days * 10
        total_amount += overdue_amount
        # overdue_details.append((overdue_days, overdue_amount))
    return total_amount






###############.............MANAGE BOOKS SECTION....................#################

@admin_blueprint.route('/manageBooks', methods = ['GET', 'POST'])
@login_required
@verified_required
def manageBooks():
    authenticate()
    # Query all books from the database
    books = Books.query.all()

    # # Sort books by acquisition_date in descending order
    # books = sorted(books, key=lambda x: x.acquistion_date, reverse=True)

    # Sort books alphabetically by title
    books = sorted(books, key=lambda x: x.title.lower())

    # Empty list for filtered books
    filtered_books = []

    if request.method == 'POST':
        search_criteria = request.form.get('search_book_criteria')
        search_content = request.form.get('search_field_content').lower()

        # Filter books based on search criteria
        for book in books:
            if search_criteria == 'Title' and search_content in book.title.lower():
                filtered_books.append(book)
            elif search_criteria == 'Author' and search_content in book.author.lower():
                filtered_books.append(book)
            elif search_criteria == 'ISBN' and search_content == book.ISBN.lower():  # Use exact match for ISBN
                filtered_books.append(book)
            elif search_criteria == 'Category' and str(book.category_id).lower() == search_content:  # Convert category_id to string for case-insensitive search
                filtered_books.append(book)
        if not filtered_books:
        	flash('Book not found', category='error')
    return render_template('admin/manageBooks.html', filtered_books=filtered_books, books=books)



@admin_blueprint.route('/manageBooks/getBookDetails/<int:book_id>', methods=['GET'])
@login_required
@verified_required
def get_book_details(book_id):
    authenticate()
    # Query the book details from the database based on the provided book ID
    book = Books.query.get(book_id)

    # Check if the book exists
    if book:
        # Convert book data to a dictionary
        book_data = {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'copies': book.copies,
            'issued': book.issued,
            'ISBN': book.ISBN,
            'category_id': book.category.name
            # Add more fields if needed
        }
        return jsonify(book_data)
    else:
        # If the book is not found, return an error response
        return jsonify({'error': 'Book not found'}), 404



@admin_blueprint.route('/manageBooks/getCategories', methods=['GET'])
@login_required
@verified_required
def get_categories():
    # Query all categories from the database
    categories = Category.query.all()

    # Convert categories to a list of dictionaries
    categories_data = [{
        'id': category.id,
        'name': category.name
    } for category in categories]

    return jsonify(categories_data)




@admin_blueprint.route('/manageBooks/updateBook/<int:book_id>', methods=['POST'])
@login_required
@verified_required
def update_book(book_id):
    # Authenticate admin
    authenticate()

    # Get the edited book details from the request
    edited_book_data = request.json

    # Find the book in the database by its ID
    book = Books.query.get(book_id)

    if not book:
        abort(404, "Book not found")

    # Check if there's another book with the same ISBN
    if edited_book_data.get('ISBN') != book.ISBN and Books.query.filter_by(ISBN=edited_book_data.get('ISBN')).first():
        return jsonify({'error': 'Another book with the same ISBN already exists'}), 400

    # Update the book details
    book.title = edited_book_data.get('title', book.title)
    book.author = edited_book_data.get('author', book.author)
    book.copies = edited_book_data.get('copies', book.copies)
    book.ISBN = edited_book_data.get('ISBN', book.ISBN)
    book.category_id = edited_book_data.get('category_id', book.category_id)

    # Commit changes to the database
    db.session.commit()

    flash('Book details updated successfully', category='success')

    # Return a success message
    return jsonify({'message': 'Book details updated successfully'}), 200





UPLOAD_FOLDER = 'my_app/static/Book_previews'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@admin_blueprint.route('/manageBooks/addBook', methods=['GET', 'POST'])
@login_required
@verified_required
def addBooks():
    authenticate()
    
    # Fetch categories
    categories = Category.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        copies = request.form.get('copies')
        isbn_no = request.form.get('isbn_no')
        category_name = request.form.get('category')
        book_preview = request.files.get('book_preview')  # Access file upload with request.files.get()

        # Ensure the upload folder exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

        # Handle file upload if an image was provided
        if book_preview:
            if book_preview.filename:
                if not allowed_file(book_preview.filename):
                    flash('Invalid file extension', category='error')
                    return redirect(request.url)

                filename = secure_filename(book_preview.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                book_preview.save(filepath)
            else:
                filename = None  # Set filename to None if no image was uploaded
        else:
            filename = None

        # Get category ID
        category = Category.query.filter_by(name=category_name).first()

        if not category:
            flash('Invalid category!', category='error')
            return redirect(url_for('admin.addBooks'))

        new_book = Books(
            title=title,
            author=author,
            copies=copies,
            issued=0,
            ISBN=isbn_no,
            category_id=category.id,
            book_preview_name=filename  # This can be the filename or None
        )

        db.session.add(new_book)
        db.session.commit()

        flash('Book Added To Library Catalogue!', category='success')
        return redirect(url_for('admin.manageBooks'))

    return render_template('admin/addBooks.html', categories=categories)






@admin_blueprint.route('/manageBooks/issueBook', methods=['GET', 'POST'])
@login_required
@verified_required
def issueBook():
	authenticate()
	if request.method == 'POST':
		# Getting the values from the form in the issue books page
		book_id = request.form.get('book_id')
		borrower_id = request.form.get('borrower_id')
		return_date_str = request.form.get('return_date')
		return_date = datetime.strptime(return_date_str, '%Y-%m-%d')


		# We first start by checking if both the  user and the books are in our database
		borrower = User.query.filter_by(email = borrower_id).first()
		book = Books.query.filter_by(ISBN = book_id).first()

		# If the user does not exist, we redirect them to the issueBook page
		if not borrower:
			flash("Action can't be completed. User does not exist!!", category='error')
			return redirect(url_for('admin.issueBook'))

		# If the requested book also does not exist, we will redirect them to the issueBook page
		elif not book:
			flash("Action can't be completed. Requested Bokok Does not exist", category='error')
			return redirect(url_for('admin.issueBook'))
		# Query the Issued_book_requests table to check if the book has already been issued to the same borrower
		already_issued = Issued_book_requests.query.filter(
			and_(
				Issued_book_requests.book_id == book.id,
				Issued_book_requests.user_id == borrower.id
			)
		).first()

		if already_issued:
			flash("This book has already been issued to the same person.", category='error')
			return redirect(url_for('admin.issueBook'))

		bookCopies = book.copies
		if bookCopies <= 0:
			flash('No copies available for issue!!', category='error')
			return redirect(url_for('admin.issueBook'))

		# Update the value of the issued books
		book.copies -= 1
		book.issued += 1

		# If both the user and the book exist, we add the entry to the database
		issued_book = Issued_book_requests(book_id = book.id, user_id = borrower.id, return_date = return_date)
		db.session.add(issued_book)
		db.session.commit()
		flash("Book Issued successfully", category = 'success')
		return redirect(url_for('admin.issueBook'))

	return render_template('/admin/issueBook.html')




@admin_blueprint.route('/get_book_titles')
@login_required
@verified_required
def get_book_titles():
	book_id = request.args.get('book_id')
	#We then query the database to perform the necessary logic to get book based on the book ID
	book = Books.query.filter_by(id=book_id).first()
	if book:
		titles = [book.title]
	else:
		titles = []#return an empty list if no book has been found
	return jsonify(titles)


	
	

@admin_blueprint.route('/manageBooks/requestedBook', methods=['GET', 'POST'])
@login_required
@verified_required
def issue_requested_book():
    authenticate()
    book_availability = None
    clicked_book = Books.query.all()

    requested_books = Requested_books.query.filter(Requested_books.status == 'pending').all()
    
    if request.method == 'POST':
        book_isbn = request.form.get('book_isbn_issue')
        
        # Query the books table to find the book ID based on the ISBN
        book_id = db.session.query(Books.id).filter(Books.ISBN == book_isbn).scalar()

        if not book_id:
            flash('Book Not Found', category='error')
            return redirect(url_for('admin.issue_requested_book'))

        return_date_str = request.form.get('returnDate')
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d')
        book_title = request.form.get('book_title')
        borrower_email = request.form.get('borrower_email_issue')
        borrower_id = db.session.query(User.id).filter(User.email == borrower_email).scalar()

        # Retrieve the requested book from the database
        requested_book = Requested_books.query.filter(
            and_(
                Requested_books.book_id == book_id,
                Requested_books.user_id == borrower_id
            )
        ).first()

        if not requested_book:
            abort(404, "Requested book not found")

        # Check if the requested book's status is 'issued'
        if requested_book.status == 'issued':
            flash("This book has already been issued to the same user.", category='error')
            return redirect(url_for('admin.issue_requested_book'))

        # Decrement the number of copies remaining and Increment the number of issued books
        bookCopies = db.session.query(Books.copies).filter(Books.id == book_id).scalar()

        if bookCopies <= 0:
            book_availability = "Not Available"
            flash('No copies available for issue', category='error')
            return redirect(url_for('admin.issue_requested_book'))

        # Check if the book is already issued to the same user
        already_issued = Issued_book_requests.query.filter(
            and_(
                Issued_book_requests.book_id == book_id,
                Issued_book_requests.user_id == borrower_id
            )
        ).first()

        # If the book is already issued to the same user, return an error
        if already_issued:
            flash("This book has already been issued to the same person.", category='error')
            return redirect(url_for('admin.issue_requested_book'))

        # Create an entry in the Issued_book_requests table
        issued_request = Issued_book_requests(user_id=borrower_id, book_id=book_id, return_date=return_date)
        db.session.add(issued_request)

        # Update the number of existing and issued book copies
        db.session.query(Books).filter(Books.id == book_id).update({Books.copies: Books.copies - 1, Books.issued: Books.issued + 1})

        # Update the status of the requested book entry
        requested_book.status = 'issued'

        # Commit the transaction
        db.session.commit()
        flash(f'Book "{book_title}" issued to "{borrower_email}" successfully.', category='success')
        return redirect(url_for('admin.issue_requested_book'))

    return render_template('admin/requestedBook.html', requested_books=requested_books)


@admin_blueprint.route('/manageBooks/denyBooks', methods=['POST'])
@login_required
@verified_required
def denyBooks():
    book_isbn = request.form.get('book_isbn_deny')
    book_id = db.session.query(Books.id).filter(Books.ISBN == book_isbn).scalar()
    
    if not book_id:
        flash('Book Not Found', category='error')
        return redirect(url_for('admin.issue_requested_book'))

    borrower_email = request.form.get('borrower_email_deny')
    borrower_id = db.session.query(User.id).filter(User.email == borrower_email).scalar()

    # Retrieve the requested book to deny from the database
    book_to_deny = Requested_books.query.filter_by(book_id=book_id, user_id=borrower_id, status='pending').first()
    
    if not book_to_deny:
        flash("Action can't be completed. Requested book not found or it's not pending.", category='error')
        return redirect(url_for('admin.issue_requested_book'))

    # Create an entry in the Canceled_book_requests table
    canceled_request = Canceled_book_requests(request_id=book_to_deny.id)
    db.session.add(canceled_request)

    # Update the status of the requested book entry to 'canceled'
    book_to_deny.status = 'canceled'

    # Commit the transaction
    db.session.commit()

    flash('Transaction completed successfully', category='success')
    return redirect(url_for('admin.issue_requested_book'))




def getIssuedBooks():    
    issued_books = Issued_book_requests.query.all()
    current_date = datetime.now().date()
    overdue_details = []

    for book in issued_books:
        if current_date > book.return_date.date():
            overdue_days = (current_date - book.return_date.date()).days
        else:
            overdue_days = 0

        overdue_amount = overdue_days * 10
        overdue_details.append((overdue_days, overdue_amount))

    return render_template('admin/issuedBooks.html', issued_books=issued_books, overdue_details=overdue_details)


def returnBook():
    book_isbn = request.form.get('book_isbn')
    borrower_email = request.form.get('borrower_email')

    book_id = db.session.query(Books.id).filter(Books.ISBN == book_isbn).scalar()
    borrower_id = db.session.query(User.id).filter(User.email == borrower_email).scalar()

    issued_book_request = Issued_book_requests.query.filter_by(book_id=book_id, user_id=borrower_id).first()
    requested_book = Requested_books.query.filter_by(book_id=book_id, user_id=borrower_id, status='issued').first()

    if issued_book_request:
        overdue_details = calculate_overdue_details(issued_book_request.return_date.date())
        
        returned_book = Returned_books(
            overdue_days=overdue_details[0],
            overdue_amount=overdue_details[1],
            book_id=book_id,
            user_id=borrower_id
        )
        db.session.add(returned_book)

        # Update book copies and issued count
        db.session.query(Books).filter(Books.id == book_id).update(
            {
                Books.copies: Books.copies + 1,
                Books.issued: Books.issued - 1
            }
        )

        # Update requested book status
        if requested_book:
            requested_book.status = 'returned'

        db.session.delete(issued_book_request)
        db.session.commit()

    return redirect(url_for('admin.showIssuedBooks'))



def calculate_overdue_details(return_date):
    current_date = datetime.now().date()
    if current_date > return_date:
        overdue_days = (current_date - return_date).days
    else:
        overdue_days = 0

    overdue_amount = overdue_days * 10
    return (overdue_days, overdue_amount)



@admin_blueprint.route('/manageBooks/issuedBooks', methods=['GET'])
@login_required
@verified_required
def showIssuedBooks():
    return getIssuedBooks()

@admin_blueprint.route('/manageBooks/returnBook', methods=['POST'])
@login_required
@verified_required
def processReturnBook():
    authenticate()
    return returnBook()





# Route to delete a book
@admin_blueprint.route('/delete-book', methods=['POST'])
@login_required
@verified_required
def delete_book():
    # Authenticate the user
    authenticate()

    # Extract book ID from the request data
    book_data = request.get_json()
    book_id = book_data.get('bookId')

    # Check if book ID is provided
    if book_id is None:
        return jsonify({"error": "No book ID provided"}), 400

    # Query the database to get the book by ID
    book = Books.query.get(book_id)

    # Check if the book exists
    if book is None:
        return jsonify({"error": "Book not found"}), 404

    try:
        # Delete the book
        db.session.delete(book)
        db.session.commit()

        return jsonify({"message": "Book deleted successfully"}), 200
    except Exception as e:
        # Handle any exceptions during deletion
        db.session.rollback()
        return jsonify({"error": str(e)}), 500






#####################..............CATEGORIES...............#############
@admin_blueprint.route('/category', methods=['GET', 'POST'])
@login_required
@verified_required
def category():
	authenticate()
	#To query all the categoris of books in our database and display them on the category page
	categories = Category.query.all()

	# We first make an empty list for filtered categories
	filtered_category = []

	if request.method == 'POST':
		search_content = request.form.get('search_field_content').lower()

		# Filter categories based on search content
		for category in categories:
			if search_content in category.name.lower():
				filtered_category.append(category)

		if not filtered_category:
			flash('Category not found!', category='error')

	return render_template('admin/categories.html', categories=categories, filtered_category=filtered_category)




@admin_blueprint.route('/category/addCategory', methods=['GET', 'POST'])
@login_required
@verified_required
def addCategory():
	authenticate()
	if request.method == 'POST':
		category_name = request.form.get('category_name')
		category_status = request.form.get('category_status')

		#we will then convert the radio values from the form to boolean values
		is_active = True if category_status == 'true' else False

		new_category = Category.query.filter_by(name = category_name).first()
		if new_category:
			flash('Category already exist!!', category='error')
		else:
			new_category = Category(name = category_name, is_active = is_active)
			db.session.add(new_category)
			db.session.commit()
			flash('Category added successfully!!', category='success')
			return redirect(url_for('admin.category'))

	#In case of any other method, redirect to the category page
	return render_template('admin/categories.html')




#the admin can delete the categories that are no longer available on the libary from this function
@admin_blueprint.route('/delete-category', methods=['POST'])
@login_required
@verified_required
def delete_category():
    authenticate()
    category_id = request.json.get('categoryId')

    if category_id is None:
        return jsonify({"error": "No category ID provided"}), 400

    category = Category.query.get(category_id)

    if category is None:
        return jsonify({"error": "Category not found"}), 404

    try:
        # Get the name of the category
        category_name = category.name

        # Delete the associated books
        books = Books.query.filter_by(category_id=category_name).all()
        for book in books:
            db.session.delete(book)

        # Debugging: Print number of books deleted
        print("Number of books deleted:", len(books))

        # Delete the category
        db.session.delete(category)
        db.session.commit()

        return jsonify({"message": "Category and associated books deleted successfully"}), 200
    except Exception as e:
        # Handle any exceptions during deletion
        db.session.rollback()
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500



###################..............MANAGE USERS SECTION...................#########################
@admin_blueprint.route('/manageUsers', methods=['GET', 'POST'])
@login_required
@verified_required
def manageUsers():
	authenticate()
	users = User.query.filter(User.role != 'admin').all()

	# Empty list for filtered users
	filtered_users = []

	if request.method == 'POST':
		search_criteria = request.form.get('search_user_criteria').lower()
		search_content = request.form.get('search_field_content').lower()

		# Filter books based on search criteria
		for user in users:
			if search_criteria == 'name' and search_content in user.name.lower():
				filtered_users.append(user)

			elif search_criteria == 'email' and search_content == user.email.lower(): # We use the exact match for email
				filtered_users.append(user)

		if not filtered_users:
			flash('User not found!', category='error')

	return render_template('admin/manageUsers.html', filtered_users=filtered_users, users=users)


from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message


@admin_blueprint.route('/manageUsers/addUser', methods = ['GET', 'POST'])
@login_required
@verified_required
def addUser():
    if request.method == 'POST':
        fname = request.form.get('fname')
        sname = request.form.get('sname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        membership_type = request.form.get('membership_type')
        password = request.form.get('password')
        password1 = request.form.get('password1')

        if password != password1:
            flash('Passwords do not match!', category='error')
            return render_template('/shared/signup.html')

        if len(password) < 6:
            flash('Password is too short (minimum 6 characters)', category='error')
            return render_template('/shared/signup.html')

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Validate phone number format
        if not validate_phone_number(phone):
            flash('Invalid phone number format. Please enter a valid phone number.', category='error')
            return render_template('/shared/signup.html')

        if membership_type == "staff":
            staff_list == Staff.query.all()
            if not email in staff_list.email:
                flash('You do not exist as a staff of Rafiki Wa Maendeleo', category="error")
                return render_template('/shared/signup.html')

        # Generate a verification code and set the expiration time
        verification_code = generate_verification_code()
        verification_code_expires = datetime.utcnow() + timedelta(hours=1)

        # Create a new User object and add it to the database
        new_user = User(
            name=fname + " " + sname,
            email=email,
            phone=phone,
            address=address,
            membership_type=membership_type,
            password=hashed_password,  # Store the hashed password
            verification_code=verification_code,
            verification_code_expires=verification_code_expires
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Sign up successful! A verification email has been sent to your email address.', category='success')
            
            # Send the verification code via email
            send_verification_code_email(email, verification_code)

            return render_template('/shared/verify_email.html', email=email)
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during sign up. Please try again later.', category='error')
            return render_template('/shared/signup.html')

    return render_template('/admin/addUser.html')





@admin_blueprint.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        email = request.form.get('email')
        verification_code = request.form.get('verification_code')

        # Check if the verification code matches the one sent to the user
        user = User.query.filter_by(email=email).first()
        if user and user.verification_code == verification_code and user.verification_code_expires > datetime.utcnow():
            # Mark the user's email as verified
            user.verified = True
            user.verification_code = None  # Clear the verification code
            user.verification_code_expires = None  # Clear the verification code expiration
            try:
                db.session.commit()  # Commit the changes to update user's verification status
                flash('Your email has been successfully verified! You can now login.', category='success')
                send_welcome_email(user.email, user.name)
                return redirect(url_for('admin.addUser'))
            except Exception as e:
                current_app.logger.error(f"Error committing user verification: {e}")
                flash('An error occurred while verifying your email. Please try again later.', category='error')
                return redirect(url_for('auth.verify_email'))
        else:
            flash('Invalid verification code or code has expired. Please try again.', category='error')
            return redirect(url_for('auth.verify_email'))

    # Handle GET request to render verification form
    email = request.args.get('email')
    if email:
        return render_template('/shared/verify_email.html', email=email)
    else:
        # Redirect to signup page if email parameter is missing
        return redirect(url_for('admin.addUser'))


def send_welcome_email(user_email, user_name):
    subject = "Welcome to Rarieda Technical And Resource Center Library"
    html_content = render_template('shared/welcome_email.html', user_name=user_name)
    send_email(user_email, subject, html_content)



def generate_verification_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def send_verification_code_email(email, verification_code):
    subject = "Verification Code for Email Verification"
    html_content = render_template('shared/verification_code_email.html', verification_code=verification_code)
    send_email(email, subject, html_content)


def send_email(recipient, subject, html_content):
    msg = Message(subject=subject, sender=current_app.config['MAIL_USERNAME'], recipients=[recipient], html=html_content)
    mail.send(msg)


def validate_phone_number(phone):
    try:
        # Parse the phone number
        phone_number = phonenumbers.parse(phone, None)

        # Check if the phone number is valid and possible
        return phonenumbers.is_valid_number(phone_number) and phonenumbers.is_possible_number(phone_number)
    except phonenumbers.phonenumberutil.NumberParseException:
        return False




# Route for sending emails to registered users
@admin_blueprint.route('/send_message', methods=['POST', 'GET'])
@login_required
@verified_required
def send_message():
    message_type = request.form.get('messageType')
    subject = request.form.get('subject')
    message = request.form.get('message')
    

    if message_type == 'not_selected':
        flash('Please select a message type.', category='error')
        return redirect(url_for('admin.manageUsers'))

    recipients = None
    if message_type == 'individual':
        recipient_email = request.form.get('email')
        recipients = [recipient_email]  # Convert single recipient email to a list
    elif message_type == 'multiple':
        recipient_emails = request.form.get('email')
        recipients = [email.strip() for email in recipient_emails.split(',') if email.strip()]  # Split multiple emails and remove empty strings

    elif message_type == 'all':
    	users = User.query.all()
    	recipients = users.email
    
    if recipients:
        # Check if the email addresses are registered in the database
        existing_recipients = User.query.filter(User.email.in_(recipients)).all()
        existing_recipient_emails = [user.email for user in existing_recipients]

        # Send message only to existing recipients
        for recipient_email in existing_recipient_emails:
            send_email_function(recipient_email, subject, message) 

            # Store the sent email in the database
            sent_message = Sent_messages(receiver=recipient_email, sending_date=datetime.now(), subject=subject, email_content=message)
            db.session.add(sent_message)
        db.session.commit()  # Commit changes to the database for every email
        
        flash(f'Message sent successfully to {len(existing_recipient_emails)} recipients.', category='success')
        # sent_email_message = Sent_messages(receiver=)
    else:
        flash('No valid recipients found.', category='error')

    return redirect(url_for('admin.manageUsers'))





@admin_blueprint.route("/suspend-user", methods=["POST"])
def suspend_user():
    data = request.get_json()
    user_id = data.get("userId")
    if not user_id:
        return jsonify({"error": "User ID not provided"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.status = "Suspended"
    db.session.commit()

    return jsonify({"message": "User suspended successfully"}), 200



@admin_blueprint.route("/unsuspend-user", methods=["POST"])
def unsuspend_user():
    data = request.get_json()
    user_id = data.get("userId")
    if not user_id:
        return jsonify({"error": "User ID not provided"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.status = "Active"
    db.session.commit()

    return jsonify({"message": "User unsuspended successfully"}), 200


@admin_blueprint.route('/remove-user/<int:user_id>', methods=['POST'])
@login_required
def remove_user(user_id):
    user = User.query.get(user_id)
    print("ID: ", user)
    if user:
    	try:
    		# We get the id of the user
    		user_id = user.id

    		# Delete all the associated tables with the user
    		requested_books = Requested_books.query.filter_by(user_id=user_id).all()
    		favourite_books = Favourites.query.filter_by(user_id=user_id).all()
    		user_library = User_Library.query.filter_by(user_id=user_id).all()

    		# We will then first check if the user still has some issued books that have not been returned
    		issued_books = Issued_book_requests.query.filter_by(user_id=user_id).all()

            # If the issued books return true, we will abort the deletion of the user
    		if issued_books:
    			flash("Can't remove this user. They still have not returned some books issued to them", category='error')

    			# We will then redirect the admin back to the manageUsers html page
    			return "<h1>Can't remove this user. They still have not returned some books issued to them<h1>" 
    		else:
    			# If there are no issued books to the user to be deleted, we will proceed with deletion of the user's data in the database

    			# We firs start by looping around the requested books, and delete any request associated to the user
    			for book in requested_books:
    				db.session.delete(book)

    			# We then proceed to the deletion of the books marked as favourites by the user
    			for book in favourite_books:
    				db.session.delete(book)

    			# Deletion of all the books the user  had included in their library
    			for book in user_library:
    				db.session.delete(book)

    			# After deleting all the data associated with the user, we will then delete the user and then commit the changes
    			db.session.delete(user)
    			db.session.commit()
    			flash('User removed successfully.', 'success')
    	except Exception as e:
    		# Handling any exception during deletion
    		db.session.rollback()
    		print("Erro:", str(e))
    else:
        flash('User not found.', 'error')
    return redirect(url_for('admin.manageUsers'))




from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
import io
import base64


# Function to generate a pie chart for categories of books
def generate_category_pie_chart():
    all_books = Books.query.all()
    categories_count = Counter(book.category.name for book in all_books if book.category)
    categories = list(categories_count.keys())
    counts = list(categories_count.values())

    fig, ax = plt.subplots()
    ax.pie(counts, labels=categories, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    # Save pie chart to a PNG image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    
    return plot_url



import matplotlib
matplotlib.use('Agg')  # Set backend to Agg


def generate_most_borrowed_books_bar_chart():
    issued_books = Issued_book_requests.query.all()
    books_count = Counter()

    # Retrieve book titles using the book_id from Issued_book_requests
    for issued_book in issued_books:
        book = Books.query.get(issued_book.book_id)
        if book:
            books_count[book.title] += 1

    sorted_books = sorted(books_count.items(), key=lambda x: x[1], reverse=True)[:5]  # Top 5 most borrowed books

    books = [book[0] for book in sorted_books]
    counts = [count[1] for count in sorted_books]

    plt.figure(figsize=(10, 6))
    plt.barh(books, counts, color='blue')
    plt.xlabel('Number of Times Borrowed')
    plt.ylabel('Book Titles')
    plt.title('Top 5 Most Borrowed Books')
    plt.tight_layout()

    # Save bar chart to a PNG image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    plt.close()  # Close the plot to release resources
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    
    return plot_url



# Function to generate a line chart for months when books were most borrowed
def generate_months_borrowed_line_chart():
    issued_books = Issued_book_requests.query.all()
    borrow_dates = [book.issued_date for book in issued_books if book.issued_date]
    months = [date.strftime('%B') for date in borrow_dates if date]

    month_counts = Counter(months)
    sorted_months = sorted(month_counts.items(), key=lambda x: datetime.strptime(x[0], '%B'))

    months = [month[0] for month in sorted_months]
    counts = [count[1] for count in sorted_months]

    plt.figure(figsize=(10, 6))
    plt.plot(months, counts, marker='o', linestyle='-', color='r')
    plt.xlabel('Months')
    plt.ylabel('Number of Books Borrowed')
    plt.title('Months When Books Were Most Borrowed')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save line chart to a PNG image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    
    return plot_url

# Route for reports and analytics
@admin_blueprint.route('/analytics')
@login_required
def reports():
    category_pie_chart = generate_category_pie_chart()
    most_borrowed_books_bar_chart = generate_most_borrowed_books_bar_chart()
    months_borrowed_line_chart = generate_months_borrowed_line_chart()

    return render_template('admin/reports.html', 
                           category_pie_chart=category_pie_chart, 
                           most_borrowed_books_bar_chart=most_borrowed_books_bar_chart,
                           months_borrowed_line_chart=months_borrowed_line_chart)





# Function for handling how the message will be sent to the users
def send_email_function(recipient_email, subject, message):
	sender_email = current_app.config['MAIL_USERNAME']
	html_message = render_template('shared/email_template.html', message=message)
	msg = Message(subject=subject, sender=sender_email, recipients=[recipient_email], html=html_message)
	mail.send(msg)




def authenticate():
	#Only do this when the role of that particular person is admin
	if current_user.role != 'admin':
		abort(403)#we will return a forbidden error if the user is not admin