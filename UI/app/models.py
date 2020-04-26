from datetime import datetime
from app import db,login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))

class Users(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(1) , nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return "Users('{self.id}')"


class Subjects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(50), nullable=False)
    instructor_id = db.Column(db.Integer,nullable=False)    #->Instrucorid -> Users.id
    def __repr__(self):
        return "Subjects('{self.id}')"


class Sections(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer,nullable=False)   #Subjectid->Subjects.id
    student_id = db.Column(db.Integer,nullable=False)   #Studentid ->Users.id
    def __repr__(self):
        return "Sections('{self.subject_id}')"


class Quizes(db.Model):
    id = db.Column(db.Integer, primary_key=True)            #??????
    subject_id = db.Column(db.Integer,nullable=False)   #Subjectid->Subjects.id
    questions_link = db.Column(db.String(100))   #Path to question paper
    def __repr__(self):
        return "Questions('{self.id}')"


class Answers(db.Model):
    id = db.Column(db.Integer, primary_key=True)        #??????
    quiz_id = db.Column(db.Integer,nullable=False)     #quiz_id -> Quizes.id
    answer_link = db.Column(db.String(100), nullable=False)   #Path to answer
    def __repr__(self):
        return "Answers('{self.quiz_id}')"


class Submissions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, nullable=False)     #quiz_id -> Quizes.id
    subject_id = db.Column(db.Integer, nullable=False)   #Subjectid->Subjects.id
    student_id = db.Column(db.Integer, nullable=False)   ##Studentid ->Users.id
    submission_link = db.Column(db.String(100), nullable=False)   #Path to submission
    score = db.Column(db.Float)
    def __repr__(self):
        return "Submissions('{self.id}')"


db.create_all()


