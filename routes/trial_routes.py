from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, flash, current_app
from models.trial_models import TrialClass, TrialTimeSlot, TrialBooking
from models import Course, Teacher, Student
from db import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import json
import csv
import io
import pandas as pd
from flask_login import current_user, login_required
import os

trial_bp = Blueprint('trial', __name__, url_prefix='/trial')


# -----------------------------------
# หน้าสำหรับผู้ดูแลระบบ (Admin Routes)
# -----------------------------------

@trial_bp.route('/')
@login_required
def index():
    """หน้าแสดงรายการคลาสทดลองเรียนทั้งหมด"""
    trial_classes = TrialClass.query.all()
    return render_template('trial/index.html', trial_classes=trial_classes)


@trial_bp.route('/class/add', methods=['GET', 'POST'])
@login_required
def add_trial_class():
    """หน้าเพิ่มคลาสทดลองเรียนใหม่"""
    courses = Course.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        course_id = request.form.get('course_id')
        if course_id == '':
            course_id = None
        max_students = request.form.get('max_students', 5)

        trial_class = TrialClass(
            title=title,
            description=description,
            course_id=course_id,
            max_students=max_students
        )

        db.session.add(trial_class)
        db.session.commit()

        flash('เพิ่มคลาสทดลองเรียนเรียบร้อยแล้ว', 'success')
        return redirect(url_for('trial.index'))

    return render_template('trial/add_class.html', courses=courses)


