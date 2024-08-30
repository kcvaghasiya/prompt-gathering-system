from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, RadioField, SelectField, MultipleFileField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class CreatePostForm(FlaskForm):
    images = MultipleFileField(u'Image File', validators=[DataRequired()])
    # img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    question = CKEditorField("Question You want to ask to user about uploaded image", validators=[DataRequired()])
    submit = SubmitField("Submit")


# Create a form to register new users
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    gender = RadioField("Gender", choices=[('male', 'Male'), ('female', 'Female')], validators=[DataRequired()])
    age = SelectField("Select Age", choices=[("below 19", "Below 19"), ("between 19 to 28", "Between 19 to 28"),
                ("between 28 to 38", "Between 28 to 38"), ("more than 38", "More than 38")],
                validators=[DataRequired()])
    profession = StringField("Profession", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


# Create a form to login existing users
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


# Create a form to add comments
# class CommentForm(FlaskForm):
#     comment_text = CKEditorField("Comment", validators=[DataRequired()])
#     submit = SubmitField("Submit Comment")
