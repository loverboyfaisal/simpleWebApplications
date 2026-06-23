# Import bluebrint
from flask import Blueprint,render_template,request,jsonify,redirect,url_for,flash
from flask_login import login_required,current_user
from src.models import create_new_post,fetch_post,delete_post_byid,get_post_byid,fetch_author_posts
# Create bluebrint instance
views = Blueprint("views",__name__)


@views.route("/home")
@views.route("/")
@login_required
def home():
    posts = fetch_post()
    return render_template('home.html',posts=posts)

# @views.route('/fetchposts')
# def fetchposts():
#     from src.models import fetch_post
#     posts = fetch_post()
#     return posts


@views.route('/createpost',methods=["GET","POST"])
# uncomment it after finish
# @login_required
def create_post():
    if request.method == "GET":
        return render_template('createpost.html')
    if request.method == "POST":
        post_content = request.values.get("user_input_post_content")
        create_new_post(current_user.id,post_content)
        flash("post have been created","success")
    return redirect(url_for('views.home'))

@views.route('/deletepost/<id>')
@login_required
def deletepost(id):
    post = get_post_byid(id)
    if post:
        if post.get('post_author') == current_user.user_name:
            delete_post_byid(id)
            flash('Post deleted successfully!', 'success')  # Green alert
            return redirect(url_for('views.home'))
        else:
            flash('You are not the author of this post', 'danger')  # Red alert
            return redirect(url_for('views.home'))
    
    flash('Post not found', 'warning')  # Yellow alert
    return redirect(url_for('views.home'))


@views.route('/authorposts/<id>')
def authorposts(id):
    posts = fetch_author_posts(id)
    if posts:
        return render_template('posts.html',posts=posts)
    flash("Author not exist","warning")
    return redirect(url_for('views.home'))