@trial_bp.route('/class/<int:class_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trial_class(class_id):
    """หน้าแก้ไขคลาสทดลองเรียน"""
    trial_class = TrialClass.query.get_or_404(class_id)
    courses = Course.query.all()

    if request.method == 'POST':
        trial_class.title = request.form.get('title')
        trial_class.description = request.form.get('description', '')
        course_id = request.form.get('course_id')
        if course_id == '':
            trial_class.course_id = None
        else:
            trial_class.course_id = course_id
        trial_class.max_students = request.form.get('max_students', 5)

        db.session.commit()

        flash('แก้ไขคลาสทดลองเรียนเรียบร้อยแล้ว', 'success')
        return redirect(url_for('trial.index'))

    return render_template('trial/edit_class.html', trial_class=trial_class, courses=courses)


@trial_bp.route('/class/<int:class_id>/delete', methods=['POST'])
@login_required
def delete_trial_class(class_id):
    """ลบคลาสทดลองเรียน"""
    trial_class = TrialClass.query.get_or_404(class_id)

    # ตรวจสอบว่ามีการจองแล้วหรือไม่
    has_bookings = False
    for time_slot in trial_class.time_slots:
        if time_slot.bookings:
            has_bookings = True
            break

    if has_bookings:
        flash('ไม่สามารถลบคลาสได้เนื่องจากมีการจองแล้ว', 'danger')
        return redirect(url_for('trial.index'))

    db.session.delete(trial_class)
    db.session.commit()

    flash('ลบคลาสทดลองเรียนเรียบร้อยแล้ว', 'success')
    return redirect(url_for('trial.index'))


@trial_bp.route('/class/<int:class_id>/slots', methods=['GET', 'POST'])
@login_required
def manage_time_slots(class_id):
    """หน้าจัดการช่วงเวลาสำหรับคลาสทดลองเรียน"""
    trial_class = TrialClass.query.get_or_404(class_id)
    time_slots = TrialTimeSlot.query.filter_by(trial_class_id=class_id).order_by(TrialTimeSlot.date,
                                                                                 TrialTimeSlot.start_time).all()

    if request.method == 'POST':
        date = request.form.get('date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        max_students = request.form.get('max_students')

        # ตรวจสอบว่าเป็นวันเสาร์หรืออาทิตย์หรือไม่
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        if date_obj.weekday() not in [5, 6]:  # 5 = Saturday, 6 = Sunday
            flash('กรุณาเลือกวันเสาร์หรืออาทิตย์เท่านั้น', 'danger')
            return redirect(url_for('trial.manage_time_slots', class_id=class_id))

        # ตรวจสอบว่าช่วงเวลาซ้ำหรือไม่
        existing_slot = TrialTimeSlot.query.filter_by(
            trial_class_id=class_id,
            date=date,
            start_time=start_time
        ).first()

        if existing_slot:
            flash('ช่วงเวลานี้มีอยู่แล้ว', 'danger')
            return redirect(url_for('trial.manage_time_slots', class_id=class_id))

        # ตรวจสอบว่าเวลาเริ่มต้นต้องมาก่อนเวลาสิ้นสุด
        if start_time >= end_time:
            flash('เวลาเริ่มต้นต้องมาก่อนเวลาสิ้นสุด', 'danger')
            return redirect(url_for('trial.manage_time_slots', class_id=class_id))

        # สร้างช่วงเวลาใหม่
        if not max_students:
            max_students = None
        else:
            max_students = int(max_students)

        new_slot = TrialTimeSlot(
            trial_class_id=class_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            max_students=max_students
        )

        db.session.add(new_slot)
        db.session.commit()

        flash('เพิ่มช่วงเวลาเรียบร้อยแล้ว', 'success')
        return redirect(url_for('trial.manage_time_slots', class_id=class_id))

    return render_template('trial/manage_slots.html', trial_class=trial_class, time_slots=time_slots)


@trial_bp.route('/slot/<int:slot_id>/toggle', methods=['POST'])
@login_required
def toggle_slot_status(slot_id):
    """เปิด/ปิดช่วงเวลา"""
    slot = TrialTimeSlot.query.get_or_404(slot_id)
    slot.is_active = not slot.is_active
    db.session.commit()

    status = "เปิด" if slot.is_active else "ปิด"
    flash(f'ช่วงเวลาถูก{status}แล้ว', 'success')
    return redirect(url_for('trial.manage_time_slots', class_id=slot.trial_class_id))


@trial_bp.route('/slot/<int:slot_id>/delete', methods=['POST'])
@login_required
def delete_time_slot(slot_id):
    """ลบช่วงเวลา"""
    slot = TrialTimeSlot.query.get_or_404(slot_id)
    class_id = slot.trial_class_id

    # ตรวจสอบว่ามีการจองแล้วหรือไม่
    if slot.bookings:
        flash('ไม่สามารถลบช่วงเวลาได้เนื่องจากมีการจองแล้ว', 'danger')
        return redirect(url_for('trial.manage_time_slots', class_id=class_id))

    db.session.delete(slot)
    db.session.commit()

    flash('ลบช่วงเวลาเรียบร้อยแล้ว', 'success')
    return redirect(url_for('trial.manage_time_slots', class_id=class_id))


@trial_bp.route('/bookings')
@login_required
def all_bookings():
    """หน้าแสดงการจองทั้งหมด"""
    # ค้นหาตามวันที่ (ถ้ามี)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')

    query = db.session.query(TrialBooking).join(TrialTimeSlot)

    if start_date:
        query = query.filter(TrialTimeSlot.date >= start_date)

    if end_date:
        query = query.filter(TrialTimeSlot.date <= end_date)

    if status and status != 'all':
        query = query.filter(TrialBooking.status == status)

    # เรียงตามวันที่และเวลา
    bookings = query.order_by(TrialTimeSlot.date, TrialTimeSlot.start_time).all()

    return render_template('trial/all_bookings.html', bookings=bookings)


@trial_bp.route('/bookings/calendar')
@login_required
def bookings_calendar():
    """หน้าแสดงการจองในรูปแบบปฏิทิน"""
    # ดึงข้อมูลการจองทั้งหมดที่ยืนยันแล้ว
    bookings = db.session.query(TrialBooking).join(TrialTimeSlot).filter(
        TrialBooking.status == 'confirmed'
    ).order_by(TrialTimeSlot.date, TrialTimeSlot.start_time).all()

    # แปลงข้อมูลเป็นรูปแบบที่เหมาะสำหรับปฏิทิน
    events = []
    for booking in bookings:
        time_slot = booking.time_slot
        trial_class = time_slot.trial_class

        # สร้าง event สำหรับปฏิทิน
        event = {
            'id': booking.id,
            'title': f"{booking.student_nickname or booking.student_name} - {trial_class.title}",
            'start': f"{time_slot.date}T{time_slot.start_time}",
            'end': f"{time_slot.date}T{time_slot.end_time}",
            'extendedProps': {
                'booking_id': booking.id,
                'student_name': booking.student_name,
                'student_nickname': booking.student_nickname,
                'student_age': booking.student_age,
                'parent_name': booking.parent_name,
                'parent_phone': booking.parent_phone,
                'parent_email': booking.parent_email,
                'trial_class': trial_class.title,
                'status': booking.status,
                'converted': booking.converted
            }
        }
        events.append(event)

    teachers = Teacher.query.all()

    return render_template('trial/calendar.html', events=events, teachers=teachers)


@trial_bp.route('/booking/<int:booking_id>')
@login_required
def booking_detail(booking_id):
    """หน้าแสดงรายละเอียดการจอง"""
    booking = TrialBooking.query.get_or_404(booking_id)
    teachers = Teacher.query.all()

    return render_template('trial/booking_detail.html', booking=booking, teachers=teachers)


@trial_bp.route('/booking/<int:booking_id>/update', methods=['POST'])
@login_required
def update_booking(booking_id):
    """อัปเดตข้อมูลการจอง"""
    booking = TrialBooking.query.get_or_404(booking_id)

    # อัปเดตสถานะ
    status = request.form.get('status')
    if status and status in ['pending', 'confirmed', 'canceled', 'completed', 'no_show']:
        booking.status = status

    # อัปเดตครูผู้สอน
    teacher_id = request.form.get('teacher_id')
    if teacher_id:
        booking.teacher_id = teacher_id if teacher_id != 'none' else None

    # อัปเดตข้อมูลทั่วไป
    booking.student_name = request.form.get('student_name', booking.student_name)
    booking.student_nickname = request.form.get('student_nickname', booking.student_nickname)
    booking.student_age = request.form.get('student_age', booking.student_age)
    booking.student_school = request.form.get('student_school', booking.student_school)
    booking.student_grade = request.form.get('student_grade', booking.student_grade)
    booking.parent_name = request.form.get('parent_name', booking.parent_name)
    booking.parent_phone = request.form.get('parent_phone', booking.parent_phone)
    booking.parent_email = request.form.get('parent_email', booking.parent_email)
    booking.parent_line_id = request.form.get('parent_line_id', booking.parent_line_id)
    booking.special_request = request.form.get('special_request', booking.special_request)

    db.session.commit()

    flash('อัปเดตข้อมูลการจองเรียบร้อยแล้ว', 'success')
    return redirect(url_for('trial.booking_detail', booking_id=booking_id))


@trial_bp.route('/booking/<int:booking_id>/convert', methods=['GET', 'POST'])
@login_required
def convert_to_student(booking_id):
    """แปลงการจองเป็นนักเรียนจริง"""
    booking = TrialBooking.query.get_or_404(booking_id)

    if request.method == 'POST':
        # แปลงเป็นนักเรียนและสร้างนักเรียนใหม่
        name = request.form.get('name', booking.student_name)
        nickname = request.form.get('nickname', booking.student_nickname)
        school_name = request.form.get('school_name', booking.student_school)
        school_level = request.form.get('school_level', booking.student_grade)
        student_age = request.form.get('student_age', booking.student_age)

        # สร้างนักเรียนใหม่
        new_student = Student(
            name=name,
            nickname=nickname,
            school_name=school_name,
            school_level=school_level,
            phone=booking.parent_phone,
            email=booking.parent_email
        )

        db.session.add(new_student)
        db.session.flush()  # เพื่อให้ได้ ID ของนักเรียนใหม่

        # อัปเดตข้อมูลการจอง
        booking.converted = True
        booking.converted_student_id = new_student.id
        booking.converted_at = datetime.now()

        db.session.commit()

        flash('แปลงเป็นนักเรียนเรียบร้อยแล้ว', 'success')

        # ไปที่หน้าลงทะเบียนเรียน
        return redirect(url_for('enroll.enroll_form', student_id=new_student.id))

    return render_template('trial/convert_to_student.html', booking=booking)


@trial_bp.route('/export', methods=['GET'])
@login_required
def export_bookings():
    """ส่งออกข้อมูลการจองเป็น CSV/Excel"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status', 'all')
    export_format = request.args.get('format', 'csv')

    # สร้างคิวรี
    query = db.session.query(TrialBooking).join(TrialTimeSlot).join(TrialClass)

    if start_date:
        query = query.filter(TrialTimeSlot.date >= start_date)

    if end_date:
        query = query.filter(TrialTimeSlot.date <= end_date)

    if status != 'all':
        query = query.filter(TrialBooking.status == status)

    # เรียงตามวันที่และเวลา
    bookings = query.order_by(TrialTimeSlot.date, TrialTimeSlot.start_time).all()

    # สร้างข้อมูลสำหรับส่งออก
    data = []
    for booking in bookings:
        time_slot = booking.time_slot
        trial_class = time_slot.trial_class

        data.append({
            'วันที่': time_slot.date.strftime('%d/%m/%Y'),
            'เวลา': f"{time_slot.start_time} - {time_slot.end_time}",
            'คลาส': trial_class.title,
            'ชื่อนักเรียน': booking.student_name,
            'ชื่อเล่น': booking.student_nickname,
            'อายุ': booking.student_age,
            'โรงเรียน': booking.student_school,
            'ระดับชั้น': booking.student_grade,
            'ชื่อผู้ปกครอง': booking.parent_name,
            'เบอร์โทร': booking.parent_phone,
            'อีเมล': booking.parent_email,
            'ไลน์ไอดี': booking.parent_line_id,
            'คำขอพิเศษ': booking.special_request,
            'สถานะ': booking.status,
            'แหล่งที่มา': booking.source,
            'สมัครเรียน': 'ใช่' if booking.converted else 'ไม่',
            'เวลาที่จอง': booking.created_at.strftime('%d/%m/%Y %H:%M')
        })

    # สร้างไฟล์ส่งออก
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys() if data else [])
        writer.writeheader()
        writer.writerows(data)

        # สร้าง Response
        return current_app.response_class(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=bookings.csv'}
        )
    elif export_format == 'excel':
        # ใช้ pandas สร้าง Excel
        df = pd.DataFrame(data)
        output = io.BytesIO()

        # สร้าง Excel Writer
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Bookings', index=False)

            # อัพเดต column widths
            worksheet = writer.sheets['Bookings']
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).map(len).max(), len(col) + 2)
                worksheet.set_column(i, i, column_len)

        output.seek(0)

        # สร้าง Response
        return current_app.response_class(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment;filename=bookings.xlsx'}
        )
    else:
        return jsonify({'error': 'รูปแบบไฟล์ไม่ถูกต้อง'}), 400


# -----------------------------------
# API สำหรับหน้าจองสำหรับผู้ใช้ทั่วไป
# -----------------------------------

@trial_bp.route('/api/classes', methods=['GET'])
def api_get_classes():
    """API เรียกดูรายการคลาสทดลอง"""
    trial_classes = TrialClass.query.all()
    result = [cls.to_dict() for cls in trial_classes]
    return jsonify(result)


@trial_bp.route('/api/slots', methods=['GET'])
def api_get_slots():
    """API เรียกดูช่วงเวลาว่าง"""
    class_id = request.args.get('class_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # สร้างคิวรี
    query = TrialTimeSlot.query.filter(TrialTimeSlot.is_active == True)

    if class_id:
        query = query.filter(TrialTimeSlot.trial_class_id == class_id)

    if start_date:
        query = query.filter(TrialTimeSlot.date >= start_date)

    if end_date:
        query = query.filter(TrialTimeSlot.date <= end_date)

    # ดึงข้อมูลช่วงเวลาที่ว่าง
    time_slots = query.order_by(TrialTimeSlot.date, TrialTimeSlot.start_time).all()

    result = [slot.to_dict() for slot in time_slots]
    return jsonify(result)


@trial_bp.route('/api/book', methods=['POST'])
def api_book_slot():
    """API สำหรับจองคลาสทดลอง"""
    data = request.get_json()

    # ตรวจสอบข้อมูลที่จำเป็น
    required_fields = ['time_slot_id', 'student_name', 'parent_name', 'parent_phone']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'กรุณากรอกข้อมูล {field}'}), 400

    # ตรวจสอบว่าช่วงเวลายังว่างอยู่หรือไม่
    time_slot = TrialTimeSlot.query.get(data['time_slot_id'])
    if not time_slot:
        return jsonify({'error': 'ไม่พบช่วงเวลาที่เลือก'}), 404

    if not time_slot.is_active:
        return jsonify({'error': 'ช่วงเวลานี้ปิดรับจองแล้ว'}), 400

    if time_slot.is_full:
        return jsonify({'error': 'ช่วงเวลานี้เต็มแล้ว'}), 400

    # สร้างข้อมูลการจอง
    booking = TrialBooking(
        time_slot_id=data['time_slot_id'],
        student_name=data['student_name'],
        student_nickname=data.get('student_nickname', ''),
        student_age=data.get('student_age'),
        student_school=data.get('student_school', ''),
        student_grade=data.get('student_grade', ''),
        parent_name=data['parent_name'],
        parent_phone=data['parent_phone'],
        parent_email=data.get('parent_email', ''),
        parent_line_id=data.get('parent_line_id', ''),
        special_request=data.get('special_request', ''),
        source=data.get('source', 'website')
    )

    db.session.add(booking)
    db.session.commit()

    # ส่งคืนข้อมูลการจอง
    return jsonify({
        'success': True,
        'booking_id': booking.id,
        'message': 'จองเรียบร้อยแล้ว'
    })


@trial_bp.route('/api/booking/<int:booking_id>', methods=['GET'])
def api_get_booking(booking_id):
    """API เรียกดูข้อมูลการจอง"""
    booking = TrialBooking.query.get_or_404(booking_id)
    return jsonify(booking.to_dict())


# -----------------------------------
# หน้าสำหรับผู้ใช้ทั่วไป (Public Pages)
# -----------------------------------

@trial_bp.route('/public', methods=['GET'])
def public_classes():
    """หน้าแสดงคลาสทดลองเรียนสำหรับผู้ใช้ทั่วไป"""
    trial_classes = TrialClass.query.all()

    # ดึงข้อมูลช่วงเวลาในอนาคตที่รับจองได้
    today = datetime.now().date()

    # ดึงช่วงเวลาที่ยังเปิดรับจองและยังไม่เต็ม
    available_slots = db.session.query(TrialTimeSlot).filter(
        TrialTimeSlot.date >= today,
        TrialTimeSlot.is_active == True
    ).all()

    # จัดกลุ่มช่วงเวลาตามคลาส
    slots_by_class = {}
    for slot in available_slots:
        if slot.trial_class_id not in slots_by_class:
            slots_by_class[slot.trial_class_id] = []

        # เพิ่มเฉพาะช่วงเวลาที่ยังไม่เต็ม
        if not slot.is_full:
            slots_by_class[slot.trial_class_id].append(slot)

    return render_template(
        'trial/public/classes.html',
        trial_classes=trial_classes,
        slots_by_class=slots_by_class
    )


@trial_bp.route('/public/<int:class_id>/book', methods=['GET', 'POST'])
def public_book_class(class_id):
    """หน้าจองคลาสทดลองเรียนสำหรับผู้ใช้ทั่วไป"""
    trial_class = TrialClass.query.get_or_404(class_id)

    # ดึงช่วงเวลาที่ยังเปิดรับจองและยังไม่เต็ม
    today = datetime.now().date()
    available_slots = TrialTimeSlot.query.filter(
        TrialTimeSlot.trial_class_id == class_id,
        TrialTimeSlot.date >= today,
        TrialTimeSlot.is_active == True
    ).order_by(TrialTimeSlot.date, TrialTimeSlot.start_time).all()

    # กรองเฉพาะช่วงเวลาที่ยังไม่เต็ม
    available_slots = [slot for slot in available_slots if not slot.is_full]

    if request.method == 'POST':
        # ตรวจสอบข้อมูลที่จำเป็น
        time_slot_id = request.form.get('time_slot_id')
        student_name = request.form.get('student_name')
        parent_name = request.form.get('parent_name')
        parent_phone = request.form.get('parent_phone')

        if not all([time_slot_id, student_name, parent_name, parent_phone]):
            flash('กรุณากรอกข้อมูลให้ครบถ้วน', 'danger')
            return redirect(url_for('trial.public_book_class', class_id=class_id))

        # ตรวจสอบว่าช่วงเวลายังว่างอยู่หรือไม่
        time_slot = TrialTimeSlot.query.get(time_slot_id)
        if not time_slot or time_slot.trial_class_id != class_id:
            flash('ไม่พบช่วงเวลาที่เลือก', 'danger')
            return redirect(url_for('trial.public_book_class', class_id=class_id))

        if not time_slot.is_active:
            flash('ช่วงเวลานี้ปิดรับจองแล้ว', 'danger')
            return redirect(url_for('trial.public_book_class', class_id=class_id))

        if time_slot.is_full:
            flash('ช่วงเวลานี้เต็มแล้ว', 'danger')
            return redirect(url_for('trial.public_book_class', class_id=class_id))

        # สร้างข้อมูลการจอง
        booking = TrialBooking(
            time_slot_id=time_slot_id,
            student_name=student_name,
            student_nickname=request.form.get('student_nickname', ''),
            student_age=request.form.get('student_age'),
            student_school=request.form.get('student_school', ''),
            student_grade=request.form.get('student_grade', ''),
            parent_name=parent_name,
            parent_phone=parent_phone,
            parent_email=request.form.get('parent_email', ''),
            parent_line_id=request.form.get('parent_line_id', ''),
            special_request=request.form.get('special_request', ''),
            source=request.form.get('source', 'website')
        )

        db.session.add(booking)
        db.session.commit()

        # ไปที่หน้ายืนยันการจอง
        return redirect(url_for('trial.public_booking_confirmation', booking_id=booking.id))

    return render_template(
        'trial/public/book.html',
        trial_class=trial_class,
        available_slots=available_slots
    )


@trial_bp.route('/public/confirmation/<int:booking_id>')
def public_booking_confirmation(booking_id):
    """หน้ายืนยันการจองสำเร็จ"""
    booking = TrialBooking.query.get_or_404(booking_id)
    return render_template('trial/public/confirmation.html', booking=booking)


@trial_bp.route('/public/verify/<int:booking_id>/<phone_suffix>')
def public_verify_booking(booking_id, phone_suffix):
    """หน้าตรวจสอบสถานะการจอง (สำหรับลิงก์ที่ส่งให้ผู้ปกครอง)"""
    booking = TrialBooking.query.get_or_404(booking_id)

    # ตรวจสอบรหัสยืนยัน (ใช้เบอร์โทร 4 ตัวท้ายเป็นรหัสยืนยัน)
    if phone_suffix != booking.parent_phone[-4:]:
        flash('รหัสยืนยันไม่ถูกต้อง', 'danger')
        return redirect(url_for('trial.public_classes'))

    return render_template('trial/public/verify.html', booking=booking)