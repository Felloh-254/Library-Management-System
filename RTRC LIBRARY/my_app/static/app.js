// Function for automatically removing the flash message after a set timout
// Function to hide flash messages after a certain duration
function hideFlashMessage(messageElement) {
    messageElement.style.display = 'none';
}

// Wait for the DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
    // Select all flash message elements
    const flashMessages = document.querySelectorAll('.flash-message');

    // Loop through each flash message element
    flashMessages.forEach(function(messageElement) {
        // Set a timeout to hide the flash message after 5 seconds
        setTimeout(function() {
            hideFlashMessage(messageElement);
        }, 3000); // 5000 milliseconds = 5 seconds
    });
});

// Function to display flash message
function displayFlashMessage(message, category) {
    // Remove any existing flash messages
    $('.flash-message').remove();

    // Create flash message element
    var flashMessage = $('<div class="flash-message"></div>');

    // Set message and category
    flashMessage.html(message);
    flashMessage.addClass(category);

    // Append flash message to body
    $('body').append(flashMessage);

    // Center flash message
    flashMessage.css({
        'position': 'fixed',
        'top': '20%',
        'left': '50%',
        'transform': 'translate(-50%, -50%)',
        'padding': '15px',
        'background-color': getColorForCategory(category),
        'color': '#fff',
        'border': '1px solid ' + getBorderColorForCategory(category),
        'border-radius': '5px',
        'z-index': '9999',
        'text-align': 'center'
    });

    // Hide flash message after 2 seconds
    setTimeout(function() {
        flashMessage.fadeOut('slow', function() {
            $(this).remove();
        });
    }, 2000);
}

// Function to get background color for category
function getColorForCategory(category) {
    switch (category) {
        case 'success':
            return '#28a745';
        case 'info':
            return '#17a2b8';
        case 'warning':
            return '#ffc107';
        case 'error':
            return '#dc3545';
        default:
            return '#dc3545';
    }
}

// Function to get border color for category
function getBorderColorForCategory(category) {
    switch (category) {
        case 'success':
            return '#218838';
        case 'info':
            return '#138496';
        case 'warning':
            return '#d39e00';
        case 'error':
            return '#c82333';
        default:
            return '#c82333';
    }
}




function setFormMessage(formElement, type, message) {
    const messageElement = formElement.querySelector(".form__message");

    messageElement.textContent = message;
    messageElement.classList.remove("form__message--success", "form__message--error");
    messageElement.classList.add(`form__message--${type}`);
}



//JS FOR INPUT ERROR MESSAGE

function setInputError(inputElement, message) {
    inputElement.classList.add("form__input--error");
    const errorMessageElement = inputElement.parentElement.querySelector(".form__input-error-message");
    if (errorMessageElement) {
        errorMessageElement.textContent = message;
    }
}

function clearInputError(inputElement) {
    inputElement.classList.remove("form__input--error");
    const errorMessageElement = inputElement.parentElement.querySelector(".form__input-error-message");
    if (errorMessageElement) {
        errorMessageElement.textContent = "";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const passwordInput = document.getElementById("password");

    passwordInput.addEventListener("blur", () => {
        const password = passwordInput.value;

        if (password.length > 0 && password.length < 6) {
            setInputError(passwordInput, "Password must be at least 6 characters long");
        } else {
            clearInputError(passwordInput);
        }
    });


    // Add an event listener to the confirmPassword input for real-time validation
    const confirmPasswordInput = document.getElementById("password1");

    confirmPasswordInput.addEventListener("input", () => {
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        if (confirmPassword !== password) {
            setInputError(confirmPasswordInput, "Passwords do not match");
        } else {
            clearInputError(confirmPasswordInput);
        }
    });
});





