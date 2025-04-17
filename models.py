# models.py
from db import db  # ✅ นำ db จาก db.py มาใช้

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
    name = db.Column(db.String(100), nullable=False)
    nickname = db.Column(db.String(50))
    school = db.Column(db.String(100))
    grade = db.Column(db.String(50))
    birthday = db.Column(db.String(10))  # รูปแบบ YYYY-MM-DD
    allergy = db.Column(db.String(255))
    health = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    emergency_name1 = db.Column(db.String(100))
    emergency_phone1 = db.Column(db.String(20))
    emergency_name2 = db.Column(db.String(100))
    emergency_phone2 = db.Column(db.String(20))

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id', ondelete="CASCADE"))  # ใช้ PostgreSQL/MySQL ถึงจะมีผล
    # ...

    student = db.relationship('Student', backref='enrollments')
    class_ = db.relationship('Class',
                             backref=db.backref('enrollments', cascade="all, delete", passive_deletes=True))
