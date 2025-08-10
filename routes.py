from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, timedelta
import random
import json
from app import db
from models import User, Order, Coupon, SupportTicket, Notification
from auth import (login_user, logout_user, get_current_user, is_logged_in, 
                 login_required, admin_required, delivery_required, authenticate_user)
from config import MENU_CONFIG, SPIN_REWARDS, generate_coupon_code, generate_order_id, Config
import qrcode
from io import BytesIO
import base64

# Create blueprints
main_bp = Blueprint('main', __name__)
admin_bp = Blueprint('admin', __name__)
delivery_bp = Blueprint('delivery', __name__)
customer_bp = Blueprint('customer', __name__)
support_bp = Blueprint('support', __name__)

# =============== MAIN ROUTES ===============
@main_bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html', menu=MENU_CONFIG, support_phone=Config.SUPPORT_PHONE)

@main_bp.route('/logout')
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('main.index'))

# =============== ADMIN ROUTES ===============
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
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
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    delivered_orders = Order.query.filter_by(status='delivered').count()
    total_revenue = db.session.query(db.func.sum(Order.total)).filter_by(status='delivered').scalar() or 0
    
    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Open support tickets
    open_tickets = SupportTicket.query.filter_by(status='open').count()
    
    stats = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'total_revenue': total_revenue,
        'open_tickets': open_tickets
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)

@admin_bp.route('/orders')
@admin_required
def orders():
    """Manage orders"""
    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Order.query
    if status != 'all':
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/orders.html', orders=orders, current_status=status)

@admin_bp.route('/update_order_status', methods=['POST'])
@admin_required
def update_order_status():
    """Update order status"""
    data = request.get_json()
    order_id = data.get('order_id')
    new_status = data.get('status')
    delivery_person_id = data.get('delivery_person_id')
    
    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    order.status = new_status
    if delivery_person_id:
        order.delivery_person_id = delivery_person_id
    
    # Set estimated delivery time
    if new_status == 'confirmed':
        order.estimated_delivery = datetime.utcnow() + timedelta(minutes=45)
    elif new_status == 'out_for_delivery':
        order.estimated_delivery = datetime.utcnow() + timedelta(minutes=15)
    
    db.session.commit()
    
    # Create notification for customer
    if order.user_id:
        notification = Notification(
            user_id=order.user_id,
            title=f"Order {order.order_id} Updated",
            message=f"Your order status has been updated to: {order.get_status_display()}",
            type='info'
        )
        db.session.add(notification)
        db.session.commit()
    
    return jsonify({'success': True, 'message': 'Order status updated successfully'})

@admin_bp.route('/support_tickets')
@admin_required
def support_tickets():
    """View support tickets"""
    status = request.args.get('status', 'open')
    tickets = SupportTicket.query.filter_by(status=status).order_by(SupportTicket.created_at.desc()).all()
    return render_template('admin/support_tickets.html', tickets=tickets, current_status=status)

@admin_bp.route('/update_ticket_status', methods=['POST'])
@admin_required
def update_ticket_status():
    """Update support ticket status"""
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    new_status = data.get('status')
    admin_notes = data.get('admin_notes', '')
    
    ticket = SupportTicket.query.filter_by(ticket_id=ticket_id).first()
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    ticket.status = new_status
    ticket.admin_notes = admin_notes
    
    if new_status in ['resolved', 'closed']:
        ticket.resolved_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Ticket status updated successfully'})