//For opening the add category popup in the category.html page
var categoryPopupContainer = document.getElementById('category_popup_container');
if (window.location.pathname === '/category/addCategory') {
    // Show the popup when the page loads
    window.onload = function() {
        categoryPopupContainer.style.display = "block";
    };

    // Get the close button for the popup
    var closeBtn = document.querySelector('.close_btn');

    // When the user clicks on the close button, close the popup
    closeBtn.onclick = function() {
        categoryPopupContainer.style.display = "none";
        // Change the URL to the desired value
        window.location.href = '/category';
    }

    // When the user clicks anywhere outside of the popup, close it
    window.onclick = function(event) {
        if (event.target == categoryPopupContainer) {
            categoryPopupContainer.style.display = "none";
            // Change the URL to the desired value
            window.location.href = '/category';
        }
    }
}




// Managing the number of rows to be displayed per page
// And handling the next and previous buttons in the manage books page
document.addEventListener("DOMContentLoaded", function () {
    const selectElement = document.getElementById("row_number");
    const rows = document.querySelectorAll("#book_data tr");
    let totalRows = rows.length;
    let defaultPerPage = parseInt(selectElement.value);
    let currentPage = 0;

    // Function to show rows for the current page
    function showRowsForPage() {
        const start = currentPage * defaultPerPage;
        const end = Math.min((currentPage + 1) * defaultPerPage, totalRows);

        rows.forEach((row, index) => {
            if (index >= start && index < end) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    }

    // Event listener for select element change
    selectElement.addEventListener("change", function () {
        defaultPerPage = parseInt(selectElement.value);
        currentPage = 0; // Reset current page to first page
        showRowsForPage(); // Show rows for the first page
    });

    // Event listener for "Next" button
    document.querySelector(".next").addEventListener("click", function () {
        if ((currentPage + 1) * defaultPerPage < totalRows) {
            currentPage++;
            showRowsForPage(); // Show rows for the next page
        }
    });

    // Event listener for "Previous" button
    document.querySelector(".previous").addEventListener("click", function () {
        if (currentPage > 0) {
            currentPage--;
            showRowsForPage(); // Show rows for the previous page
        }
    });

    // Show rows for the initial page
    showRowsForPage();


    function showEditBookModal(bookId) {
        // Logic to fetch book details from the server using the bookId
        fetch(`/manageBooks/getBookDetails/${bookId}`)
            .then(response => response.json())
            .then(bookData => {
                // Populate the modal form fields with fetched book details
                document.getElementById("edit_book_title").value = bookData.title;
                document.getElementById("edit_book_author").value = bookData.author;
                document.getElementById("edit_book_isbn").value = bookData.ISBN;
                document.getElementById("edit_book_copies").value = bookData.copies;
                
                // Populate the categories dropdown
                fetch('/manageBooks/getCategories')
                    .then(response => response.json())
                    .then(categories => {
                        const categoryDropdown = document.getElementById("edit_book_category");
                        categoryDropdown.innerHTML = '';
                        categories.forEach(category => {
                            const option = document.createElement('option');
                            option.value = category.id;
                            option.textContent = category.name;
                            
                            // Set the selected option if it matches the book's category_id
                            if (category.id === bookData.category_id) {
                                option.selected = true;
                            }

                            categoryDropdown.appendChild(option);
                        });
                    });

                // Show the modal
                const editBookModal = new bootstrap.Modal(document.getElementById("editBookModal"));
                editBookModal.show();
            })
            .catch(error => console.error(error));
    }



    let bookId; // Define bookId variable outside the event listeners

    // Add event listener to all "Edit" buttons
    const editButtons = document.querySelectorAll(".edit_btn");
    editButtons.forEach(button => {
        button.addEventListener("click", function (event) {
            bookId = parseInt(event.target.dataset.bookId); // Assign bookId when Edit button is clicked
            showEditBookModal(bookId);
        });
    });

    // Add submit event listener to the edit book form
    const editBookForm = document.getElementById("editBookForm");
    editBookForm.addEventListener("submit", function(event) {
        event.preventDefault(); // Prevent default form submission

        // Get edited book details from the form
        const editedBookData = {
            title: document.getElementById("edit_book_title").value,
            author: document.getElementById("edit_book_author").value,
            isbn: document.getElementById("edit_book_isbn").value,
            copies: document.getElementById("edit_book_copies").value,
            category: document.getElementById("edit_book_category").value
        };

        // Logic to send edited book data to the server for update (using AJAX or fetch API)
        fetch(`/manageBooks/updateBook/${bookId}`, {
            method: "POST",
            body: JSON.stringify(editedBookData),
            headers: { "Content-Type": "application/json" },
        })
        .then(response => response.json())
        .then(data => {
            const editBookModal = document.getElementById("editBookModal");
            const bootstrapModal = new bootstrap.Modal(editBookModal);  // Close the modal on successful update
            bootstrapModal.hide();

            // Set flash message in session storage
            sessionStorage.setItem('flashMessage', 'Book updated successfully');

            // Reload the page
            location.reload();
        })
        .catch(error => console.error(error));
    });
});




//this is a JSON request to delete the selected category from the database
function showCustomConfirm(message, callback) {
  var confirmDialog = document.getElementById("custom-confirm");
  var confirmYes = document.getElementById("confirm-yes");
  var confirmNo = document.getElementById("confirm-no");

  var messageElement = confirmDialog.querySelector(".message");
  messageElement.textContent = message;

  confirmYes.onclick = function() {
    callback(true);
    confirmDialog.style.display = "none";
  };

  confirmNo.onclick = function() {
    callback(false);
    confirmDialog.style.display = "none";
  };

  confirmDialog.style.display = "block";
}



function deleteCategory(categoryId) {
    // Display a custom confirmation dialog
    showCustomConfirm("Deleting this category will delete all the books registered under this category. Are you sure you want to continue?", function(result) {
        if (result) {
            // Continue with the deletion
            fetch("/delete-category", {
                method: "POST",
                body: JSON.stringify({ categoryId: categoryId }),
                headers: {
                    'Content-Type': 'application/json'
                }
            }).then(response => {
                if (response.ok) {
                    // Reload the page after successful deletion
                    window.location.reload();
                } else {
                    // Handle error
                    console.error('Failed to delete category');
                }
            }).catch(error => {
                console.error('Error:', error);
            });
        }
    });
}



// Function to delete a book with confirmation
function deleteBookWithConfirmation(bookId) {
    // Display a custom confirmation dialog
    showCustomConfirm("Are you sure you want to delete this book?", function(result) {
        if (result) {
            // Proceed with deletion if user confirms
            fetch("/delete-book", {
                method: "POST",
                body: JSON.stringify({ bookId: bookId }),
                headers: {
                    'Content-Type': 'application/json'
                }
            }).then((_res) => {
                window.location.href = "/manageBooks";
            });
        }
    });
}


//Popup for confirming the issueing of books to users
document.addEventListener("DOMContentLoaded", function() {
    // Get all issue buttons
    const issueButtons = document.querySelectorAll('.issue_btn');

    // Add click event listener to each issue button
    issueButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            // Get the borrower and book details from the table row
            const borrowerEmail = this.closest('tr').querySelector('td:nth-child(2)').textContent;
            const borrowerName = this.closest('tr').querySelector('td:nth-child(3)').textContent;
            const bookTitle = this.closest('tr').querySelector('td:nth-child(5)').textContent;
            const bookISBN = this.closest('tr').querySelector('td:nth-child(7)').textContent;
            

            // Set the borrower and book details in the modal
            document.getElementById('borrowerEmail').textContent = borrowerEmail;
            document.getElementById('borrowerName').textContent = borrowerName;
            document.getElementById('bookName').textContent = bookTitle;
            document.getElementById('bookISBN').textContent = bookISBN;


            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('issueBookModal'));
            modal.show();

            // Set the borrower name and book title in hidden input fields
            document.getElementById('borrower_email_issue').value = borrowerEmail;
            document.getElementById('borrower_name').value = borrowerName;
            document.getElementById('book_title').value = bookTitle;
            document.getElementById('book_isbn_issue').value = bookISBN;
        });
    });

    // Get all the deny buttons
    const denyButtons = document.querySelectorAll('.cancel_btn');

    // Add click event to each deny button
    denyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            // Getting the borrowe details
            const borrowerEmail = this.closest('tr').querySelector('td:nth-child(2)').textContent;
            const bookISBN = this.closest('tr').querySelector('td:nth-child(7)').textContent;

            document.getElementById('borrowerEmail').textContent = borrowerEmail;
            document.getElementById('bookISBN').textContent = bookISBN;

            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('denyBookModal'));
            modal.show();

            // Setting the details into the input fields
            document.getElementById('borrower_email_deny').value = borrowerEmail;
            document.getElementById('book_isbn_deny').value = bookISBN;
        });
    });


    // Handling the close button for the popup
    var closeButton = document.querySelector('.custom-close-button');
    if (closeButton) {
        // The popup should then close immediately the user clicks on the close button
        closeButton.onclick = function() {
            let issueBookModal = document.getElementById('issueBookModal');
            if (issueBookModal) {
                issueBookModal.style.display = "none";
                document.querySelector('.modal-backdrop').remove();
            }
        };
    }

    var buttonClose = document.getElementById('custom-close-button');
    if (buttonClose) {
        //Making the popup to close when the user clicks on the close button
        buttonClose.onclick = function() {
            let issueBookModal = document.getElementById('issueBookModal');
            if (issueBookModal) {
                issueBookModal.style.display = "none";
                document.querySelector('.modal-backdrop').remove()
            }
        }
    }

});



