import bcrypt
from functools import wraps
from flask import session, request, redirect, url_for, flash, jsonify
from models import User

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def login_user(user_id: int, role: str):
    """Login user by setting session"""
    session['user_id'] = user_id
    session['user_role'] = role
    session.permanent = True

def logout_user():
    """Logout user by clearing session"""
    session.pop('user_id', None)
    session.pop('user_role', None)

def get_current_user():
    """Get current logged in user"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session

def has_role(role):
    """Check if current user has specific role"""
    return session.get('user_role') == role

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please login to access this page.', 'warning')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in() or not has_role('admin'):
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            flash('Admin access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def delivery_required(f):
    """Decorator to require delivery role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in() or not has_role('delivery'):
            if request.is_json:
                return jsonify({'error': 'Delivery access required'}), 403
            flash('Delivery access required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def authenticate_user(username: str, password: str, required_role: str = None):
    """Authenticate user with username, password and optional role check"""
    user = User.query.filter_by(username=username, is_active=True).first()
    
    if not user:
        return None, "Invalid username or password"
    
    if user.is_banned:
        return None, "Account has been banned. Contact support."
    
    if not verify_password(password, user.password_hash):
        return None, "Invalid username or password"
    
    if required_role and user.role != required_role:
        return None, f"Access denied. {required_role.title()} role required."
    
    return user, "Login successful"
