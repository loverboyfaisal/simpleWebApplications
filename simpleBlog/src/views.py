# Import bluebrint
from flask import Blueprint,render_template,request,jsonify,redirect,url_for,flash
from flask_login import login_required,current_user
from src.models import create_new_post,fetch_post,delete_post_byid,get_post_byid,fetch_author_posts,view_comment_byid,create_comment,delete_comment,get_comment_byid
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
        if post_content == "":
            flash("Can't create empty post","warning")
            return redirect(url_for('views.home'))
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

@views.route('/postcomments/<post_id>')
def view_comments(post_id):
    post = get_post_byid(post_id)
    comment = view_comment_byid(post_id)
    return render_template('postcomment.html',comments=comment,post=post,current_user=current_user)


@views.route('/createcomment/<id>',methods=["POST"])
def create_new_comment(id):
    if request.method == "POST":
        user_name = current_user.id
        post_id = id
        comment_content = request.values.get("user_input_comment_content")
        create_comment(post_id,comment_content,user_name)
        flash("Comment have been posted","success")
        return redirect(url_for(f"views.view_comments",post_id=post_id))
    else:
        flash("Error","danger")
        return redirect(url_for("views.view_comments"))
    

@views.route('/deletecomment/<comment_id>',methods=["GET"])
def deletecomment(comment_id):
    if request.method == "GET":
        com_exist = get_comment_byid(comment_id)

        if com_exist:
            # try:
                post_id = com_exist.get("post_id")
                delete_comment(com_exist.get("com_id"))
                flash("Comment have been deleted","success")
                return redirect(url_for("views.view_comments",post_id=post_id))
            # except:
            #     flash("Error...","warning")
            #     return redirect(url_for("views.view_comments",post_id=post_id))
        else:
            flash("Comment is not exists")
            return redirect(url_for("views.view_comments",post_id=post_id))