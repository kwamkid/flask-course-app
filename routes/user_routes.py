from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, User
from datetime import datetime
from werkzeug.security import generate_password_hash


user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/')
def user_list():
    users = User.query.all()
    return render_template('user/list.html', users=users)

@user_bp.route('/add', methods=['GET', 'POST'])
def user_add():
    if request.method == 'POST':
        new_user = User(
            username=request.form['username'],
            name=request.form['name'],
            email=request.form['email'],
            password_hash=request.form['password'],
        )
        db.session.add(new_user)
        db.session.commit()
        flash('เพิ่มผู้ใช้เรียบร้อยแล้ว', 'success')
        return redirect(url_for('user.user_list'))
    return render_template('user/form.html', user=None)

@user_bp.route('/edit/<int:user_id>', methods=['GET', 'POST'], endpoint='user_edit')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form['username']
        user.name = request.form['name']
        user.email = request.form['email']

        new_password = request.form['password']
        if new_password:
            user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash('แก้ไขข้อมูลผู้ใช้เรียบร้อยแล้ว', 'success')
        return redirect(url_for('user.user_list'))  # ✅ ต้องมี return เสมอ

    return render_template('user/form.html', user=user)

@user_bp.route('/delete/<int:user_id>', methods=['POST'])
def user_delete(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('ลบผู้ใช้แล้ว', 'info')
    return redirect(url_for('user.user_list'))