from datetime import datetime
from db import db


class TrialClass(db.Model):
    """คลาสสำหรับทดลองเรียน"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    max_students = db.Column(db.Integer, default=5)  # จำนวนนักเรียนสูงสุดต่อช่วงเวลา
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # ความสัมพันธ์กับตารางอื่น
    course = db.relationship('Course', backref=db.backref('trial_classes', lazy=True))
    time_slots = db.relationship('TrialTimeSlot', backref='trial_class', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        """แปลงข้อมูลเป็น dict สำหรับ API"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'course_id': self.course_id,
            'course_name': self.course.title if self.course else None,
            'max_students': self.max_students,
        }


class TrialTimeSlot(db.Model):
    """ช่วงเวลาที่เปิดให้จองทดลองเรียน"""
    id = db.Column(db.Integer, primary_key=True)
    trial_class_id = db.Column(db.Integer, db.ForeignKey('trial_class.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(8), nullable=False)  # รูปแบบ "HH:MM"
    end_time = db.Column(db.String(8), nullable=False)  # รูปแบบ "HH:MM"
    max_students = db.Column(db.Integer,
                             nullable=True)  # จำกัดจำนวนนักเรียนเฉพาะช่วงเวลานี้ (ถ้าไม่กำหนดจะใช้ค่าจาก TrialClass)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # ความสัมพันธ์กับตารางอื่น
    bookings = db.relationship('TrialBooking', backref='time_slot', lazy=True, cascade="all, delete-orphan")

    @property
    def available_slots(self):
        """คำนวณจำนวนที่นั่งว่างสำหรับช่วงเวลานี้"""
        max_capacity = self.max_students if self.max_students is not None else self.trial_class.max_students
        booked = len([b for b in self.bookings if b.status == 'confirmed'])
        return max(0, max_capacity - booked)

    @property
    def is_full(self):
        """ตรวจสอบว่าช่วงเวลาเต็มหรือไม่"""
        return self.available_slots == 0

    @property
    def booking_count(self):
        """นับจำนวนการจองที่ยืนยันแล้ว"""
        return len([b for b in self.bookings if b.status == 'confirmed'])

    def to_dict(self):
        """แปลงข้อมูลเป็น dict สำหรับ API"""
        max_students = self.max_students or self.trial_class.max_students
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'start_time': self.start_time,
            'end_time': self.end_time,
            'max_students': max_students,
            'available_slots': self.available_slots,
            'is_full': self.is_full,
            'booking_count': self.booking_count,
            'is_active': self.is_active,
            'trial_class': {
                'id': self.trial_class.id,
                'title': self.trial_class.title
            }
        }


class TrialBooking(db.Model):
    """ข้อมูลการจองทดลองเรียน"""
    id = db.Column(db.Integer, primary_key=True)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('trial_time_slot.id'), nullable=False)
    student_name = db.Column(db.String(100), nullable=False)
    student_nickname = db.Column(db.String(50))
    student_age = db.Column(db.Integer)
    student_school = db.Column(db.String(100))
    student_grade = db.Column(db.String(20))
    parent_name = db.Column(db.String(100), nullable=False)
    parent_phone = db.Column(db.String(20), nullable=False)
    parent_email = db.Column(db.String(100))
    parent_line_id = db.Column(db.String(50))
    special_request = db.Column(db.Text)
    source = db.Column(db.String(50))  # แหล่งที่มา (เช่น Facebook, Line, Website)

    # สถานะการจอง: 'pending', 'confirmed', 'canceled', 'completed', 'no_show'
    status = db.Column(db.String(20), default='confirmed')

    # ดูแลโดยใคร
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    teacher = db.relationship('Teacher', backref=db.backref('trial_sessions', lazy=True))

    # สำหรับเก็บบันทึกข้อมูลการสมัครจริงหลังทดลองเรียน
    converted = db.Column(db.Boolean, default=False)  # แปลงเป็นนักเรียนจริงหรือไม่
    converted_student_id = db.Column(db.Integer, db.ForeignKey('student.id'),
                                     nullable=True)  # ลิงก์ไปยัง Student หลังจากสมัครเรียน
    converted_at = db.Column(db.DateTime, nullable=True)  # เวลาที่สมัครเรียน

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    student = db.relationship('Student', backref=db.backref('trial_bookings', lazy=True),
                              foreign_keys=[converted_student_id])

    def to_dict(self):
        """แปลงข้อมูลเป็น dict สำหรับ API"""
        return {
            'id': self.id,
            'student_name': self.student_name,
            'student_nickname': self.student_nickname,
            'student_age': self.student_age,
            'student_school': self.student_school,
            'student_grade': self.student_grade,
            'parent_name': self.parent_name,
            'parent_phone': self.parent_phone,
            'parent_email': self.parent_email,
            'parent_line_id': self.parent_line_id,
            'special_request': self.special_request,
            'status': self.status,
            'converted': self.converted,
            'time_slot': {
                'id': self.time_slot_id,
                'date': self.time_slot.date.strftime('%Y-%m-%d'),
                'start_time': self.time_slot.start_time,
                'end_time': self.time_slot.end_time,
                'trial_class': {
                    'id': self.time_slot.trial_class.id,
                    'title': self.time_slot.trial_class.title
                }
            }
        }