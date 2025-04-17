# models.py
from db import db  # ✅ นำ db จาก db.py มาใช้
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(100))  # ✅ ถ้าคุณใช้ name ใน register ต้องมีตรงนี้
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)  # รูปแบบ 'YYYY-MM-DD'
    note = db.Column(db.String(255))  # หมายเหตุ เช่น "วันสงกรานต์"

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(10), default='#3788d8')
    classes = db.relationship('Class', backref='course', cascade='all, delete-orphan')

class Class(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    total_sessions = db.Column(db.Integer, nullable=False)
    days = db.Column(db.String(50), nullable=False)  # เช่น "Monday,Saturday"
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    start_date = db.Column(db.String(10), nullable=False)
    schedule = db.Column(db.Text)  # เก็บเป็น JSON string
    schedules = db.relationship("ClassSchedule", back_populates="class_instance", cascade="all, delete-orphan")

class ClassSchedule(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    class_instance = db.relationship("Class", back_populates="schedules")

class Student(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # ชื่อ-นามสกุล
    nickname = db.Column(db.String(50))  # ชื่อเล่น
    phone = db.Column(db.String(50))  # เบอร์มือถือของน้อง (อาจมีหลายเบอร์)
    email = db.Column(db.String(100))  # อีเมลของน้อง
    birthday = db.Column(db.String(10))  # วันเกิดน้อง (YYYY-MM-DD)
    gender = db.Column(db.String(10))  # เพศ
    school_name = db.Column(db.String(100))  # ชื่อโรงเรียน
    school_level = db.Column(db.String(50))  # ระดับชั้นเรียน
    health_condition = db.Column(db.String(255))  # โรคประจำตัว
    health_detail = db.Column(db.String(255))  # รายละเอียดโรคประจำตัว
    allow_photo = db.Column(db.String(50))  # อนุญาตให้ถ่ายรูป หรือ VDO ได้
    allow_paracetamol = db.Column(db.String(50))  # อนุญาตให้ให้ยาพาราเซตามอลได้
    school_type = db.Column(db.String(20))  # ตัวอย่างค่า: 'ไทย', 'inter'


class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id', ondelete="CASCADE"))  # ใช้ PostgreSQL/MySQL ถึงจะมีผล
    # ...

    student = db.relationship('Student', backref='enrollments')
    class_ = db.relationship('Class',
                             backref=db.backref('enrollments', cascade="all, delete", passive_deletes=True))
