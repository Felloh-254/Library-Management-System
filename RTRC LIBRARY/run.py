#Importing the create_app function from the __init__ file in the my_app folder
from my_app import create_app

app = create_app()

if __name__ == '__main__':
	app.run(debug=True)
