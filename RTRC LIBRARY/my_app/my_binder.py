from flask_injector import Binder

class MyBinder(Binder):
    def configure(self, binder):
        from .auth import signup  # Assuming signup function is in auth.py
        binder.bind(signup, signup)  # Bind signup function without app argument
