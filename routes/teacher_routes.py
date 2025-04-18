from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import Teacher, TeacherUnavailableTime, TeacherAssignment, Class
from db import db
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


@teacher_bp.route('/')
def index():
    teachers = Teacher.query.all()
    return render_template('teacher/index.html', teachers=teachers)


@teacher_bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        specialties = ','.join(request.form.getlist('specialties'))
        max_hours = request.form['max_hours_per_week']

        teacher = Teacher(
            name=name,
            email=email,
            phone=phone,
            specialties=specialties,
            max_hours_per_week=max_hours
        )

        # จัดการรูปภาพที่อัปโหลด
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"teacher_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"

                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                image = Image.open(file)
                image.thumbnail((400, 400))
                image.save(file_path)
                teacher.image_filename = unique_filename

        db.session.add(teacher)
        db.session.commit()
        flash('เพิ่มข้อมูลครูเรียบร้อยแล้ว', 'success')
        return redirect(url_for('teacher.index'))

    return render_template('teacher/add.html')


@teacher_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    teacher = Teacher.query.get_or_404(id)

    if request.method == 'POST':
        teacher.name = request.form['name']
        teacher.email = request.form['email']
        teacher.phone = request.form['phone']
        teacher.specialties = ','.join(request.form.getlist('specialties'))
        teacher.max_hours_per_week = request.form['max_hours_per_week']
        print("โพสต์เข้ามาแล้ว")

        # จัดการรูปภาพที่อัปโหลด
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # ลบรูปเก่าถ้ามี
                if teacher.image_filename:
                    old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], teacher.image_filename)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

                # บันทึกรูปใหม่
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"teacher_{teacher.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"

                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                image = Image.open(file)
                image.thumbnail((400, 400))
                image.save(file_path)
                teacher.image_filename = unique_filename

        db.session.commit()
        flash('แก้ไขข้อมูลครูเรียบร้อยแล้ว', 'success')
        return redirect(url_for('teacher.index'))

    return render_template('teacher/edit.html', teacher=teacher)


@teacher_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    teacher = Teacher.query.get_or_404(id)

    # ลบรูปภาพที่เก็บไว้
    if teacher.image_filename:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], teacher.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(teacher)
    db.session.commit()
    flash('ลบข้อมูลครูเรียบร้อยแล้ว', 'success')
    return redirect(url_for('teacher.index'))


@teacher_bp.route('/delete-image/<int:id>', methods=['POST'])
def delete_image(id):
    teacher = Teacher.query.get_or_404(id)

    if teacher.image_filename:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], teacher.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        teacher.image_filename = None
        db.session.commit()
        flash('ลบรูปภาพครูเรียบร้อยแล้ว', 'success')

    return redirect(url_for('teacher.edit', id=id))


@teacher_bp.route('/view/<int:id>')
def view(id):
    teacher = Teacher.query.get_or_404(id)

    # ดึงข้อมูลคลาสที่ครูคนนี้สอน
    teacher_classes = db.session.query(
        Class.name.label('class_name'),
        Class.days,
        Class.start_time,
        Class.end_time
    ).join(
        TeacherAssignment, TeacherAssignment.class_id == Class.id
    ).filter(
        TeacherAssignment.teacher_id == id
    ).all()

    return render_template('teacher/view.html', teacher=teacher, teacher_classes=teacher_classes)


@teacher_bp.route('/unavailable-time/<int:id>', methods=['GET', 'POST'])
def unavailable_time(id):
    teacher = Teacher.query.get_or_404(id)

    if request.method == 'POST':
        day_of_week = request.form['day_of_week']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        unavailable_time = TeacherUnavailableTime(
            teacher_id=id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time
        )

        db.session.add(unavailable_time)
        db.session.commit()
        flash('เพิ่มเวลาที่ครูไม่ว่างเรียบร้อยแล้ว', 'success')
        return redirect(url_for('teacher.unavailable_time', id=id))

    unavailable_times = TeacherUnavailableTime.query.filter_by(teacher_id=id).all()
    return render_template('teacher/unavailable_time.html', teacher=teacher, unavailable_times=unavailable_times)


@teacher_bp.route('/delete-unavailable-time/<int:id>', methods=['POST'])
def delete_unavailable_time(id):
    unavailable_time = TeacherUnavailableTime.query.get_or_404(id)
    teacher_id = unavailable_time.teacher_id

    db.session.delete(unavailable_time)
    db.session.commit()
    flash('ลบเวลาที่ครูไม่ว่างเรียบร้อยแล้ว', 'success')
    return redirect(url_for('teacher.unavailable_time', id=teacher_id))