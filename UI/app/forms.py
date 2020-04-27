from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo,ValidationError
from app.models import Users
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user


class LoginForm(FlaskForm):
    role = SelectField( 'Login As', choices=[('S','Student'), ('I','Instructor')])
    email = StringField('Useremail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    # remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UploadAnsForm(FlaskForm):
      answer = FileField('Choose File', validators=[FileAllowed(['pdf'])])
      submit = SubmitField('Submit')


class UploadQuizForm(FlaskForm):
      quiz = FileField('Upload Quiz Questions', validators=[FileAllowed(['pdf'])])
      crct_answer = FileField('Upload Quiz Answers', validators=[FileAllowed(['pdf'])])
      submit = SubmitField('Submit')
