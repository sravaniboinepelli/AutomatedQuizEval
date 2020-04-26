import os
import binascii
import random
from flask import render_template
from sqlalchemy import and_, create_engine
from flask import url_for, redirect, request, make_response,flash
# Importing Session Object to use Sessions
from flask import session, logging
from app import app,db,bcrypt
from app.models import Users,Subjects,Sections,Quizes,Answers,Submissions
# from flask_mail import Mail,Message
from passlib.hash import sha256_crypt
from functools import wraps
# import smtplib
# from itsdangerous import URLSafeTimedSerializer, SignatureExpired
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
from app.forms import LoginForm, UploadAnsForm, UploadQuizForm, UpdateAccountForm
from flask_login import login_user,current_user,logout_user,login_required
from datetime import datetime, date
from flask import send_from_directory,send_file


# app.config.from_pyfile('config.cfg')
 
# mail = Mail(app)

# s = URLSafeTimedSerializer('Thisisasecret!')

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
		#if user and bcrypt.check_password_hash(user.password, form.password.data):
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

	return render_template("upload_quiz.html",title="UploadQuiz",form=form,subject=subject)



	# form = UpdateAccountForm()
	# if form.validate_on_submit():
	# 	if form.picture.data:
	# 		picture_file = save_picture(form.picture.data)
	# 		current_user.image_file = picture_file
	# 	current_user.username = form.username.data
	# 	current_user.email = form.email.data
	# 	db.session.commit()
	# 	flash('Your account has been updated!', 'success')
	# 	return redirect(url_for('account'))


# def save_picture(form_picture):
# 	#create a random number in random_hex
# 	#random_hex = secrets.token_hex(8)
# 	_, f_ext = os.path.splitext(form_picture.filename)
# 	#filename = form_picture.filename
# 	picture_fn = binascii.hexlify(os.urandom(24)) + f_ext
# 	#picture_fn = _ + f_ext
# 	#print ("shafiya")
# 	print(picture_fn)
# 	picture_path = os.path.join(app.root_path,'static/profile_pics',picture_fn)
# 	#print('path')
# 	#print picture_path
# 	#destination = '/'.join(target,filename)
# 	form_picture.save(picture_path)
# 	return picture_fn


# #Check this --	
# @app.route('/list_req')
# def list_req():
# 	# driver user id
# 	# usernam=session["user"]
# 	#userobj=Users.query.filter_by(username=usernam).first()	    
# 	#dri_id = userobj.id
# 	dri_id=current_user.id
# 	all_req = MyRequests.query.filter_by(Rdriverid=dri_id).all()
# 	return render_template('list_requests.html',all_req=all_req)


# @app.route('/user/<name>')
# def hello_user(name):
# 	if name == 'admin':
# 		return redirect(url_for('hello_admin'))
# 	else:
# 		return redirect(url_for('hello_guest',guest = name))





# @app.route('/loginNext',methods=['GET','POST'])
# def loginNext():
# 	# To find out the method of request, use 'request.method'
# 	if request.method == "GET":
# 		#print request.args
# 		userID = request.args.get("name")
# 		password = request.args.get("password")
# 		# Can perform some password validation here
# 		return "Login Successful for: %s" % userID
# 	elif request.method == "POST":
# 		username = request.form['name']
# 		password = request.form['password']
		# Can perform some password validation here!
		#user  = Users.query.filter(and_(Users.username == username, Users.password == password)).first()
		# passworddata =  Users.query.filter(Users.password == password).first()


		# usernamedata  = Users.query.filter(Users.username == username).first()

		# user  = Users.query.filter(and_(Users.username == username, Users.password == password)).first()
		# if user:
		# 	flash('Login successful', 'success')
		# 	session["log"] = True
		# 	session["user"] = user.username
		# 	#return "Login Successful for: %s" % user.username
		# 	return redirect(url_for("profile"))

		# else:
		# 	flash("Incorrect password.. Please provide correct password..","danger")
		# 	return render_template("login.html")



@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('index'))


def save_picture(form_picture):
	#create a random number in random_hex
	#random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	#filename = form_picture.filename
	picture_fn = binascii.hexlify(os.urandom(24)) + f_ext
	#picture_fn = _ + f_ext
	#print ("shafiya")
	print(picture_fn)
	picture_path = os.path.join(app.root_path,'static/profile_pics',picture_fn)
	#print('path')
	#print picture_path
	#destination = '/'.join(target,filename)
	form_picture.save(picture_path)
	return picture_fn

