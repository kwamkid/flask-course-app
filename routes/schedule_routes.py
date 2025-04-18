from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import Teacher, TeacherAssignment, Class, Course, ClassSchedule, TeacherUnavailableTime
from db import db
from datetime import datetime, timedelta

schedule_bp = Blueprint('schedule', __name__, url_prefix='/schedule')


def is_teacher_available(teacher, class_obj, schedule_date):
    # ตรวจสอบว่าครูว่างในช่วงเวลาที่คลาสนี้จัดหรือไม่
    day_of_week = schedule_date.weekday()
    class_start = datetime.strptime(class_obj.start_time, '%H:%M').time()
    class_end = datetime.strptime(class_obj.end_time, '%H:%M').time()

    # ตรวจสอบเวลาที่ครูไม่ว่าง
    unavailable_times = TeacherUnavailableTime.query.filter_by(
        teacher_id=teacher.id,
        day_of_week=day_of_week
    ).all()

    for unavail in unavailable_times:
        unavail_start = datetime.strptime(unavail.start_time, '%H:%M').time()
        unavail_end = datetime.strptime(unavail.end_time, '%H:%M').time()

        # ตรวจสอบว่าช่วงเวลาซ้อนทับกันหรือไม่
        if (class_start < unavail_end and class_end > unavail_start):
            return False

    # ตรวจสอบว่าครูมีคลาสอื่นซ้อนทับในวันเดียวกันหรือไม่
    existing_assignments = db.session.query(TeacherAssignment, Class, ClassSchedule). \
        join(Class, TeacherAssignment.class_id == Class.id). \
        join(ClassSchedule, Class.id == ClassSchedule.class_id). \
        filter(
        TeacherAssignment.teacher_id == teacher.id,
        ClassSchedule.date == schedule_date
    ).all()

    for assignment, assigned_class, schedule in existing_assignments:
        assigned_start = datetime.strptime(assigned_class.start_time, '%H:%M').time()
        assigned_end = datetime.strptime(assigned_class.end_time, '%H:%M').time()

        # ตรวจสอบว่าช่วงเวลาซ้อนทับกันหรือไม่
        if (class_start < assigned_end and class_end > assigned_start):
            return False

    return True


def is_teacher_qualified(teacher, class_obj):
    # ตรวจสอบว่าครูมีความเชี่ยวชาญตรงกับคลาสนี้หรือไม่
    if not class_obj.required_specialty:
        return True  # ถ้าคลาสไม่ต้องการความเชี่ยวชาญเฉพาะ

    return teacher.has_specialty(class_obj.required_specialty)


def auto_assign_teachers():
    # ดึงข้อมูลคลาสที่ยังไม่มีครูสอน
    unassigned_classes = db.session.query(Class).outerjoin(
        TeacherAssignment, Class.id == TeacherAssignment.class_id
    ).filter(
        TeacherAssignment.id.is_(None)
    ).all()
    print(len(unassigned_classes))

    all_teachers = Teacher.query.all()

    assignments_made = 0

    for class_obj in unassigned_classes:
        # ดึงตารางเรียนของคลาสนี้
        schedules = ClassSchedule.query.filter_by(class_id=class_obj.id).all()

        # หาครูที่เหมาะสมที่สุด
        best_teacher = None
        best_teacher_load = float('inf')  # เริ่มต้นด้วยค่าที่สูงมาก
        print(len(all_teachers))
        for teacher in all_teachers:
            # ตรวจสอบคุณสมบัติก่อน
            print(f"Checking teacher {teacher.name} with specialties {teacher.specialties} for class {class_obj.name} which requires {class_obj.required_specialty}")
            if not is_teacher_qualified(teacher, class_obj):
                continue

            # ตรวจสอบว่าครูสามารถสอนได้ในทุกคาบหรือไม่
            can_teach_all = True
            for schedule in schedules:
                print(f"[SKIP] ครู {teacher.name} ไม่ว่างหรือไม่ตรงคุณสมบัติ กับคลาส {class_obj.name}")
                if not is_teacher_available(teacher, class_obj, schedule.date):
                    can_teach_all = False
                    break

            if can_teach_all:
                # ตรวจสอบภาระงานปัจจุบันของครู
                current_load = TeacherAssignment.query.filter_by(teacher_id=teacher.id).count()
                if current_load < best_teacher_load:
                    best_teacher = teacher
                    best_teacher_load = current_load

        if best_teacher:
            # จัดครูให้กับคลาสนี้
            assignment = TeacherAssignment(
                teacher_id=best_teacher.id,
                class_id=class_obj.id
            )
            db.session.add(assignment)
            assignments_made += 1
        else:
            flash(f'ไม่สามารถจัดครูให้คลาส "{class_obj.name}" ได้ เพราะไม่มีครูที่ว่างและตรงคุณสมบัติ', 'warning')
            continue

    db.session.commit()
    return assignments_made


