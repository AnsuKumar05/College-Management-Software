import os
import logging
from functools import wraps
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Student, Teacher, Course, Department, Attendance, Grade

# Configure logging
logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)

# ------------------------------
# Config
# ------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_fixed_secret_key'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False      # Must be False for local HTTP
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = False     # Must be False for local HTTP

# ------------------------------
# Initialize DB and LoginManager
# ------------------------------
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# ------------------------------
# Logging
# ------------------------------
logging.basicConfig(level=logging.INFO)

@app.before_request
def log_request_info():
    logging.info(f"Request: {request.method} {request.path} from {request.remote_addr}")
    if request.args:
        logging.info(f"Query params: {dict(request.args)}")

# ------------------------------
# User loader
# ------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------------
# Role decorators
# ------------------------------
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('admin')(f)

def teacher_required(f):
    return role_required('teacher', 'admin')(f)

def student_required(f):
    return role_required('student', 'teacher', 'admin')(f)

# ------------------------------
# Create tables & default admin
# ------------------------------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@college.edu', role='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        logging.info("Default admin user created: admin/admin123")

# ==============================
# Routes
# ==============================

# -------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    logging.info(f"Login accessed - Method: {request.method}")
    
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)  # persist session
            flash(f'Welcome back, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

# -------- Register ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        student_id = request.form.get('student_id') if role == 'student' else None
        teacher_id = request.form.get('teacher_id') if role == 'teacher' else None

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html', students=Student.query.all(), teachers=Teacher.query.all())
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('register.html', students=Student.query.all(), teachers=Teacher.query.all())

        # Validate student/teacher ID
        if role == 'student' and student_id and not Student.query.get(student_id):
            flash('Invalid student ID.', 'error')
            return render_template('register.html', students=Student.query.all(), teachers=Teacher.query.all())
        if role == 'teacher' and teacher_id and not Teacher.query.get(teacher_id):
            flash('Invalid teacher ID.', 'error')
            return render_template('register.html', students=Student.query.all(), teachers=Teacher.query.all())

        user = User(username=username, email=email, role=role, student_id=student_id, teacher_id=teacher_id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', students=Student.query.all(), teachers=Teacher.query.all())

# -------- Logout ----------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# -------- Index / Root ----------
@app.route('/')
def index_redirect():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))
# -------- Dashboard ----------
@app.route('/dashboard')
@login_required
def dashboard():
    """Redirect user to the correct dashboard based on their role."""
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif current_user.role == 'student':
        return redirect(url_for('student_dashboard'))
    else:
        flash("Invalid role!", "danger")
        return redirect(url_for('index'))


# -------- Admin Dashboard ----------
@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    total_students = Student.query.count()
    total_teachers = Teacher.query.count()
    total_courses = Course.query.count()
    total_departments = Department.query.count()
    return render_template(
        'admin_dashboard.html',
        total_students=total_students,
        total_teachers=total_teachers,
        total_courses=total_courses,
        total_departments=total_departments
    )


# -------- Teacher Dashboard ----------
@app.route('/teacher_dashboard')
@teacher_required
def teacher_dashboard():
    return render_template('teacher_dashboard.html')

# -------- Student Dashboard ----------
@app.route("/student_dashboard")
@login_required
def student_dashboard():
    student = Student.query.filter_by(email=current_user.email).first()

    # fetch grades & attendance (assuming relationships are set)
    grades = Grade.query.filter_by(student_id=student.id).all()
    attendance = Attendance.query.filter_by(student_id=student.id).all()

    return render_template(
        "student_dashboard.html",
        student=student,
        grades=grades,
        attendance=attendance
    )

# -------- Public Home Page ----------
@app.route('/index')
def index():
    """Public home page"""
    return render_template('index.html')

# Student Routes
@app.route('/students')
@admin_required
def students():
    """Display all students"""
    students_list = Student.query.all()
    return render_template('students.html', students=students_list)

