from flask import Blueprint, redirect, url_for, flash
from db import db
from models import Student, Teacher, Course, Class, Holiday, User, Enrollment, ClassSchedule, TeacherAssignment, \
    TeacherUnavailableTime
from datetime import datetime, timedelta
import random
import string

demo_bp = Blueprint('demo', __name__)

@demo_bp.route('/demo/insert')
def insert():
    def random_suffix():
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    def random_thai_name():
        prefixes = ["ด.ช.", "ด.ญ."]
        first_names = ["ธีรภัทร", "ปวีณา", "นภัทร", "อาภา", "วรพล", "สุภัสรา", "ชลธิชา", "กันต์", "เกวลิน"]
        last_names = ["มงคล", "แสงทอง", "โชติชัย", "รุ่งเรือง", "บุญเกิด", "อัครเดช", "เพชรดี", "โสภณ"]
        return f"{random.choice(prefixes)} {random.choice(first_names)} {random.choice(last_names)}"

    def random_nickname():
        return random.choice(["บอส", "ใบตอง", "ปั้น", "ข้าวปั้น", "น้ำหวาน", "เจแปน", "แอล", "ฟิล์ม", "นัท"])

    def random_school():
        return random.choice(["โรงเรียนสาธิต", "โรงเรียนอัสสัมชัญ", "โรงเรียนสวนกุหลาบ", "โรงเรียนราชวินิต", "โรงเรียนสตรีวิทยา"])

    def random_grade():
        return random.choice(["ป.1", "ป.2", "ป.3", "ป.4", "ป.5", "ป.6", "ม.1", "ม.2", "ม.3"])

    def random_email(name):
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        return f"{name.lower().replace(' ', '')}_{suffix}@example.com"

    def random_teacher_name():
        names = ["บีม", "พลอย", "น้ำ", "เจ", "พี", "ตูน", "เมย์", "แนท", "เอ็ม"]
        return f"ครู{random.choice(names)}"

    def random_course_title():
        topics = ["Python", "Robotics", "Arduino", "Scratch"]
        levels = ["for Kids", "Basic", "Advanced", "Workshop"]
        return f"{random.choice(topics)} {random.choice(levels)}"

    def random_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    def random_day():
        return str(random.choice(range(7)))  # 0=Monday ... 6=Sunday

    def random_time():
        hour = random.randint(9, 15)
        start = f"{hour:02}:00"
        end = f"{hour + 2:02}:00"
        return start, end

    def random_future_date():
        return (datetime.today() + timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d")

    # สร้างข้อมูลนักเรียน
    student1_name = random_thai_name()
    student2_name = random_thai_name()
    student1 = Student(
        name=student1_name,
        nickname=random_nickname(),
        school_name=random_school(),
        school_level=random_grade(),
        email=random_email(student1_name),
        phone=f"089{random.randint(1000000, 9999999)}"
    )
    student2 = Student(
        name=student2_name,
        nickname=random_nickname(),
        school_name=random_school(),
        school_level=random_grade(),
        email=random_email(student2_name),
        phone=f"081{random.randint(1000000, 9999999)}"
    )
    db.session.add_all([student1, student2])

    # สร้างข้อมูลครู
    teacher1 = Teacher(name=random_teacher_name(), email=f"beam_{random_suffix()}@example.com", phone=f"081{random.randint(1000000, 9999999)}")
    teacher2 = Teacher(name=random_teacher_name(), email=f"ploy_{random_suffix()}@example.com", phone=f"082{random.randint(1000000, 9999999)}")
    db.session.add_all([teacher1, teacher2])

    # สร้างคอร์ส
    course1 = Course(title=random_course_title(), color=random_color())
    course2 = Course(title=random_course_title(), color=random_color())
    db.session.add_all([course1, course2])
    db.session.flush()

    # สร้างคลาส
    def create_class(course):
        day = random_day()
        start_time, end_time = random_time()
        start_date = random_future_date()
        class_name = f"{course.title} {'Sat' if day == '6' else 'Sun'} {'AM' if int(start_time[:2]) < 12 else 'PM'}"
        return Class(
            course_id=course.id,
            name=class_name,
            total_sessions=4,
            days=day,
            start_time=start_time,
            end_time=end_time,
            start_date=start_date,
            schedule="[]",
            required_specialty=course.title.split()[0]
        )

    class1 = create_class(course1)
    class2 = create_class(course2)
    db.session.add_all([class1, class2])
    db.session.flush()

    # สร้างตารางเรียนจากวันที่
    def create_class_schedule(cls):
        start = datetime.strptime(cls.start_date, "%Y-%m-%d").date()
        scheduled_dates = []
        day_indexes = list(map(int, cls.days.split(",")))
        current = start
        while len(scheduled_dates) < cls.total_sessions:
            if current.weekday() in day_indexes:
                scheduled_dates.append(current)
            current += timedelta(days=1)
        for date in scheduled_dates:
            schedule = ClassSchedule(class_id=cls.id, date=date)
            db.session.add(schedule)

    create_class_schedule(class1)
    create_class_schedule(class2)

    # วันหยุดตัวอย่าง
    holiday = Holiday(date=datetime.today().strftime("%Y-%m-%d"), note="วันแรงงานแห่งชาติ")
    db.session.add(holiday)

    # เพิ่มผู้ใช้ถ้ายังไม่มี
    if not User.query.filter_by(username="admin").first():
        user = User(username="admin", name="ผู้ดูแล", email="admin@example.com", password_hash="admin123")
        db.session.add(user)

    db.session.flush()

    # ลงทะเบียนเรียน
    db.session.add_all([
        Enrollment(student_id=student1.id, class_id=class1.id),
        Enrollment(student_id=student2.id, class_id=class2.id)
    ])

    db.session.commit()
    flash("เพิ่มข้อมูลตัวอย่างเรียบร้อยแล้ว!", "success")
    return redirect(url_for("student.student_list"))

@demo_bp.route('/demo/clear')
def clear():
    db.session.query(Enrollment).delete()
    db.session.query(ClassSchedule).delete()
    db.session.query(Class).delete()
    db.session.query(Course).delete()
    db.session.query(Student).delete()
    db.session.query(Teacher).delete()
    db.session.query(TeacherAssignment).delete()
    db.session.query(TeacherUnavailableTime).delete()
    db.session.query(Holiday).delete()
    db.session.commit()
    flash("ลบข้อมูลตัวอย่างเรียบร้อยแล้ว!", "success")
    return redirect(url_for("student.student_list"))
