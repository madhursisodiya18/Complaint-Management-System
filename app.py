from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup
from datetime import datetime
from sqlalchemy import case, text
import os
import secrets
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mit-aoe-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///complaints.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# CSRF token helper
@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get('_csrf_token', None)
        form_token = request.form.get('_csrf_token')
        if not token or token != form_token:
            return "CSRF token missing or incorrect!", 400

def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(16)
    return Markup(f'<input type="hidden" name="_csrf_token" value="{session["_csrf_token"]}">')

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')  # student or admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    complaints = db.relationship('Complaint', backref='user', lazy=True)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # teacher, student, staff, facility
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    admin_response = db.Column(db.Text, nullable=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    notification_type = db.Column(db.String(50), default='complaint_update')  # complaint_update, system, admin_message
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaint.id'), nullable=True)  # Link to related complaint
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to complaint
    complaint = db.relationship('Complaint', backref='notifications')

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, resolved
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        # Only allow @mitaoe.ac.in emails
        if not email.lower().endswith('@mitaoe.ac.in'):
            flash('Only @mitaoe.ac.in email addresses are allowed for student registration.', 'error')
            return redirect(url_for('register'))
        if email.lower().endswith('@gmail.com'):
            flash('Gmail addresses are not allowed. Please use your @mitaoe.ac.in email.', 'error')
            return redirect(url_for('register'))
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        
        # Create new user (only students)
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password, role='student')
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first!', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    session_key = f'complaint_deleted_{user.id}'
    if session.get(session_key):
        flash(session[session_key], 'warning')
        session.pop(session_key)
    # Filtering logic
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')
    if user.role == 'admin':
        complaints_query = Complaint.query
    else:
        complaints_query = Complaint.query.filter_by(user_id=user.id)
    if status and status != 'all':
        complaints_query = complaints_query.filter_by(status=status)
    if q:
        if q.isdigit():
            complaints_query = complaints_query.filter(Complaint.id == int(q))
        else:
            complaints_query = complaints_query.filter(Complaint.subject.ilike(f'%{q}%'))
    complaints = complaints_query.order_by(Complaint.created_at.desc()).all()
    return render_template('dashboard.html', user=user, complaints=complaints)

@app.route('/submit_complaint', methods=['GET', 'POST'])
def submit_complaint():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        category = request.form['category']
        subject = request.form['subject']
        description = request.form['description']
        new_complaint = Complaint(
            user_id=session['user_id'],
            category=category,
            subject=subject,
            description=description
        )
        db.session.add(new_complaint)
        db.session.commit()
        notif = Notification(
            user_id=session['user_id'],
            message=f'Your complaint #{new_complaint.id} has been submitted successfully and is under review.',
            notification_type='complaint_update',
            priority='normal',
            complaint_id=new_complaint.id
        )
        db.session.add(notif)
        db.session.commit()
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('submit_complaint.html')

