from flask import Flask, render_template, request, redirect , url_for
from datetime import datetime, timedelta
from db import db  # ✅ ใช้ db จากไฟล์ใหม่
from models import Course, Class, ClassSchedule, Holiday, User
from flask import flash
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from routes.course_routes import course_bp
from routes.class_routes import class_bp
from routes.student_routes import student_bp
from routes.enroll_routes import enroll_bp  # ✅ เพิ่ม
from routes.class_routes import generate_class_dates
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp

import os

# หลังจาก init_app แล้ว

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True  # ← ต้องมี
app.config['DEBUG'] = True

app.secret_key = 'uK&2t#fYxP7$eNp!qA1z'  # ✅ ตั้งค่าลับอะไรก็ได้
# แทนบรรทัดนี้:
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')

# ใช้แบบนี้แทน:
if os.getenv("RENDER") == "true":
    # ใช้ DATABASE_URL จาก Render
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
else:
    # ใช้ SQLite สำหรับ local
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



app.register_blueprint(course_bp)
app.register_blueprint(class_bp)
app.register_blueprint(student_bp)
app.register_blueprint(enroll_bp)  # ✅ เพิ่ม
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # ชื่อ route login ของคุณ
login_manager.login_message_category = 'info'
@app.before_request
def require_login():
    # ถ้า user ยังไม่ login และไม่ใช่ route ยกเว้น
    if not current_user.is_authenticated and not request.endpoint in ['auth.login', 'auth.register', 'static']:
        return redirect(url_for('auth.login'))


db.init_app(app)  # ✅ บอกให้ db ใช้ app นี้
migrate = Migrate(app, db)

# สร้างตาราง (รันครั้งแรกเท่านั้น)
with app.app_context():
    db.create_all()
# (ตามด้วย model และ routes ต่าง ๆ)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_weekday_index(day_name):
    days = ['จันทร์', 'อังคาร', 'พุธ', 'พฤหัสบดี', 'ศุกร์', 'เสาร์', 'อาทิตย์']
    return days.index(day_name)


def todatetime(value, format='%Y-%m-%d'):
    return datetime.strptime(value, format)

def now():
    return datetime.utcnow()

app.jinja_env.filters['todatetime'] = todatetime
app.jinja_env.globals['now'] = now

app.jinja_env.filters['todatetime'] = todatetime

@app.template_filter('format_date')
def format_date(value):
    if isinstance(value, datetime):
        return value.strftime('%d/%m/%Y')
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        return value

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/holiday', methods=['GET', 'POST'])
def holiday():
    if request.method == 'POST':
        holiday_date = request.form['holiday_date']
        db.session.add(Holiday(date=holiday_date))
        db.session.commit()
    holidays = Holiday.query.order_by(Holiday.date).all()
    return render_template('holiday.html', holidays=holidays)


@app.route('/add-holiday', methods=['GET', 'POST'])
def add_holiday():
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        note = request.form.get('note')
        print(start_date_str)
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            print("Start:", start_date)

            if not end_date_str:
                end_date = start_date
            else:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            print("End:", end_date)

            if start_date > end_date:
                flash('วันที่เริ่มต้นต้องไม่น้อยกว่าวันที่สิ้นสุด', 'danger')
                return redirect(url_for('holiday'))

            added_count = 0
            current_date = start_date
            while current_date <= end_date:
                existing = Holiday.query.filter_by(date=current_date).first()
                if not existing:
                    db.session.add(Holiday(date=current_date, note=note))
                    added_count += 1
                current_date += timedelta(days=1)

            db.session.commit()

            if added_count > 0:
                flash(f'เพิ่มวันหยุดจำนวน {added_count} วันเรียบร้อยแล้ว', 'success')
            else:
                flash('วันหยุดที่เลือกมีอยู่แล้วทั้งหมด', 'warning')
        except ValueError:
            flash('รูปแบบวันที่ไม่ถูกต้อง', 'danger')

        return redirect(url_for('holiday'))

    holidays = Holiday.query.order_by(Holiday.date).all()
    return render_template('holiday.html', holidays=holidays)

@app.route('/subject-class', methods=['GET'])
def subject_class():
    courses = Course.query.all()
    return render_template('subject_class.html', courses=courses)

@app.route('/calendar')
def calendar():
    events = []
    classes = Class.query.all()
    for cls in classes:
        course = db.session.get(Course, cls.course_id)  # ✅ แก้ตรงนี้
        color = course.color if course else '#3788d8'
        for sched in cls.schedules:
            events.append({
                'title': cls.name,
                'start': f"{sched.date}T{cls.start_time}",
                'end': f"{sched.date}T{cls.end_time}",
                'color': color,
                'extendedProps': {
                    'description': f"{cls.name}<br>{cls.start_time} - {cls.end_time}"
                }
            })

    holidays = Holiday.query.order_by(Holiday.date).all()
    for h in holidays:
        event = {
            'title': 'Holiday',
            'start': h.date,
            'color': '#cccccc',
            'textColor': '#000000'
        }
        if hasattr(h, 'note') and h.note:
            event['title'] = f"Holiday: {h.note}"
        events.append(event)

    return render_template('calendar.html', events=events)


@app.route('/regenerate-class-schedules', methods=['POST'])
def regenerate_class_schedules():
    db.session.query(ClassSchedule).delete()
    all_classes = Class.query.all()
    holiday_dates = [h.date for h in Holiday.query.all()]
    for cls in all_classes:
        days = list(map(int, cls.days.split(',')))
        schedule_dates = generate_class_dates(cls.start_date, days, cls.total_sessions, holiday_dates)
        for date in schedule_dates:
            db.session.add(ClassSchedule(class_id=cls.id, date=date))
    db.session.commit()
    flash('อัพเดทตารางเรียนใหม่ทั้งหมด โดยอ้างอิงจากวันหยุดเรียบร้อยแล้ว', 'success')
    return redirect(url_for('holiday'))

@app.route('/delete-holiday/<int:holiday_id>', methods=['POST'])
def delete_holiday(holiday_id):
    holiday = Holiday.query.get_or_404(holiday_id)
    db.session.delete(holiday)
    db.session.commit()
    flash('ลบวันหยุดเรียบร้อยแล้ว', 'success')
    return redirect(url_for('holiday'))

@app.context_processor
def inject_labels():
    return {
        "BUTTON_LABELS": {
            "view_btn": "ดูข้อมูล",
            "edit_btn": "แก้ไขข้อมูล",
            "delete_btn": "ลบข้อมูล",
            "back_btn": "กลับ",
            "update_btn": "อัพเดทข้อมูล",
            "ok_btn": "บันทึกข้อมูล",
            "cancel_btn": "ยกเลิก",
        }
    }

if __name__ == '__main__':
    app.run(debug=True)