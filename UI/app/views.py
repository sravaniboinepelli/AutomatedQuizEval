import os
import random
from flask import render_template
from sqlalchemy import and_, create_engine
from flask import url_for, redirect, request, make_response,flash
from flask import session, logging
from app import app,db
from app.models import Users,Subjects,Sections,Quizes,Answers,Submissions
from functools import wraps
from app.forms import LoginForm, UploadAnsForm, UploadQuizForm
from flask_login import login_user,current_user,logout_user,login_required
from datetime import datetime, date
from flask import send_from_directory,send_file

@app.route('/')
@app.route('/index')
@app.route('/home')
def index():
	if current_user.is_authenticated:
		role = current_user.role
		print("role in index =",role)
		if role == "S":
			# flash('Logged in as Student', 'success')
			return redirect(url_for('student',id=current_user.id)) 
		elif role == "I":
			# flash('Logged in as Instructor', 'success')
			return redirect(url_for('instructor',id=current_user.id))
	return render_template('index.html')


#Login Functions
@app.route("/login", methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		role = form.role.data
		print("role =",role)
		if role=='I':
			user = Users.query.filter( and_( Users.role == 'I', Users.email==form.email.data) ).first()
		elif role=='S':
			user = Users.query.filter( and_( Users.role == 'S', Users.email==form.email.data) ).first()
		if user and user.password == form.password.data:
			print("Login Succesful")
			login_user(user)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('index'))
			# return redirect(url_for('index'))
		else:
			flash('Login Unsuccessful. Please check email and password', 'danger')
	return render_template('login.html', title='Login', form=form)


