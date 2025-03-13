from flask import Flask
from flask_login import LoginManager
from routes import routes
from database import init_db
from models import User
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secure-key-for-development')
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['ENCODED_FOLDER'] = 'app/static/encoded'
    
    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ENCODED_FOLDER'], exist_ok=True)
    
    # Initialize database
    init_db(app)
    
    # Setup login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(routes)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)