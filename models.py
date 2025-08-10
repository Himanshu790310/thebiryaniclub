from datetime import datetime, timedelta
from app import db
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # admin, delivery, customer
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    addresses = db.Column(db.Text)  # JSON array of addresses
    loyalty_points = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orders = db.relationship('Order', foreign_keys='Order.user_id', backref='customer', lazy=True)
    support_tickets = db.relationship('SupportTicket', backref='user', lazy=True)
    
    def get_addresses(self):
        """Get addresses as list"""
        if self.addresses:
            return json.loads(self.addresses)
        return []
    
    def set_addresses(self, addresses_list):
        """Set addresses from list"""
        self.addresses = json.dumps(addresses_list)
    
    def add_address(self, address):
        """Add new address"""
        addresses = self.get_addresses()
        if address not in addresses:
            addresses.append(address)
            self.set_addresses(addresses)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'loyalty_points': self.loyalty_points,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(15), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON array of items
    subtotal = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, preparing, out_for_delivery, delivered, cancelled
    payment_method = db.Column(db.String(20), default='cash')
    coupon_code = db.Column(db.String(20))
    loyalty_points_earned = db.Column(db.Integer, default=0)
    loyalty_points_used = db.Column(db.Integer, default=0)
    delivery_person_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    estimated_delivery = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 stars
    feedback = db.Column(db.Text)
    spin_used = db.Column(db.Boolean, default=False)  # Track if spin wheel was used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    delivery_person = db.relationship('User', foreign_keys=[delivery_person_id], backref='assigned_orders')
    
    def get_items(self):
        """Get items as list"""
        if self.items:
            return json.loads(self.items)
        return []
    
    def set_items(self, items_list):
        """Set items from list"""
        self.items = json.dumps(items_list)
    
    def get_status_display(self):
        status_map = {
            'pending': 'Order Received',
            'confirmed': 'Confirmed',
            'preparing': 'Being Prepared',
            'out_for_delivery': 'Out for Delivery',
            'delivered': 'Delivered',
            'cancelled': 'Cancelled'
        }
        return status_map.get(self.status, self.status.title())
    
    def can_use_spin(self):
        """Check if order is eligible for spin (delivered and not used)"""
        return self.status == 'delivered' and not self.spin_used
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_address': self.customer_address,
            'items': self.get_items(),
            'subtotal': self.subtotal,
            'discount': self.discount,
            'total': self.total,
            'status': self.status,
            'status_display': self.get_status_display(),
            'payment_method': self.payment_method,
            'coupon_code': self.coupon_code,
            'delivery_person': self.delivery_person.full_name if self.delivery_person else None,
            'estimated_delivery': self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            'rating': self.rating,
            'feedback': self.feedback,
            'can_use_spin': self.can_use_spin(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Coupon(db.Model):
    __tablename__ = 'coupons'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    reward_name = db.Column(db.String(100), nullable=False)
    effect = db.Column(db.Text, nullable=False)  # JSON of effect
    is_used = db.Column(db.Boolean, default=False)
    used_by_order_id = db.Column(db.String(20))
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_effect(self):
        """Get effect as dict"""
        if self.effect:
            return json.loads(self.effect)
        return {}
    
    def set_effect(self, effect_dict):
        """Set effect from dict"""
        self.effect = json.dumps(effect_dict)
    
    def is_valid(self):
        """Check if coupon is valid (not used and not expired)"""
        return not self.is_used and self.expires_at > datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'reward_name': self.reward_name,
            'effect': self.get_effect(),
            'is_used': self.is_used,
            'is_valid': self.is_valid(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(15), nullable=False)
    customer_email = db.Column(db.String(120))
    order_id = db.Column(db.String(20))
    category = db.Column(db.String(50), nullable=False)  # order_issue, payment_issue, feedback, other
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    admin_notes = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_status_display(self):
        status_map = {
            'open': 'Open',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
            'closed': 'Closed'
        }
        return status_map.get(self.status, self.status.title())
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'order_id': self.order_id,
            'category': self.category,
            'subject': self.subject,
            'description': self.description,
            'status': self.status,
            'status_display': self.get_status_display(),
            'priority': self.priority,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
