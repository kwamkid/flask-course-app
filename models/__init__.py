from db import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


# นำเข้าโมเดลที่มีอยู่ในระบบเดิม

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(30), default="#3788d8")

    def __repr__(self):
        return f"<Course {self.title}>"


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    total_sessions = db.Column(db.Integer, default=1)
    days = db.Column(db.String(30), nullable=False)  # comma separated list of day indices
    start_time = db.Column(db.String(8), nullable=False, default="09:00")  # format: "HH:MM"
    end_time = db.Column(db.String(8), nullable=False, default="10:00")  # format: "HH:MM"
    schedule = db.Column(db.Text, default="[]")  # JSON array of dates
    required_specialty = db.Column(db.String(100), nullable=True)  # ความเชี่ยวชาญที่จำเป็น (เช่น Python, Robotics)

    # ความสัมพันธ์
    course = db.relationship('Course', backref=db.backref('classes', lazy=True))
    enrollments = db.relationship('Enrollment', backref='class_', lazy=True, cascade="all, delete-orphan")
    schedules = db.relationship('ClassSchedule', backref='class_', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Class {self.name}>"


class ClassSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"<ClassSchedule {self.class_id} {self.date}>"


class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(200))

    def __repr__(self):
        return f"<Holiday {self.date}>"


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    birthday = db.Column(db.Date)
    gender = db.Column(db.String(10))
    school_name = db.Column(db.String(100))
    school_type = db.Column(db.String(50))  # 'ไทย' หรือ 'inter'
    school_level = db.Column(db.String(20))
    health_condition = db.Column(db.String(100))
    health_detail = db.Column(db.Text)
    allow_photo = db.Column(db.Boolean, default=True)
    allow_paracetamol = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Student {self.name}>"


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)

    # ความสัมพันธ์
    student = db.relationship('Student', backref=db.backref('enrollments', lazy=True))

    def __repr__(self):
        return f"<Enrollment {self.student_id} in {self.class_id}>"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    image_filename = db.Column(db.String(100))
    specialties = db.Column(db.String(200))  # ความเชี่ยวชาญ เช่น "Python,Arduino,Robotics"
    max_hours_per_week = db.Column(db.Integer, default=40)

    def has_specialty(self, specialty):
        if not self.specialties:
            return False
        specialties_list = self.specialties.split(',')
        return specialty in specialties_list

    def __repr__(self):
        return f"<Teacher {self.name}>"


class TeacherAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)

    teacher = db.relationship('Teacher', backref=db.backref('assignments', lazy=True))
    class_ = db.relationship('Class', backref=db.backref('teacher_assignment', lazy=True))

    def __repr__(self):
        return f"<TeacherAssignment {self.teacher_id} to {self.class_id}>"


class TeacherUnavailableTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    start_time = db.Column(db.String(8), nullable=False)  # format: "HH:MM"
    end_time = db.Column(db.String(8), nullable=False)  # format: "HH:MM"

    teacher = db.relationship('Teacher', backref=db.backref('unavailable_times', lazy=True))

    def __repr__(self):
        return f"<TeacherUnavailableTime {self.teacher_id} on day {self.day_of_week}>"