@app.route('/add_student', methods=['GET', 'POST'])
@admin_required
def add_student():
    """Add new student"""
    if request.method == 'POST':
        try:
            student = Student(
                id=request.form['id'],
                name=request.form['name'],
                email=request.form['email'],
                course=request.form['course'] if request.form['course'] else None,
                department=request.form['department'] if request.form['department'] else None
            )
            db.session.add(student)
            db.session.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('students'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding student. Student ID may already exist.', 'error')
    
    courses = Course.query.all()
    departments = Department.query.all()
    return render_template('add_student.html', courses=courses, departments=departments)

@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    """Edit student information"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'POST':
        try:
            student.name = request.form['name']
            student.email = request.form['email']
            student.course = request.form['course'] if request.form['course'] else None
            student.department = request.form['department'] if request.form['department'] else None
            db.session.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating student.', 'error')
    
    courses = Course.query.all()
    departments = Department.query.all()
    return render_template('edit_student.html', student=student, courses=courses, departments=departments)

@app.route('/delete_student/<student_id>')
@admin_required
def delete_student(student_id):
    """Delete student"""
    try:
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        flash('Student deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting student.', 'error')
    return redirect(url_for('students'))

# Teacher Routes
@app.route('/teachers')
@admin_required
def teachers():
    """Display all teachers"""
    teachers_list = Teacher.query.all()
    return render_template('teachers.html', teachers=teachers_list)

@app.route('/add_teacher', methods=['GET', 'POST'])
@admin_required
def add_teacher():
    """Add new teacher"""
    if request.method == 'POST':
        try:
            teacher = Teacher(
                id=request.form['id'],
                name=request.form['name'],
                email=request.form['email'],
                department=request.form['department'],
                phone=request.form.get('phone', '')
            )
            db.session.add(teacher)
            db.session.commit()
            flash('Teacher added successfully!', 'success')
            return redirect(url_for('teachers'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding teacher. Teacher ID may already exist.', 'error')
    
    departments = Department.query.all()
    return render_template('add_teacher.html', departments=departments)

@app.route('/edit_teacher/<teacher_id>', methods=['GET', 'POST'])
@admin_required
def edit_teacher(teacher_id):
    """Edit teacher information"""
    teacher = Teacher.query.get_or_404(teacher_id)
    
    if request.method == 'POST':
        try:
            teacher.name = request.form['name']
            teacher.email = request.form['email']
            teacher.department = request.form['department']
            teacher.phone = request.form.get('phone', '')
            db.session.commit()
            flash('Teacher updated successfully!', 'success')
            return redirect(url_for('teachers'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating teacher.', 'error')
    
    departments = Department.query.all()
    return render_template('edit_teacher.html', teacher=teacher, departments=departments)

@app.route('/delete_teacher/<teacher_id>')
@admin_required
def delete_teacher(teacher_id):
    """Delete teacher"""
    try:
        teacher = Teacher.query.get_or_404(teacher_id)
        db.session.delete(teacher)
        db.session.commit()
        flash('Teacher deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting teacher.', 'error')
    return redirect(url_for('teachers'))

# Course Routes
@app.route('/courses')
@teacher_required
def courses():
    """Display all courses"""
    courses_list = Course.query.all()
    return render_template('courses.html', courses=courses_list)

@app.route('/add_course', methods=['GET', 'POST'])
@admin_required
def add_course():
    """Add new course"""
    if request.method == 'POST':
        try:
            course = Course(
                code=request.form['code'],
                name=request.form['name'],
                credits=int(request.form['credits']),
                instructor_id=request.form['instructor_id'] if request.form['instructor_id'] else None,
                department=request.form['department']
            )
            db.session.add(course)
            db.session.commit()
            flash('Course added successfully!', 'success')
            return redirect(url_for('courses'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding course. Course code may already exist.', 'error')
    
    teachers = Teacher.query.all()
    departments = Department.query.all()
    return render_template('add_course.html', teachers=teachers, departments=departments)

@app.route('/edit_course/<course_code>', methods=['GET', 'POST'])
@admin_required
def edit_course(course_code):
    """Edit course information"""
    course = Course.query.get_or_404(course_code)
    
    if request.method == 'POST':
        try:
            course.name = request.form['name']
            course.credits = int(request.form['credits'])
            course.instructor_id = request.form['instructor_id'] if request.form['instructor_id'] else None
            course.department = request.form['department']
            db.session.commit()
            flash('Course updated successfully!', 'success')
            return redirect(url_for('courses'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating course.', 'error')
    
    teachers = Teacher.query.all()
    departments = Department.query.all()
    return render_template('edit_course.html', course=course, teachers=teachers, departments=departments)

@app.route('/delete_course/<course_code>')
@admin_required
def delete_course(course_code):
    """Delete course"""
    try:
        course = Course.query.get_or_404(course_code)
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting course.', 'error')
    return redirect(url_for('courses'))

# Department Routes
@app.route('/departments')
@admin_required
def departments():
    """Display all departments"""
    departments_list = Department.query.all()
    return render_template('departments.html', departments=departments_list)

@app.route('/add_department', methods=['GET', 'POST'])
@admin_required
def add_department():
    """Add new department"""
    if request.method == 'POST':
        try:
            department = Department(
                code=request.form['code'],
                name=request.form['name'],
                head=request.form.get('head', ''),
                description=request.form.get('description', '')
            )
            db.session.add(department)
            db.session.commit()
            flash('Department added successfully!', 'success')
            return redirect(url_for('departments'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding department. Department code may already exist.', 'error')
    
    return render_template('add_department.html')

# Attendance Routes
@app.route('/attendance')
@teacher_required
def attendance():
    """Display attendance records"""
    attendance_records = Attendance.query.all()
    return render_template('attendance.html', attendance_records=attendance_records)

@app.route('/mark_attendance', methods=['GET', 'POST'])
@teacher_required
def mark_attendance():
    """Mark attendance for students"""
    if request.method == 'POST':
        try:
            # Parse date string to date object
            date_obj = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            
            # Check if attendance already exists for this student, course, and date
            existing_attendance = Attendance.query.filter_by(
                student_id=request.form['student_id'],
                course_code=request.form['course_code'],
                date=date_obj
            ).first()
            
            if existing_attendance:
                # Update existing attendance
                existing_attendance.status = request.form['status']
            else:
                # Create new attendance record
                attendance = Attendance(
                    student_id=request.form['student_id'],
                    course_code=request.form['course_code'],
                    date=date_obj,
                    status=request.form['status']
                )
                db.session.add(attendance)
            
            db.session.commit()
            flash('Attendance marked successfully!', 'success')
            return redirect(url_for('attendance'))
        except Exception as e:
            db.session.rollback()
            flash('Error marking attendance.', 'error')
    
    students = Student.query.all()
    courses = Course.query.all()
    return render_template('mark_attendance.html', students=students, courses=courses)

# Grades Routes
@app.route('/grades')
@teacher_required
def grades():
    """Display all grades"""
    grades_list = Grade.query.all()
    return render_template('grades.html', grades=grades_list)

@app.route('/add_grade', methods=['GET', 'POST'])
@teacher_required
def add_grade():
    """Add grade for student"""
    if request.method == 'POST':
        try:
            # Parse date string to date object
            date_obj = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            
            # Auto-calculate grade if not provided
            marks = float(request.form['marks'])
            max_marks = float(request.form['max_marks'])
            percentage = (marks / max_marks) * 100
            
            grade_letter = request.form['grade'] if request.form['grade'] else None
            if not grade_letter:
                if percentage >= 90:
                    grade_letter = 'A+'
                elif percentage >= 80:
                    grade_letter = 'A'
                elif percentage >= 70:
                    grade_letter = 'B'
                elif percentage >= 60:
                    grade_letter = 'C'
                else:
                    grade_letter = 'F'
            
            grade = Grade(
                student_id=request.form['student_id'],
                course_code=request.form['course_code'],
                grade=grade_letter,
                marks=marks,
                max_marks=max_marks,
                exam_type=request.form['exam_type'],
                date=date_obj
            )
            
            db.session.add(grade)
            db.session.commit()
            flash('Grade added successfully!', 'success')
            return redirect(url_for('grades'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding grade.', 'error')
    
    students = Student.query.all()
    courses = Course.query.all()
    return render_template('add_grade.html', students=students, courses=courses)

@app.route('/report_card/<student_id>')
@student_required
def report_card(student_id):
    """Generate report card for student"""
    student = Student.query.get_or_404(student_id)
    grades = Grade.query.filter_by(student_id=student_id).all()
    attendance = Attendance.query.filter_by(student_id=student_id).all()
    
    return render_template('report_card.html', student=student, grades=grades, attendance=attendance)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
