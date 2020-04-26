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


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = users.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username already exists.. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = users.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email id already exists.. Please choose a different one.')

