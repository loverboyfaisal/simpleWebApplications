from flask import Flask
from flask_login import LoginManager
import mysql.connector

def mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        username="root",
        password="root",
        database="blog"
    )


def create_app():   
    app = Flask(__name__)
    app.secret_key = "my_sec_key"

    # Connect blueprint to our main app
    from src.views import views
    # url_prifix is the root url which means for example if i wanna to visit /home
    # and url_prefix is /root so i have to go to /root/home
    app.register_blueprint(views, url_prefix='/')

    from src.auth import auth
    app.register_blueprint(auth, url_prefix='/')

    from src.models import create_blog_db,User,create_comments_table,create_posts_table
    create_blog_db()
    create_posts_table()
    create_comments_table()
    

    login_manger = LoginManager()
    # if user is not authenticated redirect them to blueprint auth => login 
    login_manger.login_view = "auth.login"
    login_manger.init_app(app)

    @login_manger.user_loader
    def load_user(id):
        return User.get(id)

    return app

