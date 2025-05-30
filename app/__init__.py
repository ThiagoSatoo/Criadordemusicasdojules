import os
from flask import Flask

app = Flask(__name__)
# It's important to set a secret key for session management (e.g., flash messages)
# In a real application, use a more secure and randomly generated key,
# and consider loading it from an environment variable or a config file.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'you-will-never-guess'


from app import routes
