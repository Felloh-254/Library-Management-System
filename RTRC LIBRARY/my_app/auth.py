from flask import Blueprint, render_template, flash, request, url_for, redirect, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from my_app import db, mail
from my_app.models import User, Staff
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from functools import wraps
from datetime import datetime, timedelta
import time
import random
import string
import phonenumbers

auth_blueprint = Blueprint('auth', __name__, url_prefix='/')



def verified_required(view_func):
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if not current_user.verified:
            flash('Please verify your email to access this page.', category='warning')
            return redirect(url_for('auth.login'))  # Redirect to the login page if not verified
        if current_user.status != 'Active':
            flash('Your account is suspended.', category='danger')
            return redirect(url_for('auth.login'))  # Redirect to the login page if suspended
        return view_func(*args, **kwargs)
    return decorated_view



@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'user':
                return redirect(url_for('userView.home'))
            elif user.role == 'superadmin':
                return redirect(url_for('superadmin.manage_users'))
        flash('Incorrect email or password. Try again', category='error')
        # return jsonify({"message" : "Incorrect email or password. Try again"}), 400

    return render_template('/shared/login.html', user=current_user)


def delete_unverified_accounts():
    # Calculate the timestamp one hour ago
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    # Query for unverified accounts created more than one hour ago
    unverified_accounts = User.query.filter_by(verified=False).filter(User.creation_date <= one_hour_ago).all()
    
    for account in unverified_accounts:
        db.session.delete(account)
        db.session.commit()


@auth_blueprint.before_request
def delete_unverified_accounts_before_request():
    delete_unverified_accounts()


@auth_blueprint.route('/signup', methods=['GET', 'POST'])
def signup():
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
            staff_list = Staff.query.all()
            staff_emails = [staff.email for staff in staff_list]
            if email not in staff_emails:
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
            
            # Send the verification code via email
            send_verification_code_email(email, verification_code)

            return render_template('/shared/verify_email.html', email=email)
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during sign up. Please try again later.', category='error')
            return render_template('/shared/signup.html')

    return render_template('/shared/signup.html')





@auth_blueprint.route('/verify_email', methods=['GET', 'POST'])
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
                return redirect(url_for('auth.login'))
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
        return redirect(url_for('auth.signup'))


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


@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully!', category='info')
    return redirect(url_for('auth.login'))


