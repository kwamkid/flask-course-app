

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
            school=request.form.get('school'),
            grade=request.form.get('grade'),
            birthday=request.form.get('birthday'),
            allergy=request.form.get('allergy'),
            health=request.form.get('health'),
            phone=request.form.get('phone'),
            emergency_name1=request.form.get('emergency_name1'),
            emergency_phone1=request.form.get('emergency_phone1'),
            emergency_name2=request.form.get('emergency_name2'),
            emergency_phone2=request.form.get('emergency_phone2')
        )
        db.session.add(student)
        db.session.commit()
        return redirect('/student')
    return render_template('student/add.html')

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
        student.school = request.form.get('school')
        student.grade = request.form.get('grade')
        student.birthday = request.form.get('birthday')
        student.allergy = request.form.get('allergy')
        student.health = request.form.get('health')
        student.phone = request.form.get('phone')
        student.emergency_name1 = request.form.get('emergency_name1')
        student.emergency_phone1 = request.form.get('emergency_phone1')
        student.emergency_name2 = request.form.get('emergency_name2')
        student.emergency_phone2 = request.form.get('emergency_phone2')

        db.session.commit()
        flash("✅ แก้ไขข้อมูลนักเรียนเรียบร้อยแล้ว!")
        return redirect('/student')
    return render_template('student/edit.html', student=student)

@student_bp.route('/student/<int:id>/delete', methods=['POST'])
def student_delete(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('ลบนักเรียนเรียบร้อยแล้ว', 'success')
    return redirect('/student')
