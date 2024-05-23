# Library-Management-System
##Description

The Library Management System is a software application designed to efficiently manage the operations of a library. It provides functionalities for librarians to manage books, patrons, loans, and various administrative tasks.

##Features

Book Management: Add, edit, and delete books from the library catalog.
Patron Management: Maintain a database of library patrons, including their contact information and borrowing history.
Loan Management: Track loans, due dates, and fines for overdue books.
Search Functionality: Enable users to search for books by title, author, genre, or other criteria.
Reporting: Generate reports on book availability, overdue loans, and other relevant metrics.
User Authentication: Secure access to the system with authentication mechanisms for librarians and administrators.

##Installation

To install the Library Management System, follow these steps:

Clone the repository: git clone https://github.com/Felloh-254/library-management-system.git
1. **Install dependencies:**
   - Install the required Python packages listed in the `requirements.txt` file using pip:
     ```
     pip install -r requirements.txt
     ```

2. **Set up the database:**
   - Initialize the SQLite database and manage the database schema using Flask migration commands:
     ```
     flask db init
     flask db migrate -m "Initial migration"
     flask db upgrade
     ```

3. **Configure the application settings:**
   - Ensure that your `__init__.py` file contains the necessary settings, including the path to the SQLite database file and any other configuration parameters required by your Flask application.

4. **Start the application:**
   - Run the main Python file of your Flask application to start the development server:
     ```
     python run.py
     ```
   - Access your Flask application by visiting `http://localhost:5000` in your web browser.

##Documentation

For detailed documentation on how to use the Library Management System, refer to the documentation folder in this repository.

##Contributing

Contributions are welcome! If you'd like to contribute to the Library Management System, please follow these steps:

##Fork the repository

Create a new branch: git checkout -b feature/your-feature
Make your changes and commit them: git commit -am 'Add new feature'
Push to the branch: git push origin feature/your-feature
Submit a pull request

##License

This project is licensed under the MIT License.

##Contact

For any inquiries or support, please contact felixogweny@gmail.com.