//Popup for confirming the returning of books from the borrowers
document.addEventListener("DOMContentLoaded", function() {
    // We get the return_btn
    const returnButton = document.querySelectorAll('.return_btn')

    // Adding the click event listener to the button
    returnButton.forEach(function(button) {
        button.addEventListener('click', function() {
            // Get the borrower and the book details from the table row
            const borrowerEmail = this.closest('tr').querySelector('td:nth-child(2)').textContent;
            const borrowerName = this.closest('tr').querySelector('td:nth-child(3)').textContent;
            const bookTitle = this.closest('tr').querySelector('td:nth-child(4)').textContent;
            const bookISBN = this.closest('tr').querySelector('td:nth-child(6)').textContent;
            const overdue_days = this.closest('tr').querySelector('td:nth-child(7)').textContent;
            const overdue_amount = this .closest('tr').querySelector('td:nth-child(8)').textContent;


            // Set the borrower and book details in the popup for confirmation
            document.getElementById('borrowerName').textContent = borrowerName;
            document.getElementById('borrowerEmail').textContent = borrowerEmail;
            document.getElementById('bookTitle').textContent = bookTitle;
            document.getElementById('bookISBN').textContent = bookISBN;
            document.getElementById('overdue_days').textContent = overdue_days;
            document.getElementById('overdue_amount').textContent = overdue_amount;

            // Show the modal
            const modal = new bootstrap.Modal(document.getElementById('issuedBooksModal'));
            modal.show();


            // Set the borrower and book details in the hidden input fields
            document.getElementById('borrower_name').value = borrowerName;
            document.getElementById('borrower_email').value = borrowerEmail;
            document.getElementById('book_title').value = bookTitle;
            document.getElementById('book_isbn').value = bookISBN;

        });
    });


    // Handling the close button for the popup
    var closeButton = document.querySelector('.btn-close');
    if (closeButton) {
        // The popup should then close immediately the user clicks on the close button
        closeButton.onclick = function() {
            let issuedBooksModal = document.getElementById('issuedBooksModal');
            if (issuedBooksModal) {
                issuedBooksModal.style.display = "none";
                document.querySelector('.modal-backdrop').remove();
            }
        };
    }


    var buttonClose = document.getElementById('custom-close-button');
    if (buttonClose) {
        //Making the popup to close when the user clicks on the close button
        buttonClose.onclick = function() {
            let issuedBooksModal = document.getElementById('issuedBooksModal');
            if (issuedBooksModal) {
                issuedBooksModal.style.display = "none";
                document.querySelector('.modal-backdrop').remove()
            }
        }
    }
})


