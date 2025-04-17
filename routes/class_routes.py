from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Class, Course, Student, Holiday, ClassSchedule
from datetime import datetime, timedelta
from datetime import time

class_bp = Blueprint('classroom', __name__, url_prefix='/class')  # ✅ เปลี่ยนชื่อ blueprint

def get_holiday_dates():
    return [h.date for h in Holiday.query.all()]


def generate_class_dates(start_date, repeat_days, total_sessions, holiday_dates):
    class_dates = []

    # ถ้า start_date เป็น string -> แปลงเป็น datetime
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    # ถ้า holiday_dates เป็น string list -> แปลงทุกตัว
    holiday_dates = [datetime.strptime(h, "%Y-%m-%d").date() if isinstance(h, str) else h for h in holiday_dates]

    current_date = start_date
    while len(class_dates) < total_sessions:
        if current_date.weekday() in repeat_days and current_date not in holiday_dates:
            class_dates.append(current_date)
        current_date += timedelta(days=1)
    return class_dates

@class_bp.route('/')
def class_list():
    classes = Class.query.all()
    class_data = []
    for cls in classes:
        schedules = ClassSchedule.query.filter_by(class_id=cls.id).order_by(ClassSchedule.date).all()
        last_date = schedules[-1].date.strftime('%Y-%m-%d') if schedules else None
        class_data.append({
            'class': cls,
            'total_sessions': cls.total_sessions,
            'schedules': schedules,
            'last_date': last_date
        })
    return render_template('class/list.html', class_list=class_data)

@class_bp.route('/add', methods=['GET', 'POST'])
def class_add():
    courses = Course.query.all()
    if request.method == 'POST':
        course_id = request.form['course_id']
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        days = list(map(int, request.form.getlist('days')))
        total_sessions = int(request.form['total_sessions'])
        name = request.form['name']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        if not days or all(day == '' for day in request.form.getlist('days')):
            flash('กรุณาเลือกวันเรียนอย่างน้อย 1 วัน', 'danger')
            return redirect(url_for('classroom.class_add'))

        holiday_dates = get_holiday_dates()
        class_dates = generate_class_dates(start_date, days, total_sessions, holiday_dates)

        new_class = Class(
            name=name,
            course_id=course_id,
            start_date=start_date,
            total_sessions=total_sessions,
            days=",".join(map(str, days)),
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(new_class)
        db.session.flush()  # get new_class.id

        for date in class_dates:
            schedule = ClassSchedule(
                class_id=new_class.id,
                date=date
            )
            db.session.add(schedule)

        db.session.commit()
        flash(f'เพิ่มคลาสเรียนจำนวน {len(class_dates)} วันเรียบร้อยแล้ว', 'success')
        return redirect(url_for('classroom.class_list'))  # ✅ ชื่อต้องตรงกับ blueprint

    return render_template('class/add.html', courses=courses)


@class_bp.route('/edit/<int:class_id>', methods=['GET', 'POST'])
def class_edit(class_id):
    class_instance = Class.query.get_or_404(class_id)
    courses = Course.query.all()

    if request.method == 'POST':
        class_instance.course_id = request.form['course_id']

        class_instance.name = request.form['name']
        class_instance.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        class_instance.days = ','.join(request.form.getlist('days'))  # save as comma string
        class_instance.total_sessions = int(request.form['total_sessions'])
        class_instance.start_time = request.form['start_time']
        class_instance.end_time = request.form['end_time']

        # อัปเดตคลาส
        db.session.commit()

        # ลบ ClassSchedule เดิม
        ClassSchedule.query.filter_by(class_id=class_instance.id).delete()

        # สร้างใหม่
        days = list(map(int, request.form.getlist('days')))
        holiday_dates = get_holiday_dates()
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        class_instance.start_date = start_date
        class_dates = generate_class_dates(start_date, days, class_instance.total_sessions, holiday_dates)

        for date in class_dates:
            schedule = ClassSchedule(class_id=class_instance.id, date=date)
            db.session.add(schedule)

        db.session.commit()
        flash('อัปเดตข้อมูลคลาสเรียนเรียบร้อยแล้ว', 'success')
        return redirect(url_for('classroom.class_list'))

    # สำหรับ GET
    days = list(map(int, class_instance.days.split(','))) if class_instance.days else []
    return render_template(
        'class/edit.html',
        class_instance=class_instance,
        courses=courses,
        days=days
    )


@class_bp.route('/delete/<int:class_id>', methods=['POST'])
def class_delete(class_id):
    class_instance = Class.query.get_or_404(class_id)

    # ลบ ClassSchedule ทั้งหมดที่เกี่ยวข้องก่อน
    ClassSchedule.query.filter_by(class_id=class_instance.id).delete()

    # ค่อยลบคลาส
    db.session.delete(class_instance)
    db.session.commit()

    flash('ลบคลาสเรียนเรียบร้อยแล้ว', 'success')
    return redirect(url_for('classroom.class_list'))

@class_bp.route('/view/<int:class_id>')
def class_view(class_id):
    class_instance = Class.query.get_or_404(class_id)
    if isinstance(class_instance.start_date, str):
        class_instance.start_date = datetime.strptime(class_instance.start_date, '%Y-%m-%d').date()
    return render_template('class/view.html', class_instance=class_instance)