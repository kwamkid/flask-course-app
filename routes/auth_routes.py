from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from datetime import datetime
from flask_login import login_user
from flask_login import logout_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(username + password)
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)  # ✅ ใช้ Flask-Login
            flash('เข้าสู่ระบบสำเร็จ', 'success')
            return redirect(url_for('index'))
        else:
            flash('Username or password ไม่ถูกต้อง', 'danger')

    return render_template('forms/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('รหัสผ่านไม่ตรงกัน', 'danger')
            return redirect(url_for('auth.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('มีผู้ใช้งานอีเมลนี้แล้ว', 'warning')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, name=username, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('สมัครสมาชิกสำเร็จ กรุณาเข้าสู่ระบบ', 'success')
        return redirect(url_for('auth.login'))

    return render_template('forms/register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()  # ✅ ใช้ Flask-Login
    flash('ออกจากระบบแล้ว', 'info')
    return redirect(url_for('auth.login'))