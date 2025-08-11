from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, timedelta
import random, json, qrcode, base64
from io import BytesIO

from extensions import db
from models import User, Order, Coupon, SupportTicket, Notification
from auth import (
    login_user, logout_user, get_current_user, is_logged_in, 
    login_required, admin_required, delivery_required, authenticate_user
)
from config import MENU_CONFIG, SPIN_REWARDS, generate_coupon_code, generate_order_id, Config

# Create blueprints
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)
delivery_bp = Blueprint('delivery', __name__)
customer_bp = Blueprint('customer', __name__)
support_bp = Blueprint('support', __name__)

# ===================== MAIN ROUTES =====================
@main_bp.route('/')
def index():
    return render_template('index.html', menu=MENU_CONFIG, support_phone=Config.SUPPORT_PHONE)

@main_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('main.index'))

# ===================== ADMIN ROUTES =====================
@admin_bp.route('/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user, message = authenticate_user(username, password, 'admin')
        if user:
            login_user(user.id, user.role)
            flash(message, 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/dashboard')
@admin_required
def dashboard_admin():
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    delivered_orders = Order.query.filter_by(status='delivered').count()
    total_revenue = db.session.query(db.func.sum(Order.total)).filter_by(status='delivered').scalar() or 0
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    open_tickets = SupportTicket.query.filter_by(status='open').count()
    
    stats = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': total_revenue,
        'open_tickets': open_tickets
    }
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)

# (Your other admin routes: orders, update_order_status, support_tickets, update_ticket_status)

# ===================== DELIVERY ROUTES =====================
@delivery_bp.route('/login', methods=['GET', 'POST'])
def login_delivery():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user, message = authenticate_user(username, password, 'delivery')
        if user:
            login_user(user.id, user.role)
            flash(message, 'success')
            return redirect(url_for('delivery.dashboard_delivery'))
        else:
            flash(message, 'error')
    
    return render_template('delivery/login.html')

# (Your other delivery routes: dashboard, mark_delivered)

# ===================== CUSTOMER ROUTES =====================
@customer_bp.route('/menu')
def menu():
    return render_template('customer/menu.html', menu=MENU_CONFIG)

# (Your other customer routes: cart, add_to_cart, remove_from_cart, checkout, place_order, track_order, spin_wheel, rate_order)

# ===================== SUPPORT ROUTES =====================
@support_bp.route('/contact')
def contact():
    return render_template('support/contact.html', support_phone=Config.SUPPORT_PHONE)

# (Your other support routes: create_ticket)

# ===================== API ROUTES =====================
@main_bp.route('/api/check_coupon', methods=['POST'])
def check_coupon():
    data = request.get_json()
    coupon_code = data.get('coupon_code', '').strip().upper()
    if not coupon_code:
        return jsonify({'valid': False, 'message': 'Coupon code is required'})
    
    coupon = Coupon.query.filter_by(code=coupon_code).first()
    if coupon and coupon.is_valid():
        return jsonify({
            'valid': True,
            'reward_name': coupon.reward_name,
            'effect': coupon.get_effect()
        })
    else:
        return jsonify({'valid': False, 'message': 'Invalid or expired coupon code'})