#Decorators to restrict access to student and instructor
def instructor_required(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if current_user.is_authenticated and current_user.role == 'I':
			return f(*args,**kwargs)
		else:
			flash('You donot have access to the page.Please login','danger')
			return redirect(url_for('index'))
	return wrap

def student_required(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if current_user.is_authenticated and current_user.role == 'I':
			return f(*args,**kwargs)
		else:
			flash('You donot have access to the page.Please login','danger')
			return redirect(url_for('index'))
	return wrap


@app.route("/student/<id>")
# @student_required
@login_required
def student(id):
	student_obj = Users.query.filter( Users.id == id).first()
	student_name = student_obj.name
	print(student_name)
	subjects_list = Sections.query.filter(Sections.student_id == id).all()
	# print(subjects_list) #
	subject_obj_list = []
	for sub in subjects_list:
		subject_obj_list.append( Subjects.query.filter(Subjects.id == sub.subject_id ).first())
	return render_template("student_home.html", student = student_name, subjects = subject_obj_list)



@app.route("/instructor/<id>", methods=['GET', 'POST'])
@instructor_required
def instructor(id):
	instructor_obj = Users.query.filter( Users.id == id).first()
	instructor_name = instructor_obj.name
	print(instructor_name)
	subjects_list = Subjects.query.filter(Subjects.instructor_id == id).all()
	return render_template("instructor_home.html", instructor=instructor_name, subjects=subjects_list)



@app.route('/subject/<id>')
# @student_required
@login_required
def subject(id):
	subject_obj = Subjects.query.filter( Subjects.id == id).first()
	session['subject']=subject_obj.id
	print("Subject is -",subject_obj.subject_name)
	quizes_list = Quizes.query.filter( Quizes.subject_id == subject_obj.id)
	return render_template("subject.html", subject=subject_obj, quizes=quizes_list)


@app.route('/subject_prof/<id>')
@instructor_required
def subject_prof(id):
	subject_obj = Subjects.query.filter( Subjects.id == id).first()
	session['subject']=subject_obj.id
	print("Subject is -",subject_obj.subject_name)
	quizes_list = Quizes.query.filter( Quizes.subject_id == subject_obj.id)
	return render_template("subject_prof.html", subject=subject_obj, quizes=quizes_list)


@app.route('/quiz/<id>',methods=['GET'])
# @student_required
@login_required
def quiz(id):
	print("In quiz")
	subject_id = request.args.get("subject_id")
	print("s=",subject_id)
	subject_obj = Subjects.query.filter( Subjects.id == subject_id).first()
	session['subject']=subject_obj.id
	quiz_obj = Quizes.query.filter( Quizes.id == id).first()
	session['quiz']=quiz_obj.id
	quiz_path = quiz_obj.questions_link
	print(app.root_path)
	path = os.path.join(app.root_path,quiz_path)
	print(path)
	return render_template("quiz.html", subject=subject_obj, quiz=quiz_obj,file_path=path)


@app.route('/quiz_prof/<id>',methods=['GET'])
@instructor_required
def quiz_prof(id):
	print("In quiz prof")
	subject_id = session['subject']
	subject_obj = Subjects.query.filter( Subjects.id == subject_id).first()
	print("Subject is -",subject_obj.subject_name)
	quiz_obj = Quizes.query.filter( Quizes.id == id).first()
	session['quiz']=quiz_obj.id
	print("Quiz is -",quiz_obj.id)
	#Question path
	quiz_path = quiz_obj.questions_link
	quiz_path = os.path.join(app.root_path,quiz_path)
	print("Question=",quiz_path)
	#Answer path
	answer_obj = Answers.query.filter( Answers.quiz_id == quiz_obj.id).first()
	ans_path = answer_obj.answer_link
	ans_path = os.path.join(app.root_path,ans_path)
	print("Answer=",ans_path)
	return render_template("quiz_prof.html", subject=subject_obj, quiz=quiz_obj,quiz_path=quiz_path, ans_path=ans_path)
	


@app.route('/download', methods=['GET'])
@login_required
def download():    
	file_path = request.args.get("file_path")
	return send_file(file_path, as_attachment=True)


def save_ansfile(ansfile,subject,quiz):
	_, f_ext = os.path.splitext(ansfile.filename)
	filename = ansfile.filename
	print(filename)
	file_db_link = ""
	file_path = os.path.join(app.root_path,'data')
	file_db_link += "data/"
	file_path = os.path.join(file_path,'Sub'+str(subject.id))	#Subject
	file_db_link += "Sub"+str(subject.id)+"/"
	file_path = os.path.join(file_path,'Q'+str(quiz.id))		#Quiz
	file_db_link += 'Q'+str(quiz.id)+"/"
	file_path = os.path.join(file_path,'Submissions')
	file_db_link += "Submissions/"
	if os.path.isdir(file_path):
		file_path = os.path.join(file_path,str(current_user.id)+f_ext)
		file_db_link += str(current_user.id)+f_ext
		if os.path.isfile(file_path):
			os.remove(file_path)
			ansfile.save(file_path)
		else:
			ansfile.save(file_path)

	else:
		os.makedirs(file_path)
		file_path = os.path.join(file_path,str(current_user.id)+f_ext)
		file_db_link += str(current_user.id)+f_ext
		if os.path.isfile(file_path):
			os.remove(file_path)
			ansfile.save(file_path)
		else:
			ansfile.save(file_path)

	print("final path -",file_path)

	return file_db_link



@app.route('/uploadans', methods=['GET','POST'])
# @student_required
@login_required
def uploadans():
# 	if request.method == "GET":
# 		subject = request.args.get("subject")
# 		quiz = request.args.get("quiz")
# 	elif request.method == "POST":
# 		subject = request.form['subject']
# 		quiz = request.form['quiz']

	subject_id = session['subject']
	quiz_id = session['quiz']
	subject = Subjects.query.filter(Subjects.id == subject_id).first()
	quiz = Quizes.query.filter(Quizes.id == quiz_id).first()

	form = UploadAnsForm()
	if form.validate_on_submit():
		print("Form Submitted")
		print(form.answer.data)
		if form.answer.data:
			print("Data found")
			file_db_path = save_ansfile(form.answer.data,subject,quiz)
			print("file_path in db",file_db_path)
			#add to db
			s_insert = Submissions( quiz_id=quiz.id, subject_id=subject_id, student_id=current_user.id, submission_link=file_db_path)
			db.session.add(s_insert)
			db.session.flush()
			db.session.refresh(s_insert)
			submission_id = s_insert.id
			db.session.commit()
			flash('Your answer is submitted', 'success')
			return redirect(url_for('score',submission_id=submission_id))
		else:
			print("*******Data not found")
			flash('Error during submission.Please Resubmit', 'danger')
			return redirect(url_for('quiz',id=quiz.id, subject_id=subject.id))

	return render_template("upload_answer.html",subject=subject,quiz=quiz,title='UploadAns',form=form)


@app.route('/score/<submission_id>', methods=['GET','POST'])
# @student_required
@login_required
def score(submission_id):
	subject_id = session['subject']
	quiz_id = session['quiz']
	subject = Subjects.query.filter(Subjects.id == subject_id).first()
	quiz = Quizes.query.filter(Quizes.id == quiz_id).first()

	#Call Function to find score here(score-float)
	score = 10.0
	submission_t = Submissions.query.filter(Submissions.id == submission_id).first()
	submission_t.score = score
	db.session.commit()
	return render_template("score.html",subject=subject,quiz=quiz,score=score)


def save_quiz(quizfile, ansfile, subject, quiz_id):
	_, q_ext = os.path.splitext(quizfile.filename)
	_, a_ext = os.path.splitext(ansfile.filename)
	quizfilename = quizfile.filename
	print(quizfilename)
	ansfilename = ansfile.filename
	print(ansfilename)

	file_db_link = ""
	file_path = os.path.join(app.root_path,'data')
	file_db_link += "data/"
	file_path = os.path.join(file_path,'Sub'+str(subject.id))	#Subject
	file_db_link += "Sub"+str(subject.id)+"/"
	file_path = os.path.join(file_path,'Q'+str(quiz_id))		#Quiz
	file_db_link += 'Q'+str(quiz_id)+"/"

	if os.path.isdir(file_path):
		quiz_file_path = os.path.join(file_path,'Q'+str(quiz_id)+q_ext)
		quiz_file_db_link = file_db_link+'Q'+str(quiz_id)+q_ext
		ans_file_path = os.path.join(file_path,'A'+str(quiz_id)+a_ext)
		ans_file_db_link = file_db_link+'A'+str(quiz_id)+a_ext
		if os.path.isfile(quiz_file_path):
			os.remove(quiz_file_path)
			quizfile.save(quiz_file_path)
		else:
			quizfile.save(quiz_file_path)
		if os.path.isfile(ans_file_path):
			os.remove(ans_file_path)
			ansfile.save(ans_file_path)
		else:
			ansfile.save(ans_file_path)
	else:
		os.makedirs(file_path)
		quiz_file_path = os.path.join(file_path,'Q'+str(quiz_id)+q_ext)
		quiz_file_db_link = file_db_link+'Q'+str(quiz_id)+q_ext
		ans_file_path = os.path.join(file_path,'A'+str(quiz_id)+a_ext)
		ans_file_db_link = file_db_link+'A'+str(quiz_id)+a_ext
		if os.path.isfile(quiz_file_path):
			os.remove(quiz_file_path)
			quizfile.save(quiz_file_path)
		else:
			quizfile.save(quiz_file_path)
		if os.path.isfile(ans_file_path):
			os.remove(ans_file_path)
			ansfile.save(ans_file_path)
		else:
			ansfile.save(ans_file_path)
	print("final paths -",quiz_file_path,"   ",ans_file_path)

	return quiz_file_db_link,ans_file_db_link


@app.route('/uploadquiz', methods=['GET','POST'])
@instructor_required
def uploadquiz():
	print("In upload quiz")
	subject_id = session['subject']
	subject = Subjects.query.filter(Subjects.id == subject_id).first()
	print("Subject is -",subject.subject_name)

	form = UploadQuizForm()
	if form.validate_on_submit(): 
		print("Form Submitted")
		print(form.quiz.data)
		print(form.crct_answer.data)
		if form.quiz.data and form.crct_answer.data:
			print("Data Found")
			#add quiz to db
			#Adding quiz without link - because we need id to create file_link
			q_insert = Quizes( subject_id=subject.id)
			db.session.add(q_insert)
			db.session.flush()
			db.session.refresh(q_insert)
			quiz_id = q_insert.id		#Getting corrently created id
			print("Quiz Created id =",quiz_id)

			quiz_db_path , crct_ans_db_path = save_quiz( form.quiz.data , form.crct_answer.data ,subject , quiz_id)			###TODO
			print("db file paths",quiz_db_path," ",crct_ans_db_path)

			q_insert.questions_link = quiz_db_path
			# db.session.commit()
			
			#Add answer to db
			a_insert = Answers( quiz_id=quiz_id , answer_link=crct_ans_db_path)
			db.session.add(a_insert)
			db.session.commit()
			session['quiz']=quiz_id
			flash('Quiz is submitted', 'success')
			# return render_template("quiz_prof.html", subject=subject, quiz=q_insert ,quiz_path=quiz_db_path, ans_db_path=ans_path)
			quizes_list = Quizes.query.filter( Quizes.subject_id == subject.id)
			return render_template("subject_prof.html", subject=subject, quizes=quizes_list)
		else:
			print("************Data not Found")
			flash('Error during submission.Please Resubmit', 'danger')
			# return render_template("quiz_prof.html", subject=subject, quiz=q_insert,quiz_path=quiz_db_path, ans_path=ans_db_path)
			quizes_list = Quizes.query.filter( Quizes.subject_id == subject.id)
			return render_template("subject_prof.html", subject=subject, quizes=quizes_list)

	return render_template("upload_quiz.html",title="UploadQuiz",form=form,subject=subject)		#if user and bcrypt.check_password_hash(user.password, form.password.data):


@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('index'))


# #Decorator to check if logged in
# def is_logged_in(f):
# 	@wraps(f)
# 	def wrap(*args,**kwargs):
# 		if 'log' in session:
# 			return f(*args,**kwargs)
# 		else:
# 			flash('Please Login before you proceed','danger')
# 			return redirect(url_for('connect'))
# 	return wrap
