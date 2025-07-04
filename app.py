from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from forms import RegistrationForm, LoginForm, LeaveRequestForm
from datetime import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/employee_db'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), default='employee')

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), nullable=False)

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.String(10), nullable=False)
    end_date = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='Pending')

class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    pay_date = db.Column(db.String(10), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, password=form.password.data).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    attendance_records = Attendance.query.filter_by(user_id=current_user.id).all()
    leave_requests = LeaveRequest.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', attendance=attendance_records, leaves=leave_requests)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    status = request.form['status']
    new_attendance = Attendance(
        user_id=current_user.id,
        date=datetime.today().strftime('%Y-%m-%d'),
        status=status
    )
    db.session.add(new_attendance)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/leave_request', methods=['GET', 'POST'])
@login_required
def leave_request():
    form = LeaveRequestForm()
    if form.validate_on_submit():
        leave = LeaveRequest(
            user_id=current_user.id,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        db.session.add(leave)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('leave_request.html', form=form)

@app.route('/payroll', methods=['GET'])
@login_required
def payroll():
    payroll_records = Payroll.query.filter_by(user_id=current_user.id).all()
    return render_template('payroll.html', payroll=payroll_records)

@app.route('/staff_management')
@login_required
def staff_management():
    if current_user.role != 'admin':
        flash('Access denied!')
        return redirect(url_for('dashboard'))
    staff = User.query.all()
    return render_template('staff_management.html', staff=staff)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
