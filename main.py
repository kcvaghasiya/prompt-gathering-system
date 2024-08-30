import os
from datetime import date
from datetime import datetime
from flask import Flask, abort, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import UserMixin, login_required, login_user, LoginManager, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Integer, String, Text, Float
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
# Import your forms from the forms.py
from forms import CreatePostForm
from forms import RegisterForm, LoginForm

'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('app_secret_key')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
ckeditor = CKEditor(app)
Bootstrap5(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLES


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"),  nullable=False)
    # Create reference to the User object. The "posts" refers to the posts property in the User class.
    author = relationship("User", back_populates="posts")
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    reaction_time: Mapped[float] = mapped_column(Float, nullable=False)
    prompt_length: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[str] = mapped_column(db.DateTime, nullable=False, default=datetime.utcnow)



# Create a User table for all your registered users
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    profession: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(100))

    # This will act like a list of BlogPost objects attached to each User.
    # The "author" refers to the author property in the BlogPost class.
    posts = relationship("BlogPost", back_populates="author")

class AdminImages(db.Model):
    __tablename__ = "admin_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    img_urls: Mapped[str] = mapped_column(String(250), nullable=False)
    question: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()


# Create an admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)

    return decorated_function


# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        # Check if user email is already present in the database.
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()
        if user:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            name=form.name.data,
            email = form.email.data,
            gender = form.gender.data,
            age = form.age.data,
            profession = form.profession.data,
            password=hash_and_salted_password,

        )
        db.session.add(new_user)
        db.session.commit()
        # This line will authenticate the user with Flask-Login
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        # Note, email in db is unique so will only have one result.
        user = result.scalar()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))

    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():
    result = db.session.execute(db.select(AdminImages))
    images = result.scalars().all()
    image_list = []
    for image in images:
        image_urls = image.img_urls.split(",")
        # Merge the list into image_list
        image_list.extend(image_urls)
    return render_template("index.html", images=image_list, current_user=current_user)


@app.route('/submit_form', methods=['POST'])
@login_required
def submit_form():
    try:
        # Assuming that you have a fixed naming pattern: 'answer1', 'reaction_time1', 'image_urls1', etc.
        index = 1  # Start from the first image/response

        while True:
            response = request.form.get(f'answer{index}')
            reaction_time_str = request.form.get(f'reaction_time{index}')
            image_url = request.form.get(f'image_urls{index}')

            # Break the loop if there's no more images to process
            if not image_url:
                break

            # Ensure there's a valid response for the current image
            if response and reaction_time_str:
                # Convert reaction time to float, with default value 0.0 if conversion fails
                try:
                    reaction_time = float(reaction_time_str)
                except ValueError:
                    reaction_time = 0.0  # Default value for invalid float conversion
                # Measure the prompt length (character count)
                prompt_length_chars = len(response) if response else 0
                
                # Create a new BlogPost object
                new_response = BlogPost(
                    author_id=current_user.id,  # Associate the post with the current user
                    img_url=image_url,
                    response=response,
                    reaction_time=float(reaction_time),
                    prompt_length=prompt_length_chars
                )

                # Add the new response to the session
                db.session.add(new_response)

            # Move to the next image/response pair
            index += 1

        # Commit the session to save all responses to the database
        db.session.commit()
        flash('Your responses have been successfully submitted!', 'success')
        return redirect(url_for('thank_you'))

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the transaction if there is an error
        # flash(f'An error occurred: {str(e)}', 'danger')
        return render_template("index.html", current_user=current_user)



@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        image_urls = []
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    # Construct the URL to the uploaded file
                    file_url = url_for('static', filename=f'uploads/{filename}', _external=True)
                    image_urls.append(file_url)

        # Join the image URLs into a single string (you could also use a different method to store them)
        image_urls_str = ",".join(image_urls)

        new_post = AdminImages(
            img_urls=image_urls_str,
            question=form.question.data
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))

    return render_template("make-post.html", form=form, current_user=current_user)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# # Use a decorator so only an admin user can delete a post
# @app.route("/delete/<int:post_id>")
# @admin_only
# def delete_post(post_id):
#     post_to_delete = db.get_or_404(BlogPost, post_id)
#     db.session.delete(post_to_delete)
#     db.session.commit()
#     return redirect(url_for('get_all_posts'))
#

@app.route("/about")
def about():
    return render_template("about.html", current_user=current_user)


@app.route("/contact")
def contact():
    return render_template("contact.html", current_user=current_user)

@app.route("/thank_you")
def thank_you():
    return render_template("thank-you.html", current_user=current_user)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