@schedule_bp.route('/auto-assign', methods=['GET', 'POST'])
def auto_assign():
    if request.method == 'POST':
        print("Yess Man")
        assignments_made = auto_assign_teachers()
        flash(f'จัดตารางสอนอัตโนมัติเรียบร้อยแล้ว {assignments_made} คลาส', 'success')
        return redirect(url_for('schedule.view'))

    return render_template('schedule/auto_assign.html')


@schedule_bp.route('/view')
def view():
    assignments = db.session.query(
        TeacherAssignment, Teacher, Class, Course
    ).join(
        Teacher, TeacherAssignment.teacher_id == Teacher.id
    ).join(
        Class, TeacherAssignment.class_id == Class.id
    ).join(
        Course, Class.course_id == Course.id
    ).all()

    return render_template('schedule/view.html', assignments=assignments)


@schedule_bp.route('/manual-assign', methods=['GET', 'POST'])
def manual_assign():
    if request.method == 'POST':
        teacher_id = request.form['teacher_id']
        class_id = request.form['class_id']

        # ตรวจสอบว่ามีการจัดครูให้คลาสนี้แล้วหรือไม่
        existing = TeacherAssignment.query.filter_by(class_id=class_id).first()
        if existing:
            existing.teacher_id = teacher_id
        else:
            assignment = TeacherAssignment(
                teacher_id=teacher_id,
                class_id=class_id
            )
            db.session.add(assignment)

        db.session.commit()
        flash('จัดครูให้คลาสเรียนเรียบร้อยแล้ว', 'success')
        return redirect(url_for('schedule.view'))

    teachers = Teacher.query.all()

    # ตรวจสอบว่า class_id ที่ถูก assign ไปแล้วมีอะไรบ้าง
    assigned_class_ids = db.session.query(TeacherAssignment.class_id).distinct().all()
    print(f"assigned_class_ids (raw): {assigned_class_ids}")
    assigned_class_ids = [cid for (cid,) in assigned_class_ids]
    print(f"assigned_class_ids (flatten): {assigned_class_ids}")

    # ตรวจสอบว่า unassigned_classes หาได้กี่คลาส
    unassigned_classes = Class.query.filter(~Class.id.in_(assigned_class_ids)).all()
    print(f"unassigned_classes count: {len(unassigned_classes)}")
    for cls in unassigned_classes:
        print(f"Unassigned Class: {cls.id} - {cls.name}")

    print("Rendering manual_assign.html")
    return render_template(
        'schedule/manual_assign.html',
        teachers=teachers,
        unassigned_classes=unassigned_classes
    )


@schedule_bp.route('/change-teacher/<int:assignment_id>', methods=['GET', 'POST'])
def change_teacher(assignment_id):
    assignment = TeacherAssignment.query.get_or_404(assignment_id)
    class_obj = Class.query.get_or_404(assignment.class_id)

    if request.method == 'POST':
        new_teacher_id = request.form['teacher_id']
        assignment.teacher_id = new_teacher_id
        db.session.commit()
        flash('เปลี่ยนครูให้คลาสเรียนเรียบร้อยแล้ว', 'success')
        return redirect(url_for('schedule.view'))

    teachers = Teacher.query.all()
    return render_template('schedule/change_teacher.html', assignment=assignment, class_obj=class_obj,
                           teachers=teachers)


@schedule_bp.route('/delete-assignment/<int:assignment_id>', methods=['POST'])
def delete_assignment(assignment_id):
    assignment = TeacherAssignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash('ลบการจัดครูเรียบร้อยแล้ว', 'success')
    return redirect(url_for('schedule.view'))