@app.route('/view_complaint/<int:complaint_id>')
def view_complaint(complaint_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    complaint = Complaint.query.get_or_404(complaint_id)
    if user.role != 'admin' and complaint.user_id != user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard'))
    return render_template('view_complaint.html', complaint=complaint, user=user)

@app.route('/update_complaint/<int:complaint_id>', methods=['POST'])
def update_complaint(complaint_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    if user.role != 'admin':
        flash('Access denied! Only administrators can update complaints.', 'error')
        return redirect(url_for('dashboard'))
    try:
        complaint = Complaint.query.get_or_404(complaint_id)
        status = request.form.get('status', 'pending')
        admin_response = request.form.get('admin_response', '')
        old_status = complaint.status
        complaint.status = status
        complaint.admin_response = admin_response
        if status == 'resolved':
            complaint.resolved_at = datetime.utcnow()
        db.session.commit()
        if complaint.user_id != user.id and status != old_status:
            notif_msg = None
            priority = 'normal'
            if status == 'in_progress':
                notif_msg = f'Your complaint #{complaint.id} is now in progress.'
                priority = 'high'
            elif status == 'resolved':
                notif_msg = f'Your complaint #{complaint.id} has been resolved.'
                priority = 'high'
            if notif_msg:
                notif = Notification(
                    user_id=complaint.user_id, 
                    message=notif_msg,
                    notification_type='complaint_update',
                    priority=priority,
                    complaint_id=complaint.id
                )
                db.session.add(notif)
                db.session.commit()
        flash('Complaint updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating complaint: {str(e)}', 'error')
    return redirect(url_for('view_complaint', complaint_id=complaint_id))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        if not name or not email or not message:
            flash('Please fill out all fields.', 'error')
            return redirect(url_for('contact'))
        try:
            cm = ContactMessage(name=name, email=email, message=message)
            if 'user_id' in session:
                cm.user_id = session['user_id']
            db.session.add(cm)
            db.session.commit()
            flash('Thank you for reaching out. Your message has been sent to the admin.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error saving your message: {str(e)}', 'error')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/admin/messages')
def admin_messages():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    if user.role != 'admin':
        flash('Access denied! Only administrators can view messages.', 'error')
        return redirect(url_for('dashboard'))
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')
    query = ContactMessage.query
    if status == 'resolved':
        query = query.filter((ContactMessage.status == 'resolved') | (ContactMessage.is_resolved == True))
    elif status == 'unresolved':
        query = query.filter((ContactMessage.status != 'resolved') & (ContactMessage.is_resolved == False))
    if q:
        query = query.filter(ContactMessage.message.ilike(f'%{q}%'))
    messages = query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin_messages.html', messages=messages)

@app.route('/admin/messages/<int:message_id>')
def admin_message_view(message_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or user.role != 'admin':
        flash('Access denied! Only administrators can view messages.', 'error')
        return redirect(url_for('dashboard'))
    m = ContactMessage.query.get_or_404(message_id)
    return render_template('admin_message_view.html', message=m)

@app.route('/admin/messages/<int:message_id>/update', methods=['POST'])
def update_message_status(message_id):
    if 'user_id' not in session:
        return 'Unauthorized', 401
    user = User.query.get(session['user_id'])
    if not user or user.role != 'admin':
        return 'Forbidden', 403
    status = request.form.get('status', 'pending')
    try:
        msg = ContactMessage.query.get_or_404(message_id)
        msg.status = status
        msg.is_resolved = (status == 'resolved')
        db.session.commit()
        if msg.user_id:
            notif_msg = None
            priority = 'normal'
            if status == 'in_progress':
                notif_msg = f'Your message #{msg.id} is now in progress.'
                priority = 'high'
            elif status == 'resolved':
                notif_msg = f'Your message #{msg.id} has been resolved.'
                priority = 'high'
            if notif_msg:
                notif = Notification(
                    user_id=msg.user_id,
                    message=notif_msg,
                    notification_type='admin_message',
                    priority=priority,
                    complaint_id=None
                )
                db.session.add(notif)
                db.session.commit()
        flash('Message status updated.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating message: {str(e)}', 'error')
    return redirect(url_for('admin_message_view', message_id=message_id))

@app.route('/history')
def view_history():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    q = request.args.get('q', '').strip()
    status = request.args.get('status', 'all')
    if user.role == 'admin':
        complaints_query = Complaint.query
    else:
        complaints_query = Complaint.query.filter_by(user_id=user.id)
    if status and status != 'all':
        complaints_query = complaints_query.filter_by(status=status)
    if q:
        if q.isdigit():
            complaints_query = complaints_query.filter(Complaint.id == int(q))
        else:
            complaints_query = complaints_query.filter(Complaint.subject.ilike(f'%{q}%'))
    complaints = complaints_query.order_by(Complaint.created_at.desc()).all()
    return render_template('history.html', user=user, complaints=complaints)

@app.route('/delete_complaint/<int:complaint_id>', methods=['POST'])
def delete_complaint(complaint_id):
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    if user.role != 'admin':
        flash('Access denied! Only administrators can delete complaints.', 'error')
        return redirect(url_for('dashboard'))
    complaint = Complaint.query.get_or_404(complaint_id)
    student_user = User.query.get(complaint.user_id)
    try:
        db.session.delete(complaint)
        db.session.commit()
        if student_user and student_user.id != user.id:
            notif = Notification(
                user_id=student_user.id,
                message=f'Your complaint #{complaint_id} has been deleted by the administrator.',
                notification_type='complaint_update',
                priority='high',
                complaint_id=complaint_id
            )
            db.session.add(notif)
            db.session.commit()
        flash(f'Complaint #{complaint_id} deleted successfully.', 'success')
        if student_user and student_user.id != user.id:
            session_key = f'complaint_deleted_{student_user.id}'
            session[session_key] = f'Your complaint #{complaint_id} has been deleted by the admin.'
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting complaint: {str(e)}', 'error')
    return redirect(url_for('dashboard'))

@app.context_processor
def inject_notifications():
    notifications = []
    unread_count = 0
    unresolved_messages_count = 0
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.role == 'student':
            notifications = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(10).all()
            unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        if user and user.role == 'admin':
            unresolved_messages_count = ContactMessage.query.filter((ContactMessage.status != 'resolved') | (ContactMessage.is_resolved == False)).count()
    return dict(notifications=notifications, unread_count=unread_count, unresolved_messages_count=unresolved_messages_count)

@app.route('/mark_notifications_read', methods=['POST'])
def mark_notifications_read():
    if 'user_id' not in session:
        return '', 401
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return '', 401
    if user.role != 'student':
        return '', 403
    Notification.query.filter_by(user_id=user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return '', 204

@app.route('/reset_db', methods=['POST'])
def reset_db():
    if 'user_id' not in session:
        return 'Unauthorized', 401
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return 'Unauthorized', 401
    if not user or user.role != 'admin':
        return 'Forbidden', 403
    try:
        Complaint.query.delete()
        Notification.query.delete()
        User.query.filter(User.role != 'admin').delete()
        db.session.commit()
        flash('Database reset: all complaints, notifications, and student logins removed.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error during reset: {str(e)}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('login'))
    if user.role != 'student':
        flash('Access denied! Only students can view notifications.', 'error')
        return redirect(url_for('dashboard'))
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    priority_filter = request.args.get('priority', 'all')
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    query = Notification.query.filter_by(user_id=user.id)
    if status_filter == 'read':
        query = query.filter_by(is_read=True)
    elif status_filter == 'unread':
        query = query.filter_by(is_read=False)
    if type_filter != 'all':
        query = query.filter_by(notification_type=type_filter)
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)
    if sort_by == 'oldest':
        query = query.order_by(Notification.created_at.asc())
    elif sort_by == 'priority':
        priority_order = case(
            (Notification.priority == 'urgent', 1),
            (Notification.priority == 'high', 2),
            (Notification.priority == 'normal', 3),
            (Notification.priority == 'low', 4),
            else_=5
        )
        query = query.order_by(priority_order.asc(), Notification.created_at.desc())
    else:
        query = query.order_by(Notification.created_at.desc())
    notifications = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('notifications.html', 
                         user=user, 
                         notifications=notifications,
                         status_filter=status_filter,
                         type_filter=type_filter,
                         priority_filter=priority_filter,
                         sort_by=sort_by)

@app.route('/mark_notification_read/<int:notification_id>', methods=['POST'])
def mark_notification_read(notification_id):
    if 'user_id' not in session:
        return '', 401
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return '', 401
    if user.role != 'student':
        return '', 403
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user.id:
        return '', 403
    notification.is_read = True
    db.session.commit()
    return '', 204

@app.route('/delete_notification/<int:notification_id>', methods=['POST'])
def delete_notification(notification_id):
    if 'user_id' not in session:
        return '', 401
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return '', 401
    if user.role != 'student':
        return '', 403
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != user.id:
        return '', 403
    db.session.delete(notification)
    db.session.commit()
    flash('Notification deleted successfully!', 'success')
    return redirect(url_for('notifications'))

@app.route('/clear_all_notifications', methods=['POST'])
def clear_all_notifications():
    if 'user_id' not in session:
        return '', 401
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return '', 401
    if user.role != 'student':
        return '', 403
    Notification.query.filter_by(user_id=user.id).delete()
    db.session.commit()
    flash('All notifications cleared!', 'success')
    return redirect(url_for('notifications'))

@app.route('/bulk_mark_read', methods=['POST'])
def bulk_mark_read():
    if 'user_id' not in session:
        return '', 401
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return '', 401
    if user.role != 'student':
        return '', 403
    notification_ids = request.form.getlist('notification_ids')
    if notification_ids:
        Notification.query.filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user.id
        ).update({'is_read': True}, synchronize_session=False)
        db.session.commit()
        flash(f'{len(notification_ids)} notification(s) marked as read!', 'success')
    return redirect(url_for('notifications'))

@app.route('/bulk_delete_notifications', methods=['POST'])
def bulk_delete_notifications():
    if 'user_id' not in session:
        return '', 401
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return '', 401
    if user.role != 'student':
        return '', 403
    notification_ids = request.form.getlist('notification_ids')
    if notification_ids:
        Notification.query.filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user.id
        ).delete(synchronize_session=False)
        db.session.commit()
        flash(f'{len(notification_ids)} notification(s) deleted!', 'success')
    return redirect(url_for('notifications'))

@app.route('/get_notification_count')
def get_notification_count():
    if 'user_id' not in session:
        return {'count': 0}
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return {'count': 0}
    if user.role != 'student':
        return {'count': 0}
    unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return {'count': unread_count}

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        try:
            cols = [row[1] for row in db.session.execute(text('PRAGMA table_info(contact_message)')).fetchall()]
            if 'status' not in cols:
                db.session.execute(text("ALTER TABLE contact_message ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"))
            if 'user_id' not in cols:
                db.session.execute(text("ALTER TABLE contact_message ADD COLUMN user_id INTEGER"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        # Create admin user if not exists
        admin = User.query.filter_by(email='madhur.sisodiya@mitaoe.ac.in').first()
        if not admin:
            admin = User(
                name='Madhur Sisodiya',
                email='madhur.sisodiya@mitaoe.ac.in',
                password=generate_password_hash('Madhur123@'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: madhur.sisodiya@mitaoe.ac.in / Madhur123@")
        else:
            print("Admin user already exists: madhur.sisodiya@mitaoe.ac.in")
    
    app.run(debug=True)