from flask import Blueprint, render_template, request, redirect, flash
from models import Student, Class, Enrollment, Course, db

student_bp = Blueprint('student', __name__)

@student_bp.route('/student', methods=['GET'])
def student_list():
    student_list = Student.query.all()
    return render_template('student/list.html', students=student_list)

@student_bp.route('/student/add', methods=['GET', 'POST'])
def student_add():
    if request.method == 'POST':
        student = Student(
            name=request.form['name'],
            nickname=request.form.get('nickname'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            birthday=request.form.get('birthday'),
            gender=request.form.get('gender'),
            school_name=request.form.get('school_name'),
            school_type = request.form.get('school_type'),
            school_level=request.form.get('school_level'),
            health_condition=request.form.get('health_condition'),
            health_detail=request.form.get('health_detail'),
            allow_photo=request.form.get('allow_photo') == 'on',
            allow_paracetamol=request.form.get('allow_paracetamol') == 'on'
        )
        db.session.add(student)
        db.session.commit()
        return redirect('/student')
    return render_template('student/add.html', student=None)

@student_bp.route('/student/<int:student_id>')
def student_view(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('student/view.html', student=student)

@student_bp.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
def student_edit(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form['name']
        student.nickname = request.form.get('nickname')
        student.phone = request.form.get('phone')
        student.email = request.form.get('email')
        student.birthday = request.form.get('birthday')
        student.gender = request.form.get('gender')
        student.school_name = request.form.get('school_name')
        student.school_type = request.form.get('school_type')
        student.school_level = request.form.get('school_level')
        student.health_condition = request.form.get('health_condition')
        student.health_detail = request.form.get('health_detail')
        student.allow_photo = request.form.get('allow_photo') == 'on'
        student.allow_paracetamol = request.form.get('allow_paracetamol') == 'on'

        db.session.commit()
        flash("✅ แก้ไขข้อมูลนักเรียนเรียบร้อยแล้ว!", "success")
        return redirect('/student')
    return render_template('student/edit.html', student=student)

@student_bp.route('/student/<int:id>/delete', methods=['POST'])
def student_delete(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('ลบนักเรียนเรียบร้อยแล้ว', 'success')
    return redirect('/student')