# =============== DELIVERY ROUTES ===============
@delivery_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Delivery person login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user, message = authenticate_user(username, password, 'delivery')
        if user:
            login_user(user.id, user.role)
            flash(message, 'success')
            return redirect(url_for('delivery.dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('delivery/login.html')

@delivery_bp.route('/dashboard')
@delivery_required
def dashboard():
    """Delivery dashboard"""
    user = get_current_user()
    
    # Get assigned orders
    assigned_orders = Order.query.filter_by(
        delivery_person_id=user.id,
        status='out_for_delivery'
    ).order_by(Order.created_at.desc()).all()
    
    # Get delivered orders today
    today = datetime.utcnow().date()
    delivered_today = Order.query.filter(
        Order.delivery_person_id == user.id,
        Order.status == 'delivered',
        db.func.date(Order.updated_at) == today
    ).count()
    
    return render_template('delivery/dashboard.html', 
                         assigned_orders=assigned_orders, 
                         delivered_today=delivered_today)

@delivery_bp.route('/mark_delivered', methods=['POST'])
@delivery_required
def mark_delivered():
    """Mark order as delivered"""
    data = request.get_json()
    order_id = data.get('order_id')
    
    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    user = get_current_user()
    if order.delivery_person_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    order.status = 'delivered'
    db.session.commit()
    
    # Create notification for customer
    if order.user_id:
        notification = Notification(
            user_id=order.user_id,
            title=f"Order {order.order_id} Delivered!",
            message="Your order has been delivered successfully. Enjoy your meal!",
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
    
    return jsonify({'success': True, 'message': 'Order marked as delivered'})

# =============== CUSTOMER ROUTES ===============
@customer_bp.route('/menu')
def menu():
    """Display menu"""
    return render_template('customer/menu.html', menu=MENU_CONFIG)

@customer_bp.route('/cart')
def cart():
    """Display cart"""
    cart_items = session.get('cart', [])
    return render_template('customer/cart.html', cart_items=cart_items)

@customer_bp.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Add item to cart"""
    data = request.get_json()
    item_name = data.get('item_name')
    
    # Find item in menu
    item = None
    for category, items in MENU_CONFIG.items():
        for menu_item in items:
            if menu_item['name'] == item_name:
                item = menu_item.copy()
                item['category'] = category
                break
        if item:
            break
    
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    # Get current cart
    cart = session.get('cart', [])
    
    # Check if item already in cart
    for cart_item in cart:
        if cart_item['name'] == item_name:
            cart_item['quantity'] += 1
            break
    else:
        # Add new item
        item['quantity'] = 1
        cart.append(item)
    
    session['cart'] = cart
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    total_items = sum(item['quantity'] for item in cart)
    
    return jsonify({
        'success': True,
        'cart_count': total_items,
        'subtotal': subtotal
    })

@customer_bp.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    """Remove item from cart"""
    data = request.get_json()
    item_name = data.get('item_name')
    
    cart = session.get('cart', [])
    cart = [item for item in cart if item['name'] != item_name]
    session['cart'] = cart
    
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    total_items = sum(item['quantity'] for item in cart)
    
    return jsonify({
        'success': True,
        'cart_count': total_items,
        'subtotal': subtotal
    })

@customer_bp.route('/checkout')
def checkout():
    """Checkout page"""
    cart = session.get('cart', [])
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('customer.menu'))
    
    return render_template('customer/checkout.html', cart=cart, upi_id=Config.UPI_ID)

@customer_bp.route('/place_order', methods=['POST'])
def place_order():
    """Place order"""
    cart = session.get('cart', [])
    if not cart:
        return jsonify({'error': 'Cart is empty'}), 400
    
    data = request.get_json()
    customer_name = data.get('customer_name')
    customer_phone = data.get('customer_phone')
    customer_address = data.get('customer_address')
    payment_method = data.get('payment_method', 'cash')
    coupon_code = data.get('coupon_code', '').strip().upper()
    
    if not all([customer_name, customer_phone, customer_address]):
        return jsonify({'error': 'All fields are required'}), 400
    
    # Calculate totals
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    discount = 0
    
    # Apply coupon if provided
    coupon = None
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        if coupon and coupon.is_valid():
            effect = coupon.get_effect()
            if 'discount' in effect:
                discount = min(effect['discount'], subtotal)
            elif 'item' in effect:
                # Add free item to cart
                free_item_name = effect['item']
                for category, items in MENU_CONFIG.items():
                    for menu_item in items:
                        if menu_item['name'] == free_item_name:
                            free_item = menu_item.copy()
                            free_item['quantity'] = 1
                            free_item['is_free'] = True
                            cart.append(free_item)
                            break
        else:
            return jsonify({'error': 'Invalid or expired coupon code'}), 400
    
    total = subtotal - discount
    
    # Create order
    order_id = generate_order_id()
    order = Order(
        order_id=order_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_address=customer_address,
        subtotal=subtotal,
        discount=discount,
        total=total,
        payment_method=payment_method,
        coupon_code=coupon_code if coupon else None,
        loyalty_points_earned=int(total // 10)  # 1 point per ₹10
    )
    order.set_items(cart)
    
    db.session.add(order)
    
    # Mark coupon as used
    if coupon:
        coupon.is_used = True
        coupon.used_by_order_id = order_id
    
    db.session.commit()
    
    # Clear cart
    session.pop('cart', None)
    
    # Generate QR code for order tracking
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(f"Order ID: {order_id}")
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    qr_img.save(buffered)
    qr_code_b64 = base64.b64encode(buffered.getvalue()).decode()
    
    return jsonify({
        'success': True,
        'order_id': order_id,
        'total': total,
        'qr_code': qr_code_b64,
        'estimated_delivery': 45  # minutes
    })

@customer_bp.route('/track_order/<order_id>')
def track_order(order_id):
    """Track order status"""
    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        flash('Order not found.', 'error')
        return redirect(url_for('main.index'))
    
    return render_template('customer/orders.html', order=order)

@customer_bp.route('/spin_wheel', methods=['GET', 'POST'])
def spin_wheel():
    """Spin wheel for rewards"""
    if request.method == 'POST':
        data = request.get_json()
        order_id = data.get('order_id', '').strip().upper()
        
        if not order_id:
            return jsonify({'error': 'Order ID is required'}), 400
        
        # Check if order exists and is eligible
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        if not order.can_use_spin():
            if order.spin_used:
                return jsonify({'error': 'Spin already used for this order'}), 400
            elif order.status != 'delivered':
                return jsonify({'error': 'Order must be delivered to use spin'}), 400
        
        # Perform spin
        weights = [reward["weight"] for reward in SPIN_REWARDS]
        chosen_reward = random.choices(SPIN_REWARDS, weights=weights)[0]
        
        # Mark spin as used
        order.spin_used = True
        
        result = {
            'reward_name': chosen_reward['name'],
            'emoji': chosen_reward['emoji'],
            'effect': chosen_reward['effect']
        }
        
        # Create coupon if reward has effect
        if chosen_reward['effect']:
            coupon_code = generate_coupon_code()
            coupon = Coupon(
                code=coupon_code,
                reward_name=chosen_reward['name'],
                expires_at=datetime.utcnow() + timedelta(hours=72)
            )
            coupon.set_effect(chosen_reward['effect'])
            db.session.add(coupon)
            result['coupon_code'] = coupon_code
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    return render_template('customer/spin.html')

@customer_bp.route('/rate_order', methods=['POST'])
def rate_order():
    """Rate and provide feedback for order"""
    data = request.get_json()
    order_id = data.get('order_id')
    rating = data.get('rating')
    feedback = data.get('feedback', '')
    
    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    if order.status != 'delivered':
        return jsonify({'error': 'Can only rate delivered orders'}), 400
    
    order.rating = rating
    order.feedback = feedback
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Thank you for your feedback!'})

# =============== SUPPORT ROUTES ===============
@support_bp.route('/contact')
def contact():
    """Contact support page"""
    return render_template('support/contact.html', support_phone=Config.SUPPORT_PHONE)

@support_bp.route('/create_ticket', methods=['POST'])
def create_ticket():
    """Create support ticket"""
    data = request.get_json()
    
    ticket_id = f"TK{random.randint(100000, 999999)}"
    ticket = SupportTicket(
        ticket_id=ticket_id,
        customer_name=data.get('customer_name'),
        customer_phone=data.get('customer_phone'),
        customer_email=data.get('customer_email'),
        order_id=data.get('order_id'),
        category=data.get('category'),
        subject=data.get('subject'),
        description=data.get('description')
    )
    
    db.session.add(ticket)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'ticket_id': ticket_id,
        'message': 'Support ticket created successfully. Our team will contact you soon.'
    })

# =============== API ROUTES ===============
@main_bp.route('/api/check_coupon', methods=['POST'])
def check_coupon():
    """Check if coupon is valid"""
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

@main_bp.route('/api/order_status/<order_id>')
def order_status(order_id):
    """Get order status API"""
    order = Order.query.filter_by(order_id=order_id).first()
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify(order.to_dict())