//Handling the favourites button
$(document).ready(function() {
    $('#add-to-favorites').on('click', function() {
        var bookId = $(this).data('book-id');
        var isFavorite = $(this).hasClass('favorite');

        $.ajax({
            url: '/toggle_favorite',
            type: 'POST',
            data: { book_id: bookId, favorite: !isFavorite },
            success: function(response) {
                if (response.success) {
                    if (isFavorite) {
                        $('#add-to-favorites').removeClass('favorite');
                        $('#add-to-favorites i').removeClass('fas fa-heart').addClass('far fa-heart');
                    } else {
                        $('#add-to-favorites').addClass('favorite');
                        $('#add-to-favorites i').removeClass('far fa-heart').addClass('fas fa-heart');
                    }
                }
            }
        });
    });
});



// JS for sending message popup to users in the admin manage Users section
document.addEventListener("DOMContentLoaded", function() {
    const messageTypeDropdown = document.getElementById("messageType");
    const emailInput = document.getElementById("emailInput");

    // Hide/show email input field based on the selected message type
    messageTypeDropdown.addEventListener("change", function() {
        if (messageTypeDropdown.value === "individual" || messageTypeDropdown.value === "multiple") {
            emailInput.style.display = "block";
        } else {
            emailInput.style.display = "none";
        }
    });
 });

