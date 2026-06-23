from src import mysql_connection
from flask_login import UserMixin


# This class which get data from mysql database 
class User(UserMixin):
    def __init__(self,user_id,user_name,user_email,user_password):
        self.id = user_id
        self.user_name = user_name
        self.user_email = user_email
        self.user_password = user_password
    @staticmethod
    def get(user_id :int):
        db = mysql_connection()
        curr = db.cursor(dictionary=True,buffered=True)

        curr.execute("select * from users where id = %s;",(user_id,))
        row = curr.fetchone()

        curr.close()
        db.close()

        if row:
            return User(
                row.get("id"), 
                row.get("user_name"), 
                row.get("user_email"), 
                row.get("user_password_hash")
            )
        
        return None
    @staticmethod
    def get_by_email(user_email :int):
        db = mysql_connection()
        curr = db.cursor(dictionary=True,buffered=True)

        curr.execute("select * from users where user_email = %s;",(user_email,))
        row = curr.fetchone()

        curr.close()
        db.close()

        if row:
            return User(
            row.get("id"), 
            row.get("user_name"), 
            row.get("user_email"), 
            row.get("user_password_hash")
            )

        return None
    

def fetch_author_posts(user_id):
    db = mysql_connection()
    curr = db.cursor(dictionary=True)

    query = """
    select post_id,user_id,post_content from posts where user_id = %s
"""
    curr.execute(query,(user_id,))
    rows = curr.fetchall()
    
    curr.close()
    db.close()

    return rows


    

def fetch_post():
    db = mysql_connection()
    curr = db.cursor(dictionary=True)

    query = "select post_id,user_id,user_name as username,post_content,data_publish from posts inner join users on users.id = posts.user_id;"
    curr.execute(query)
    rows = curr.fetchall()

    curr.close()
    db.close()

    return rows
    

def delete_post_byid(post_id):
    db = mysql_connection()
    curr = db.cursor(dictionary=True)

    query = """
    delete from posts where post_id = %s;
    """
    curr.execute(query,(post_id,))
    db.commit()

    curr.close()
    db.close() 

def get_post_byid(post_id):
    db = mysql_connection()
    curr = db.cursor(dictionary=True)

    query = """
    select post_id,user_id,user_name as post_author,post_content,data_publish from posts inner join users on users.id = posts.user_id where posts.post_id = %s;
    """
    curr.execute(query,(post_id,))
    row = curr.fetchone()

    curr.close()
    db.close()

    return row


def create_new_post(user_id,post_content):
    db = mysql_connection()
    curr = db.cursor(buffered=True)

    query = "insert into posts (user_id,post_content) values (%s,%s)"
    curr.execute(query,(user_id,post_content))
    db.commit()

    curr.close()
    db.close()

def deletepost(post_id):
    db = mysql_connection()
    curr = db.cursor(buffered=True)

    query = "delete from posts where post_id = %s"
    curr.execute(query,(post_id,))
    db.commit()

    curr.close()
    db.close()


def create_blog_db():
    db = mysql_connection()
    curr = db.cursor()
    
    query = "create database if not exists blog;"
    curr.execute(query)

    curr.close()
    db.close()


def create_users_table():
    db = mysql_connection()
    curr = db.cursor()
    
    query = "create table if not exists users (id int primary key auto_increment unique,user_name varchar(255),user_email varchar(255),user_password_hash varchar(255));"
    curr.execute(query)

    curr.close()
    db.close()


def create_user(user_name,user_email,password):
    db = mysql_connection()
    curr = db.cursor()

    query = "insert into users (user_name,user_email,user_password_hash) values (%s,%s,%s)"
    curr.execute(query,(user_name,user_email,password))
    db.commit()
    curr.close()
    db.close()