# #Prompt to login when Unauthorized access
# @app.route("/connect")
# def connect():
# 	return render_template("connect.html")


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


#Profile of User after login
@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		if form.picture.data:
			picture_file = save_picture(form.picture.data)
			current_user.image_file = picture_file
		current_user.username = form.username.data
		current_user.email = form.email.data
		db.session.commit()
		flash('Your account has been updated!', 'success')
		return redirect(url_for('account'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email
	image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
	dri_id=current_user.id
	all_req = MyRequests.query.filter_by(Rdriverid=dri_id).all()
	# print all_req[0].Ruserid
	as_driver= Drivers.query.filter_by(userid=dri_id).all()
	past_driver=[]
	coming_driver=[]
	for x in as_driver :
		datetime_object = datetime.strptime(x.Date, '%Y-%m-%d')
		print(datetime_object)
		print(datetime.now())
		if datetime_object < datetime.now() :
			past_driver.append(x)
			print(x.Date)
		else :
			coming_driver.append(x)
			print( "baad ki date ----"	)

	as_rider = Riders.query.filter_by(userid=dri_id).all()
	as_rider_details=[]
	for detail in as_rider :
		as_rider_details.append(Drivers.query.filter_by(BookingId=detail.BookingId).first()) 


	past_rider=[]
	coming_rider=[]	
	for x in as_rider_details :
		datetime_object = datetime.strptime(x.Date, '%Y-%m-%d')
		print(datetime_object)
		print( datetime.now())
		if datetime_object < datetime.now() :
			past_rider.append(x)
			print (x.Date)
		else :
			coming_rider.append(x)
	return render_template('account.html', title='Account',
						   image_file=image_file, form=form,all_req=all_req,
						   past_driver=past_driver,coming_driver=coming_driver,
						   past_rider=past_rider,coming_rider=coming_rider)
# @app.route("/profile")
# @is_logged_in
# def profile():
# 	return render_template("profile.html")

# #logout
# @app.route("/logout")
# @is_logged_in
# def logout():
# 	session.clear()
# 	flash("You are now logged out","success")
# 	return redirect(url_for('index'))



@app.route('/selride', methods=['GET', 'POST'])
def selride():
    name = request.args.get('values')
    #print name
    #print "heeeeeeeeeeeeheeeeeee"
    selected_dri = Drivers.query.filter_by(BookingId=name).first()
    return render_template('select_driver.html',selected_dri=selected_dri)


# @app.route('/list_req')
# def list_req():
# 	# driver user id
# 	# usernam=session["user"]
# 	#userobj=Users.query.filter_by(username=usernam).first()	    
# 	#dri_id = userobj.id
# 	dri_id=current_user.id
# 	all_req = MyRequests.query.filter_by(Rdriverid=dri_id).all()
# 	return render_template('list_requests.html',all_req=all_req)


@app.route('/accept_req', methods=['GET', 'POST'])
def accept_req():
	userobjid = request.args.get('value1')
	b_id = request.args.get('value2')
	#insertion in booking(riders) table
	# driver user id
	#usernam=session["user"]
	usernam=current_user.username
	userobj=Users.query.filter_by(username=usernam).first()	    
	dri_id = userobj.id
	vacant=Drivers.query.filter_by(BookingId=b_id).first()
	vac_seat = vacant.Vac_seats
	if int(vac_seat) == 0 :
		objjaroori=Users.query.filter_by(id=userobjid).first()
		emailto=objjaroori.email
		email = 'help.primeriders@gmail.com'
		password = 'Rider@prime1'		
		send_to_email = emailto
		subject = 'Ride notification'
		message = 'Sorry no seats available for requested ride. Please consider other ride options. \n\n Regards, \n PRIME RIDE Team '
		msg = MIMEMultipart()
		msg['From'] = email
		msg['To'] = send_to_email
		msg['Subject'] = subject
		msg.attach(MIMEText(message, 'plain'))
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(email, password)
		text = msg.as_string()
		server.sendmail(email, send_to_email, text)
		server.quit()
		return render_template('noseats.html')
	else :
		vacant.Vac_seats = int(vac_seat) -1
		db.session.commit()
		objname = Drivers()
		insert =Riders(driverid=dri_id,BookingId=b_id,userid=userobjid)
		db.session.add(insert)
		db.session.commit()
		sendto = userobj.email
		email = 'help.primeriders@gmail.com'
		password = 'Rider@prime1'		
		send_to_email = sendto
		subject = 'Ride notification'
		message = 'You have successfully added a rider for your journey. Please visit your profile for further details. \n\n Regards, \n PRIME RIDE Team '
		msg = MIMEMultipart()
		msg['From'] = email
		msg['To'] = send_to_email
		msg['Subject'] = subject
		msg.attach(MIMEText(message, 'plain'))
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(email, password)
		text = msg.as_string()
		server.sendmail(email, send_to_email, text)
		server.quit()
			#inform requester about accepting
		objjaroori=Users.query.filter_by(id=userobjid).first()
		emailto=objjaroori.email
		email = 'help.primeriders@gmail.com'
		password = 'Rider@prime1'		
		send_to_email = emailto
		subject = 'Ride notification'
		message = 'Congratulations, your ride is confirmed. Please visit your profile for further details. \n\n Regards, \n PRIME RIDE Team '
		msg = MIMEMultipart()
		msg['From'] = email
		msg['To'] = send_to_email
		msg['Subject'] = subject
		msg.attach(MIMEText(message, 'plain'))
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(email, password)
		text = msg.as_string()
		server.sendmail(email, send_to_email, text)
		server.quit()		
	
	#deletion
	
	obj = MyRequests.query.filter_by(Ruserid=userobjid,RBookingId=b_id).first()
	db.session.delete(obj)
	db.session.commit()


	# redirect to profile page
	return render_template('index.html')

	


@app.route('/delete_req', methods=['GET', 'POST'])
def delete_req():
	userobjid = request.args.get('value1')
	b_id = request.args.get('value2')
	print (userobjid)
	obj = MyRequests.query.filter_by(Ruserid=userobjid,RBookingId=b_id).first()
	db.session.delete(obj)
	db.session.commit()

	#inform requester about rejection
	newobj=Users.query.filter_by(id=userobjid).first()
	emailto=newobj.email
	email = 'help.primeriders@gmail.com'
	password = 'Rider@prime1'		
	send_to_email = emailto
	subject = 'Ride notification'
	message = 'Sorry, the driver has declined your request. Kindly consider the other available options. \n\n Regards, \n PrimeRIDE Team '
	msg = MIMEMultipart()
	msg['From'] = email
	msg['To'] = send_to_email
	msg['Subject'] = subject
	msg.attach(MIMEText(message, 'plain'))
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(email, password)
	text = msg.as_string()
	server.sendmail(email, send_to_email, text)
	server.quit()
	# redirect to profile page
	return render_template('index.html')


@app.route('/req_details', methods=['GET', 'POST'])
def req_details():
	# value1= user id
	u_id = request.args.get('value1')
	b_id = request.args.get('value2')
	userobj=Users.query.filter_by(id=u_id).first()	
	# usernam=session["user"]
	# userobj=Users.query.filter_by(username=usernam).first()	    
	# dri_id = userobj.id
    # all_req = MyRequests.query.filter_by(Ruserid=dri_id).all()
	return render_template('req_details.html',userobj=userobj,b_id=b_id)

@app.route('/req_ride', methods=['GET', 'POST'])
def req_ride():
    name = request.args.get('values')
    selected_dri = Drivers.query.filter_by(BookingId=name).first()
    return render_template('req_ride.html',selected_dri=selected_dri)



@app.route('/success_booking')
@login_required
def success_booking():
	#get email from session
	name = request.args.get('values')
	print (name)
	data=Drivers.query.filter_by(BookingId=name).first()
	print (data.CarModel)
	available=data.Vac_seats
	# driver user id
	#usernam=session["user"]
	usernam=current_user.username
	userobj=Users.query.filter_by(username=usernam).first()	
	if int(available) == 0 :
		
		#userto=userobj.userid
		#print userto
		#obj=Users.query.filter_by(id=userto).first()
		print( userobj.email)
		emailto=userobj.email
		email = 'help.primeriders@gmail.com'
		password = 'Rider@prime1'		
		send_to_email = emailto
		subject = 'Ride notification'
		message = 'Sorry for inconvenience. No seats are available for the selected ride. We will notify you as soon as rides will be available.\n Regards, \n PRIME RIDE Team '
		msg = MIMEMultipart()
		msg['From'] = email
		msg['To'] = send_to_email
		msg['Subject'] = subject
		msg.attach(MIMEText(message, 'plain'))
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(email, password)
		text = msg.as_string()
		server.sendmail(email, send_to_email, text)
		server.quit()
		return render_template('sorry.html')
	else :
		bookingid=name
		#data is driver object
		driverid=data.userid
		#requester is logged in			
		driverobj=Users.query.filter_by(id=driverid).first()
		sendto=driverobj.email
		print (sendto)
		insert=MyRequests(Rdriverid=driverid,RBookingId=bookingid,Ruserid=userobj.id)
		db.session.add(insert)
		db.session.commit()	
		email = 'help.primeriders@gmail.com'
		password = 'Rider@prime1'		
		send_to_email = sendto
		subject = 'Ride request notification'
		message = 'You have a new request for your ride offer.Please visit your profile to accept or reject request\n Regards, \n PRIME RIDE Team '
		msg = MIMEMultipart()
		msg['From'] = email
		msg['To'] = send_to_email
		msg['Subject'] = subject
		msg.attach(MIMEText(message, 'plain'))
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(email, password)
		text = msg.as_string()
		server.sendmail(email, send_to_email, text)
		server.quit()			
		print ("displayed booking id")
		return render_template('success_booking.html')


@app.route('/findride')
def find_ride():
    return render_template('findride.html')



@app.route('/offerride')
def offer_ride():
    return render_template('offerride.html')

@app.route('/findNext',methods = ['GET','POST'])
def findNext():
	startplace=request.form["source"]
	endplace = request.form["destination"]
	date_ = request.form["date"]
	time_ = request.form["time"]
	idhere=current_user.id
	driverdetails=Drivers.query.filter_by(Source=startplace,Destination=endplace,Date=date_).all()
	#filter_by(Source=startplace,Destination=endplace,Date=date_,Time=time_).first()
	#for drivers in driverdetails
	#print driverdetails.BookingId
	return render_template('gridview.html',driverdetails=driverdetails)



@app.route('/offerNext', methods = ['GET','POST'])
@login_required
def offerNext():
	vac=request.form["noofseats"]
	vac=int(vac)-1
	# idhere=session["user"]

	# details=Users.query.filter_by(username=idhere).first()
	booking = Drivers(userid=current_user.id,Source=request.form["source"],  Destination=request.form["destination"], 
	Date=request.form["date"],Time=request.form["time"],
	CarModel=request.form["carmodel"],CarNumber=request.form["carno"],Cost=request.form["cost"],
	Seats=request.form["noofseats"],Vac_seats=vac)
	print (request.form["time"])
	print ("time-----------")
	db.session.add(booking)
	db.session.commit()
	flash('Congratulations your ride details has been saved and you will be notified via email', 'success')
	email = 'help.primeriders@gmail.com'
	password = 'Rider@prime1'
	# change here accordingly
	
	#
	send_to_email = current_user.email
	subject = 'Ride notification'
	message = 'Congratulations your ride details has been saved and you will get regular updates regarding riders'
	msg = MIMEMultipart()
	msg['From'] = email
	msg['To'] = send_to_email
	msg['Subject'] = subject

	msg.attach(MIMEText(message, 'plain'))

	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(email, password)
	text = msg.as_string()
	server.sendmail(email, send_to_email, text)
	server.quit()
	#redirect to profile or home
	flash('Your ride offer has been successfully published','success')
	return render_template('index.html')

@app.route('/send_useremail', methods=['GET', 'POST'])
def send_useremail():
	bande_ki_email=	request.form['email']
	bande_ka_naam= request.form["name"]
	bande_ka_phone= request.form["phone"]
	bande_ka_msg=request.form["message"]
	#mail feedback from banda	
	emailto='help.primeriders@gmail.com'
	email = 'help.primeriders@gmail.com'
	password = 'Rider@prime1'		
	send_to_email = emailto
	subject = 'Feedback'
	message = bande_ka_msg +"\nsent by:" + bande_ki_email + "---" +bande_ka_naam + "\n Phone no. "+bande_ka_phone
	msg = MIMEMultipart()
	msg['From'] = email
	msg['To'] = send_to_email
	msg['Subject'] = subject
	msg.attach(MIMEText(message, 'plain'))
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login(email, password)
	text = msg.as_string()
	server.sendmail(email, send_to_email, text)
	server.quit()
	# redirect to profile page
	flash('Thank you for your valuable feedback','success')
	return render_template('index.html')	