// Function to suspend user
function suspendUser(userId, button) {
    // Send request to suspend user
    fetch("/suspend-user", {
        method: "POST",
        body: JSON.stringify({ userId: userId }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => {
        if (response.ok) {
            // Update button text and disable it
            button.innerText = "Unsuspend";
            button.className = "unsuspend_btn";
            // Reload the page
            window.location.reload();
        } else {
            console.error('Failed to suspend user');
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}

// Function to unsuspend user
function unsuspendUser(userId, button) {
    // Send request to unsuspend user
    fetch("/unsuspend-user", {
        method: "POST",
        body: JSON.stringify({ userId: userId }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(response => {
        if (response.ok) {
            // Update button text and enable it
            button.innerText = "Suspend";
            button.className = "suspend_btn";
            // Reload the page
            window.location.reload();
        } else {
            console.error('Failed to unsuspend user');
        }
    }).catch(error => {
        console.error('Error:', error);
    });
}

// Function to remove user
function confirmRemoveUser(userId) {
    if (window.confirm("Are you sure you want to remove this user?")) {
        // Proceed with removal
        fetch(`/remove-user/${userId}`, {
            method: "POST"
        }).then(response => {
            if (response.ok) {
                // Reload the page after successful removal
                window.location.reload();
            } else {
                // Handle error
                console.error('Failed to remove user');
            }
        }).catch(error => {
            console.error('Error:', error);
        });
    }
}





// JavaScript to determine the current page and set the active_page variable
document.addEventListener("DOMContentLoaded", function() {
    var path = window.location.pathname;
    var activePage = path.split("/").pop();
    document.querySelectorAll('.navmenu a').forEach(function(link) {
        var href = link.getAttribute('href').split("/").pop();
        if (href === activePage) {
            link.classList.add('active');
        }
    });
});


// Function for showing the navigation bar when the user clicks on the menu button in the user pages
document.addEventListener("DOMContentLoaded", function() {
    let fixedNavbar = document.querySelector(".responsive-navbar");
    document.getElementById("user-menu-btn").onclick = () => {
        fixedNavbar.classList.toggle('active');
    }

    window.onscroll = () => {
        fixedNavbar.classList.remove('active');
    }

    document.querySelector(".closeBtn").onclick = () => {
        fixedNavbar.classList.remove('active');
    }

    let searchForm = document.querySelector('.search-form-contents')
    document.getElementById("search-button").onclick = () => {
        searchForm.classList.toggle('active');
    }
})



// Function for showing the navigation bar when the admin clicks on the menu button in the admin pages
document.addEventListener("DOMContentLoaded", function() {
    let fixedNavbar = document.querySelector(".responsive_lib_navbar");
    document.getElementById("admin-menu-btn").onclick = () => {
        fixedNavbar.classList.toggle('active');
    }

    window.onscroll = () => {
        fixedNavbar.classList.remove('active');
    }

    document.querySelector(".closeBtn").onclick = () => {
        fixedNavbar.classList.remove('active');
    }
})

