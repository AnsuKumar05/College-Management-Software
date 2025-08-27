from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'teacher', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign key links to existing models
    student_id = db.Column(db.String(50), db.ForeignKey('students.id'), nullable=True)
    teacher_id = db.Column(db.String(50), db.ForeignKey('teachers.id'), nullable=True)
    
    # Relationships
    student = db.relationship('Student', backref='user_account', lazy=True)
    teacher = db.relationship('Teacher', backref='user_account', lazy=True)
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'student_id': self.student_id,
            'teacher_id': self.teacher_id
        }

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    course = db.Column(db.String(50))
    department = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='student_info', lazy=True)
    grades = db.relationship('Grade', backref='student_info', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'course': self.course,
            'department': self.department
        }

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    department = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    courses = db.relationship('Course', backref='instructor', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'phone': self.phone
        }

class Department(db.Model):
    __tablename__ = 'departments'
    
    code = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    head = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'code': self.code,
            'name': self.name,
            'head': self.head,
            'description': self.description
        }

class Course(db.Model):
    __tablename__ = 'courses'
    
    code = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    instructor_id = db.Column(db.String(50), db.ForeignKey('teachers.id'))
    department = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='course_info', lazy=True)
    grades = db.relationship('Grade', backref='course_info', lazy=True)
    
    def to_dict(self):
        return {
            'code': self.code,
            'name': self.name,
            'credits': self.credits,
            'instructor_id': self.instructor_id,
            'department': self.department
        }

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.id'), nullable=False)
    course_code = db.Column(db.String(20), db.ForeignKey('courses.code'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present, Absent, Late, Excused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate attendance for same student, course, and date
    __table_args__ = (db.UniqueConstraint('student_id', 'course_code', 'date', name='unique_attendance'),)
    
    def to_dict(self):
        return {
            'student_id': self.student_id,
            'course_code': self.course_code,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'status': self.status
        }

class Grade(db.Model):
    __tablename__ = 'grades'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(50), db.ForeignKey('students.id'), nullable=False)
    course_code = db.Column(db.String(20), db.ForeignKey('courses.code'), nullable=False)
    grade = db.Column(db.String(5))  # A+, A, B, C, D, F
    marks = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)  # Quiz, Assignment, Midterm, Final, Project, Lab
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'student_id': self.student_id,
            'course_code': self.course_code,
            'grade': self.grade,
            'marks': self.marks,
            'max_marks': self.max_marks,
            'exam_type': self.exam_type,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None
        }