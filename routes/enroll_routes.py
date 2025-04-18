from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from models import Student, Class, Enrollment , Course
from db import db
from datetime import datetime, timedelta

from routes.course_routes import course_list

enroll_bp = Blueprint('enroll', __name__)

@enroll_bp.route('/enrollments')
def enrollment_list():
    class_list = Class.query.all()
    course_list = Course.query.all()

    return render_template(
        'enrollment/list.html',
        class_list=class_list,
        course_list=course_list,
    )

@enroll_bp.route('/enroll', methods=['GET', 'POST'])
def enroll_form():

    students = Student.query.with_entities(Student.id, Student.name).all()
    all_classes_raw = Class.query.all()
    today = datetime.now().date()

    def get_day_display(days_str):
        day_map = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัส', 'ศุกร์', 'เสาร์', 'อาทิตย์']
        day_indexes = [int(d) for d in days_str.split(',') if d.isdigit()]
        return ', '.join(day_map[i] for i in day_indexes)

    def get_end_date(class_id, start_date, total_sessions, days):
        from models import ClassSchedule  # เพิ่มถ้ายังไม่มี

        # ดึงรายการ schedule ตาม class_id แล้วเรียงจากวันล่าสุด
        class_schedules = ClassSchedule.query.filter_by(class_id=class_id).order_by(ClassSchedule.date.desc()).all()

        if class_schedules:
            return class_schedules[0].date  # คืนวันที่ล่าสุด
        return start_date  # fallback ถ้าไม่เจออะไรเลย

    all_classes = []
    for cls in all_classes_raw:
        if isinstance(cls.start_date, str):
            cls_start_date = datetime.strptime(cls.start_date, "%Y-%m-%d").date()
        else:
            cls_start_date = cls.start_date

        end_date = get_end_date(cls.id, cls_start_date, cls.total_sessions, cls.days)
        if end_date >= today:
            all_classes.append({
                'id': cls.id,
                'name': cls.name,
                'start_time': cls.start_time,
                'end_time': cls.end_time,
                'start_date': cls_start_date,
                'end_date': end_date,
                'day_display': get_day_display(cls.days),
                'course': {
                    'title': str(cls.course.title),
                    'color': str(cls.course.color)
                }
            })
            print("📌 class:", cls.name, "start_date:", cls_start_date, "end_date:", end_date)

    if request.method == 'POST':
        student_id = request.form['student_id']
        class_id_raw = request.form.get('class_id', '').strip()
        if not class_id_raw.isdigit():
            flash('กรุณาเลือกคลาสเรียนก่อนลงทะเบียน', 'danger')
            return redirect(url_for('enroll.enrollment_list'))
        class_id = int(class_id_raw)
        enrollment = Enrollment(student_id=student_id, class_id=class_id)
        db.session.add(enrollment)
        db.session.commit()
        flash("ลงทะเบียนเรียบร้อยแล้ว", "success")
        return redirect(url_for('enroll.enrollment_list'))

    enrollments = Enrollment.query.all()
    return render_template('enrollment/add.html', students=students, all_classes=all_classes)

@enroll_bp.route('/get_available_classes/<int:student_id>')
def get_available_classes(student_id):
    enrolled_class_ids = db.session.query(Enrollment.class_id).filter_by(student_id=student_id).all()
    enrolled_class_ids = [id for (id,) in enrolled_class_ids]
    available_classes = Class.query.filter(~Class.id.in_(enrolled_class_ids)).all()

    return jsonify([
        {'id': c.id, 'name': c.name} for c in available_classes
    ])

@enroll_bp.route('/api/student_enrollments/<int:student_id>')
def get_student_enrollments(student_id):
    from models import ClassSchedule

    enrollments = (
        db.session.query(Enrollment, Class, Course)
        .join(Class, Enrollment.class_id == Class.id)
        .join(Course, Class.course_id == Course.id)
        .filter(Enrollment.student_id == student_id)
        .all()
    )

    result = []
    for enrollment, cls, course in enrollments:
        # ดึงวันเรียนแบบตัวเลข แล้วแปลงเป็นชื่อวัน
        day_indexes = list(map(int, cls.days.split(',')))
        day_map = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']
        day_names = [day_map[i] for i in day_indexes]

        result.append({
            'class_name': cls.name,
            'course_title': course.title,
            'days': day_names,
            'start_time': cls.start_time,
            'end_time': cls.end_time
        })

    return jsonify(result)
