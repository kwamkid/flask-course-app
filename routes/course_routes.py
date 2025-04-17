from flask import Blueprint, request, redirect, render_template, flash, url_for
from models import db,Course

course_bp = Blueprint('course', __name__)

@course_bp.route('/course', methods=['GET'])
def course_list():
    courses = Course.query.all()
    return render_template('course/list.html', courses=courses)

@course_bp.route('/course/add', methods=['GET', 'POST'])
def course_add():
    if request.method == 'POST':
        course = Course(
            title=request.form['title'],
            color=request.form.get('color', '#3788d8')
        )
        db.session.add(course)
        db.session.commit()
        return redirect('/course')
    return render_template(
        "course/add.html",
        form_title="เพิ่มคอร์สเรียน",
        form_action=url_for("course.course_add"),
        course=None,
        submit_label="บันทึกข้อมูล"
    )

@course_bp.route('/course/<int:id>/edit', methods=['GET', 'POST'])
def course_edit(id):
    course = Course.query.get_or_404(id)
    if request.method == 'POST':
        course.title = request.form['title']
        course.color = request.form['color']
        db.session.commit()
        flash("✅ แก้ไขวิชาเรียบร้อยแล้ว!")
        return redirect('/course')
    return render_template('course/edit.html', course=course)

@course_bp.route('/course/<int:id>/delete', methods=['POST'])
def course_delete(id):
    course = Course.query.get_or_404(id)
    db.session.delete(course)
    db.session.commit()
    flash("🗑️ ลบวิชาเรียบร้อยแล้ว!")
    return redirect('/course')

