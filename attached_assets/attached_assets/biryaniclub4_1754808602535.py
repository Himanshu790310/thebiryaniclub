import gradio as gr
import sqlite3
import bcrypt
import random
import qrcode
from io import BytesIO
import base64
import string
import time
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# =============== ENVIRONMENT VARIABLES ===============
ADMIN_USERNAME = "cupadmin"
ADMIN_PASSWORD = "cupadmin"
UPI_ID = "7903102794-2@ybl"
DB_PATH = "biryani_club.db"

# =============== IMAGE LINKS ===============
image_links = {
    "biryani": "https://images.unsplash.com/photo-1563379091339-03246963d29a?w=300&h=200&fit=crop",
    "roll": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=300&h=200&fit=crop",
    "chowmein": "https://images.unsplash.com/photo-1612797395899-1412e31cb5c1?w=300&h=200&fit-crop",
    "drink": "https://images.unsplash.com/photo-1544145945-f90425340c7e?w=300&h=200&fit-crop",
    "extra": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=300&h=200&fit-crop",
    "logo": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=200&h=200&fit=crop"
}

# =============== MENU CONFIGURATION ===============
menu = {
    "Biryani": [
        {"name": "Veg Biryani", "price": 110, "emoji": "🍛", "img": image_links["biryani"]},
        {"name": "Egg Biryani", "price": 150, "emoji": "🍳", "img": image_links["biryani"]},
        {"name": "Chicken Biryani (Half)", "price": 120, "emoji": "🍗", "img": image_links["biryani"]},
        {"name": "Chicken Biryani (Full)", "price": 200, "emoji": "🍗", "img": image_links["biryani"]},
        {"name": "Chicken Fry Biryani", "price": 220, "emoji": "🍗🔥", "img": image_links["biryani"]},
        {"name": "Double Egg Biryani", "price": 170, "emoji": "🍳🍳", "img": image_links["biryani"]},
        {"name": "Paneer Biryani", "price": 160, "emoji": "🧀", "img": image_links["biryani"]},
    ],
    "Rolls & Snacks": [
        {"name": "Veg Roll", "price": 50, "emoji": "🌯", "img": image_links["roll"]},
        {"name": "Egg Roll", "price": 60, "emoji": "🌯🍳", "img": image_links["roll"]},
        {"name": "Paneer Roll", "price": 70, "emoji": "🌯🧀", "img": image_links["roll"]},
        {"name": "Chicken Roll", "price": 80, "emoji": "🌯🍗", "img": image_links["roll"]},
    ],
    "Chowmein": [
        {"name": "Veg Chowmein", "price": 70, "emoji": "🍜", "img": image_links["chowmein"]},
        {"name": "Egg Chowmein", "price": 80, "emoji": "🍜🍳", "img": image_links["chowmein"]},
        {"name": "Chicken Chowmein", "price": 90, "emoji": "🍜🍗", "img": image_links["chowmein"]},
    ],
    "Extras & Drinks": [
        {"name": "Soft Drink (500 ml)", "price": 35, "emoji": "🥤", "img": image_links["drink"]},
        {"name": "Extra Raita", "price": 10, "emoji": "🥣", "img": image_links["extra"]},
        {"name": "Extra Gravy (Salan)", "price": 10, "emoji": "🍼", "img": image_links["extra"]},
    ],
}

# =============== SPIN REWARDS WITH WEIGHTS ===============
spin_rewards = [
    {"name": "Free Soft Drink", "emoji": "🥤", "effect": {"item": "Soft Drink (500 ml)"}, "weight": 25},
    {"name": "₹20 off", "emoji": "💸", "effect": {"discount": 20}, "weight": 20},
    {"name": "Free Veg Roll", "emoji": "🌯", "effect": {"item": "Veg Roll"}, "weight": 15},
    {"name": "Better luck next time", "emoji": "❌", "effect": None, "weight": 30},
    {"name": "RARE ★ Free Chicken Biryani", "emoji": "🎉⭐", "effect": {"item": "Chicken Biryani (Full)"}, "weight": 3},
    {"name": "₹50 off", "emoji": "🔥", "effect": {"discount": 50}, "weight": 5},
    {"name": "Free Paneer Roll", "emoji": "🧀", "effect": {"item": "Paneer Roll"}, "weight": 2},
]

# =============== GLOBAL VARIABLES ===============
current_user = None
notifications = {}

# =============== DATABASE FUNCTIONS ===============
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.execute('PRAGMA journal_mode=WAL')
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            addresses TEXT,  -- JSON array of addresses
            loyalty_points INTEGER DEFAULT 0,
            banned BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            items TEXT NOT NULL,  -- JSON array of items
            total REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            coupon_code TEXT,
            loyalty_points_earned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Coupons table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS coupons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            reward_name TEXT NOT NULL,
            effect TEXT NOT NULL,  -- JSON of effect
            used BOOLEAN DEFAULT FALSE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create admin user if not exists
    admin_exists = cursor.execute('SELECT 1 FROM users WHERE username = ?', (ADMIN_USERNAME,)).fetchone()
    if not admin_exists:
        password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute(
            'INSERT INTO users (username, password_hash, full_name) VALUES (?, ?, ?)',
            (ADMIN_USERNAME, password_hash, "Admin User")
        )

    conn.commit()
    conn.close()

# =============== AUTHENTICATION FUNCTIONS ===============
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(username: str, password: str, confirm_password: str):
    """Register new user"""
    if not username or not password:
        return "Please fill all fields"

    if password != confirm_password:
        return "Passwords do not match"

    if len(password) < 4:
        return "Password must be at least 4 characters"

    try:
        conn = sqlite3.connect(DB_PATH, timeout=20.0)
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute(
            'INSERT INTO users (username, password_hash, addresses) VALUES (?, ?, ?)',
            (username, password_hash, json.dumps([]))
        )
        conn.commit()
        conn.close()
        return f"✅ Account created successfully! Please login with username: {username}"
    except sqlite3.IntegrityError:
        return "❌ Username already exists. Please choose a different username."

def login_user(username: str, password: str):
    """Login user"""
    global current_user

    if not username or not password:
        return False, "Please enter both username and password"

    user = get_user_by_username(username)
    if not user:
        return False, "❌ Invalid username or password"

    if user['banned']:
        return False, "❌ Your account has been banned. Contact support."

    if verify_password(password, user['password_hash']):
        current_user = user
        return True, "✅ Login successful!"
    else:
        return False, "❌ Invalid username or password"

def logout_user():
    """Logout user and return to landing page"""
    global current_user
    current_user = None
    return (
        gr.update(visible=True),   # Show landing page
        gr.update(visible=False),  # Hide main app
        "",                        # Clear user info bar
        False                      # Set logged out state
    )

def get_user_by_username(username: str) -> Optional[Dict]:
    """Get user by username from database"""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'id': row[0],
            'username': row[1],
            'password_hash': row[2],
            'full_name': row[3],
            'addresses': json.loads(row[4]) if row[4] else [],
            'loyalty_points': row[5],
            'banned': bool(row[6]),
            'created_at': row[7]
        }
    return None

# =============== MENU FUNCTIONS ===============
def get_menu_item(name: str) -> Optional[Dict]:
    """Get menu item by name"""
    for category, items in menu.items():
        for item in items:
            if item["name"] == name:
                return item
    return None

def add_to_cart(item_name: str, cart: List[Dict]) -> Tuple[List[Dict], str, str]:
    """Add item to cart"""
    item = get_menu_item(item_name)
    if not item:
        return cart, format_cart(cart), get_total_display(cart)

    # Check if item already in cart
    for cart_item in cart:
        if cart_item["name"] == item_name:
            cart_item["quantity"] += 1
            break
    else:
        # Add new item to cart
        cart_item = item.copy()
        cart_item["quantity"] = 1
        cart.append(cart_item)

    return cart, format_cart(cart), get_total_display(cart)

def format_cart(cart: List[Dict]) -> str:
    """Format cart for display"""
    if not cart:
        return "🛒 Cart is empty"

    cart_text = "🛒 *Your Cart:*\n\n"
    for item in cart:
        subtotal = item["price"] * item["quantity"]
        cart_text += f"{item['emoji']} {item['name']}\n"
        cart_text += f"₹{item['price']} × {item['quantity']} = ₹{subtotal}\n\n"

    return cart_text

def get_total_display(cart: List[Dict], coupon: Optional[Dict] = None) -> str:
    """Get total display with coupon discount"""
    if not cart:
        return "💵 Total: ₹0"

    subtotal = sum(item["price"] * item["quantity"] for item in cart)
    discount = 0

    if coupon and coupon.get('effect'):
        if 'discount' in coupon['effect']:
            discount = coupon['effect']['discount']

    total = max(0, subtotal - discount)

    if discount > 0:
        return f"💵 Subtotal: ₹{subtotal}\n🎫 Discount: -₹{discount}\n💰 *Total: ₹{total}*"
    else:
        return f"💵 Total: ₹{subtotal}"

# =============== COUPON & SPIN FUNCTIONS ===============
def create_coupon(code: str, reward_name: str, effect: Dict):
    """Create coupon in database"""
    expires_at = datetime.now() + timedelta(hours=72)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO coupons (code, reward_name, effect, expires_at) VALUES (?, ?, ?, ?)',
        (code, reward_name, json.dumps(effect), expires_at)
    )
    conn.commit()
    conn.close()

def get_valid_coupon(code: str) -> Optional[Dict]:
    """Get valid coupon from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT code, reward_name, effect FROM coupons WHERE code = ? AND used = FALSE AND expires_at > ?',
        (code, datetime.now())
    )
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            'code': row[0],
            'reward_name': row[1],
            'effect': json.loads(row[2]) if row[2] else {}
        }
    return None

def use_coupon(code: str):
    """Mark coupon as used"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE coupons SET used = TRUE WHERE code = ?', (code,))
    conn.commit()
    conn.close()

def spin_wheel():
    """Spin the wheel for rewards"""
    weights = [reward["weight"] for reward in spin_rewards]
    chosen_reward = random.choices(spin_rewards, weights=weights)[0]

    if chosen_reward["effect"] is None:
        return f"""
        🎰 *Spin Result:*

        {chosen_reward['emoji']} *{chosen_reward['name']}*

        Try again next time! 🍀
        """

    # Create coupon
    coupon_code = f"SPIN{random.randint(10000, 99999)}"
    create_coupon(coupon_code, chosen_reward["name"], chosen_reward["effect"])

    return f"""
    🎰 *Spin Result:*

    {chosen_reward['emoji']} *{chosen_reward['name']}*

    🎫 *Coupon Code:* {coupon_code}
    ⏰ Valid for 72 hours

    Use this code at checkout to claim your reward! 🎉
    """

def spin_wheel_with_order_id(order_id: str):
    """Spin wheel with order ID for guaranteed reward"""
    if not order_id:
        return "Please enter your order ID"

    # Verify order exists
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM orders WHERE order_id = ?', (order_id,))
    order_exists = cursor.fetchone()[0] > 0
    conn.close()

    if not order_exists:
        return "❌ Order ID not found. Please check your order ID."

    # Give guaranteed reward (exclude "Better luck next time")
    guaranteed_rewards = [r for r in spin_rewards if r["effect"] is not None]
    weights = [r["weight"] for r in guaranteed_rewards]
    chosen_reward = random.choices(guaranteed_rewards, weights=weights)[0]

    coupon_code = f"ORDER{order_id[:4]}{random.randint(100, 999)}"
    create_coupon(coupon_code, chosen_reward["name"], chosen_reward["effect"])

    return f"""
    🎰 *Order ID Spin Result:*

    ✅ Order {order_id} verified!
    {chosen_reward['emoji']} *{chosen_reward['name']}*

    🎫 *Coupon Code:* {coupon_code}
    ⏰ Valid for 72 hours

    Congratulations! Use this code at checkout! 🎉
    """

def apply_coupon(code: str, cart: List[Dict]):
    """Apply coupon to cart"""
    if not code:
        return None, cart, "Please enter a coupon code"

    if not cart:
        return None, cart, "Add items to cart first"

    coupon = get_valid_coupon(code)
    if not coupon:
        return None, cart, "❌ Invalid or expired coupon code"

    effect = coupon['effect']

    # Handle free item
    if 'item' in effect:
        item = get_menu_item(effect['item'])
        if item:
            free_item = item.copy()
            free_item['quantity'] = 1
            free_item['price'] = 0  # Make it free
            cart.append(free_item)
            return coupon, cart, f"✅ {coupon['reward_name']} applied! Free {effect['item']} added to cart."

    # Handle discount
    elif 'discount' in effect:
        return coupon, cart, f"✅ {coupon['reward_name']} applied! ₹{effect['discount']} discount will be applied at checkout."

    return coupon, cart, "✅ Coupon applied!"

# =============== ORDER FUNCTIONS ===============
def generate_order_id() -> str:
    """Generate unique order ID"""
    return f"ORD{random.randint(10000, 99999)}{int(time.time()) % 10000}"

def create_order(order_data: Dict) -> str:
    """Create order in database and return order ID"""
    order_id = generate_order_id()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO orders (order_id, user_id, customer_name, customer_address, items, total, coupon_code, loyalty_points_earned) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (
            order_id,
            order_data['user_id'],
            order_data['customer_name'],
            order_data['customer_address'],
            json.dumps(order_data['items']),
            order_data['total'],
            order_data['coupon_code'],
            order_data['loyalty_points_earned']
        )
    )
    conn.commit()
    conn.close()
    return order_id

def add_loyalty_points(user_id: int, points: int):
    """Add loyalty points to user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE users SET loyalty_points = loyalty_points + ? WHERE id = ?',
        (points, user_id)
    )
    conn.commit()
    conn.close()

def generate_qr(amount: float) -> str:
    """Generate UPI QR code"""
    upi_string = f"upi://pay?pa={UPI_ID}&pn=The Biryani Club&am={amount}&cu=INR"

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(upi_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f'<img src="data:image/png;base64,{img_str}" style="max-width: 300px;">'

def process_payment(name: str, address: str, cart: List[Dict], coupon: Optional[Dict]):
    """Process order and payment"""
    if not current_user:
        return cart, coupon, "❌ Please log in to place an order", "", "", format_cart(cart), get_total_display(cart, coupon)

    if not cart:
        return cart, coupon, "❌ Cart is empty", "", "", "🛒 Cart is empty", "💵 Total: ₹0"

    if not name or not address:
        return cart, coupon, "❌ Please fill in name and address", "", "", format_cart(cart), get_total_display(cart, coupon)

    # Calculate total
    subtotal = sum(item["price"] * item["quantity"] for item in cart)
    discount = 0
    coupon_code = None

    if coupon and coupon.get('effect') and 'discount' in coupon['effect']:
        discount = coupon['effect']['discount']
        coupon_code = coupon['code']
        use_coupon(coupon_code)

    total = max(0, subtotal - discount)

    # Calculate loyalty points (1 point per ₹10 spent)
    loyalty_points_earned = int(total // 10)

    # Create order
    order_data = {
        'user_id': current_user['id'],
        'customer_name': name,
        'customer_address': address,
        'items': [item['name'] for item in cart],
        'total': total,
        'coupon_code': coupon_code,
        'loyalty_points_earned': loyalty_points_earned
    }

    order_id = create_order(order_data)

    # Add loyalty points to user
    add_loyalty_points(current_user['id'], loyalty_points_earned)
    current_user['loyalty_points'] += loyalty_points_earned

    # Format items for WhatsApp
    items_text = ', '.join([f"{item['name']} × {item.get('quantity', 1)}" for item in cart])

    whatsapp_button = f"""
    <button onclick="window.open('https://wa.me/917903102794?text=Order%20ID:%20{order_id}%0ACustomer:%20{name}%0AAddress:%20{address}%0ATotal:%20₹{total}%0AItems:%20{items_text.replace(' ', '%20')}', '_blank')"
            style="background: #25d366; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 16px; cursor: pointer; margin: 10px 0; display: block; width: 100%;">
        📱 Confirm Order on WhatsApp
    </button>
    """

    qr_code = generate_qr(total)

    success_message = f"""
    ✅ *Order Placed Successfully!*

    📋 *Order ID:* {order_id}
    💰 *Total Amount:* ₹{total}
    🎯 *Loyalty Points Earned:* {loyalty_points_earned}

    📱 *Payment Instructions:*
    1. Scan the UPI QR code below
    2. Pay ₹{total}
    3. Send payment screenshot to WhatsApp

    Your order is being prepared! 🍛
    """

    return [], None, success_message, qr_code, whatsapp_button, "🛒 Cart cleared!", "💵 Total: ₹0"

# =============== USER ORDER FUNCTIONS ===============
def get_user_orders(user_id: str = None):
    """Get orders for the logged-in user"""
    if not current_user or not current_user.get('id'):
        return []

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT order_id, customer_name, items, total, status, created_at, loyalty_points_earned
        FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (current_user['id'],))
    rows = cursor.fetchall()
    conn.close()

    orders = []
    for row in rows:
        orders.append({
            'order_id': row[0],
            'customer_name': row[1],
            'items': json.loads(row[2]) if row[2] else [],
            'total': row[3],
            'status': row[4],
            'created_at': row[5],
            'loyalty_points_earned': row[6]
        })
    return orders

def display_user_orders():
    """Display orders for the logged-in user"""
    if not current_user:
        return "Please log in to view your orders"

    orders = get_user_orders()
    if not orders:
        return "No orders found. Place your first order!"

    status_emojis = {
        'pending': '⏳',
        'accepted': '✅',
        'preparing': '👨‍🍳',
        'delivered': '🚚',
        'cancelled': '❌'
    }

    order_text = f"📋 *Your Orders ({current_user['username']}):*\n\n"
    for order in orders:
        items_str = ", ".join(order['items'])
        status_emoji = status_emojis.get(order['status'], '📊')
        order_text += f"""
        *Order #{order['order_id']}*
        🛍 Items: {items_str}
        💰 Total: ₹{order['total']}
        {status_emoji} Status: *{order['status'].upper()}*
        🎯 Points Earned: {order['loyalty_points_earned']}
        📅 Date: {order['created_at']}

        ---
        """
    return order_text

def update_user_addresses(address_list):
    """Update user addresses in database"""
    if not current_user:
        return "Not logged in"

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET addresses = ? WHERE id = ?',
                   (json.dumps(address_list), current_user['id']))
    conn.commit()
    conn.close()
    current_user['addresses'] = address_list
    return "Addresses updated successfully"

def save_profile(full_name: str):
    """Save user profile information"""
    if not current_user:
        return "Not logged in"

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET full_name = ? WHERE id = ?',
                   (full_name, current_user['id']))
    conn.commit()
    conn.close()
    current_user['full_name'] = full_name
    return "✅ Profile saved successfully"

def add_address(new_address: str):
    """Add new address to user profile"""
    if not current_user:
        return "Not logged in", ""

    if not new_address.strip():
        return "Please enter a valid address", ""

    addresses = current_user.get('addresses', [])
    if new_address not in addresses:
        addresses.append(new_address.strip())
        update_user_addresses(addresses)
        return f"✅ Address saved! You now have {len(addresses)} saved addresses.", ""
    else:
        return "Address already exists", ""

def display_profile_info():
    """Display user profile information"""
    if not current_user:
        return "Please log in to view your profile"

    profile_text = f"""
    👤 *Profile Information*

    🆔 Username: {current_user['username']}
    📝 Name: {current_user.get('full_name', 'Not set')}
    🎯 Loyalty Points: {current_user.get('loyalty_points', 0)}
    📅 Member Since: {current_user.get('created_at', 'N/A')}

    📍 *Saved Addresses:*
    """

    if current_user.get('addresses'):
        for i, address in enumerate(current_user['addresses'], 1):
            profile_text += f"\n{i}. {address}"
    else:
        profile_text += "\nNo saved addresses yet."

    return profile_text

# =============== ADMIN FUNCTIONS ===============
def admin_login(username: str, password: str):
    """Admin login"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return (
            gr.update(visible=True),  # Show admin dashboard
            gr.update(visible=False), # Hide admin login
            "✅ Admin access granted",
            get_admin_analytics(),
            get_admin_orders(),
            get_admin_users()
        )
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        "❌ Invalid admin credentials",
        "",
        "",
        ""
    )

def get_order_analytics():
    """Get order analytics for admin dashboard"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total orders
    cursor.execute('SELECT COUNT(*), SUM(total) FROM orders')
    total_orders, total_revenue = cursor.fetchone()
    total_revenue = total_revenue or 0

    # Today's orders
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*), SUM(total) FROM orders WHERE date(created_at) = ?', (today,))
    today_orders, today_revenue = cursor.fetchone()
    today_orders = today_orders or 0
    today_revenue = today_revenue or 0

    # Top items
    cursor.execute('''
        SELECT item, COUNT(*) as count
        FROM orders, json_each(orders.items)
        GROUP BY item
        ORDER BY count DESC
        LIMIT 5
    ''')
    top_items = cursor.fetchall()

    conn.close()

    return {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
        'top_items': top_items
    }

def get_all_orders():
    """Get all orders for admin"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT orders.*, users.username
        FROM orders
        LEFT JOIN users ON orders.user_id = users.id
        ORDER BY orders.created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()

    orders = []
    for row in rows:
        orders.append({
            'order_id': row[1],
            'user_id': row[2],
            'customer_name': row[3],
            'customer_address': row[4],
            'items': json.loads(row[5]) if row[5] else [],
            'total': row[6],
            'status': row[7],
            'coupon_code': row[8],
            'loyalty_points_earned': row[9],
            'created_at': row[10],
            'username': row[11]
        })
    return orders

def admin_update_order_status(order_id: str, new_status: str):
    """Admin function to update order status"""
    if not order_id or not new_status:
        return "Please enter order ID and select status"

    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ? WHERE order_id = ?', (new_status, order_id))

    if cursor.rowcount == 0:
        conn.close()
        return "Order ID not found"

    conn.commit()
    conn.close()
    return f"✅ Order {order_id} status updated to: {new_status.upper()}"

def get_admin_analytics():
    """Get analytics for admin dashboard"""
    analytics = get_order_analytics()

    analytics_text = f"""
    📊 *Order Analytics*

    📈 *Total Orders:* {analytics['total_orders']}
    💰 *Total Revenue:* ₹{analytics['total_revenue']:.2f}

    🚀 *Today's Orders:* {analytics['today_orders']}
    💵 *Today's Revenue:* ₹{analytics['today_revenue']:.2f}

    🔥 *Top 5 Selling Items:*
    """

    for i, (item, count) in enumerate(analytics['top_items'], 1):
        analytics_text += f"\n{i}. {item} - {count} orders"

    return analytics_text

def get_admin_orders():
    """Get orders for admin management"""
    orders = get_all_orders()

    if not orders:
        return "No orders found"

    orders_text = "📋 *All Orders:*\n\n"
    for order in orders[:20]:  # Show latest 20 orders
        items_str = ", ".join(order['items'])
        orders_text += f"""
        *Order #{order['order_id']}* ({order['status']})
        👤 Customer: {order['customer_name']} ({order.get('username', 'Guest')})
        📍 Address: {order['customer_address']}
        🛍 Items: {items_str}
        💰 Total: ₹{order['total']}
        📅 Date: {order['created_at']}

        ---
        """

    return orders_text

def get_admin_users():
    """Get all users for admin"""
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    cursor = conn.cursor()
    cursor.execute('SELECT username, full_name, loyalty_points, banned, created_at FROM users ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No users found"

    user_text = "👥 *All Users:*\n\n"
    for row in rows:
        username, full_name, loyalty_points, banned, created_at = row
        status = "🚫 BANNED" if banned else "✅ Active"
        user_text += f"""
        *{username}*
        📝 Name: {full_name or 'Not set'}
        🎯 Points: {loyalty_points}
        📊 Status: {status}
        📅 Joined: {created_at}

        ---
        """
    return user_text

# =============== CSS STYLING ===============
custom_css = """
<style>
.header {
    text-align: center;
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
    padding: 30px;
    border-radius: 20px;
    margin-bottom: 20px;
}

.header h1 {
    color: #333;
    font-size: 2.5em;
    margin-bottom: 5px;
}

.header p {
    color: #666;
    font-size: 1.2em;
}

.menu-category {
    font-size: 1.4em;
    font-weight: bold;
    color: #d84315;
    margin-bottom: 15px;
    text-align: center;
}

.menu-item {
    display: flex;
    align-items: center;
    background: white;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}

.menu-item:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.menu-item img {
    width: 80px;
    height: 60px;
    border-radius: 10px;
    object-fit: cover;
    margin-right: 15px;
}

.item-details {
    flex-grow: 1;
}

.item-name {
    font-size: 1.1em;
    font-weight: bold;
    color: #d84315;
    margin-bottom: 5px;
}

.item-price {
    color: #d84315;
    font-weight: bold;
    font-size: 1.1em;
}

.cart-title {
    font-size: 1.3em;
    font-weight: bold;
    color: #2e7d32;
    margin-bottom: 15px;
    text-align: center;
}

.cart-section {
    background: #f1f8e9;
    padding: 15px;
    border-radius: 15px;
    margin-bottom: 10px;
}

.spin-button {
    background: linear-gradient(45deg, #ff6b6b, #feca57) !important;
    color: white !important;
    font-weight: bold !important;
    font-size: 1.1em !important;
    border: none !important;
    border-radius: 15px !important;
    padding: 15px 30px !important;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

.rewards-section {
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
    border-radius: 20px;
    margin-bottom: 20px;
}

.section-header {
    text-align: center;
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
    padding: 25px;
    border-radius: 15px;
    margin-bottom: 20px;
}

.admin-section {
    background: #f5f5f5;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
}

.address-item {
    background: #e8f5e9;
    padding: 10px;
    border-radius: 8px;
    margin: 5px 0;
}

.profile-section {
    background: #e3f2fd;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 15px;
}

.user-info-bar {
    background: #e8f5e8;
    padding: 10px;
    border-radius: 8px;
    margin: 10px 0;
    font-size: 1.1em;
}

.refresh-button {
    background: #4caf50 !important;
    color: white !important;
}

.error-message {
    color: #d32f2f;
    font-weight: bold;
}

.success-message {
    color: #388e3c;
    font-weight: bold;
}
</style>
"""

# =============== GRADIO INTERFACE ===============
def create_interface():
    """Create the main Gradio interface"""
    with gr.Blocks(css=custom_css, title="The Biryani Club") as app:
        # Initialize database
        init_database()

        # State variables
        cart_state = gr.State([])
        coupon_state = gr.State(None)
        user_logged_in = gr.State(False)

        # Header
        gr.HTML("""
        <div class="header">
            <h1>🍛 The Biryani Club</h1>
            <p>Authentic flavors delivered to your doorstep!</p>
        </div>
        """)

        # Landing page with login/register (shown initially)
        landing_page = gr.Group(visible=True)
        with landing_page:
            gr.HTML("""
            <div style="text-align: center; padding: 50px 20px; background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%); border-radius: 20px; margin: 20px 0;">
                <h1 style="color: #333; font-size: 2.5em; margin-bottom: 10px;">🍛 Welcome to The Biryani Club</h1>
                <p style="color: #666; font-size: 1.2em; margin-bottom: 30px;">Please login or register to access our delicious menu</p>
            </div>
            """)

            with gr.Tabs() as auth_tabs:
                with gr.Tab("🔐 Login"):
                    login_username = gr.Textbox(placeholder="Enter your username", label="Username")
                    login_password = gr.Textbox(placeholder="Enter your password", label="Password", type="password")
                    login_btn = gr.Button("Login", variant="primary", size="lg")
                    login_message = gr.Markdown("")

                with gr.Tab("👤 Register"):
                    reg_username = gr.Textbox(placeholder="Choose a username", label="Username")
                    reg_password = gr.Textbox(placeholder="Choose a password", label="Password", type="password")
                    reg_confirm = gr.Textbox(placeholder="Confirm your password", label="Confirm Password", type="password")
                    register_btn = gr.Button("Register", variant="secondary", size="lg")
                    register_message = gr.Markdown("")

        # Main application (hidden initially)
        main_app = gr.Group(visible=False)
        with main_app:
            # User info bar
            user_info_bar = gr.HTML("")
            logout_btn = gr.Button("Logout", variant="secondary", size="sm")

            # Main tabs
            with gr.Tabs() as main_tabs:
                # Menu Tab
                with gr.Tab("🍽 Menu"):
                    with gr.Row():
                        with gr.Column(scale=2):
                            # Store add to cart buttons for later configuration
                            add_buttons = []

                            # Menu sections
                            for category, items in menu.items():
                                with gr.Accordion(f"🍛 {category}", open=True):
                                    gr.HTML(f'<div class="menu-category">{category}</div>')
                                    for item in items:
                                        with gr.Row():
                                            with gr.Column():
                                                gr.HTML(f"""
                                                <div class="menu-item">
                                                    <img src="{item['img']}" alt="{item['name']}">
                                                    <div class="item-details">
                                                        <div class="item-name">{item['emoji']} {item['name']}</div>
                                                        <div class="item-price">₹{item['price']}</div>
                                                    </div>
                                                </div>
                                                """)
                                            with gr.Column(scale=0):
                                                add_btn = gr.Button("Add to Cart", variant="primary", size="sm")
                                                add_buttons.append((add_btn, item['name']))

                        with gr.Column(scale=1):
                            # Cart section
                            gr.HTML('<div class="cart-title">🛒 Your Cart</div>')
                            cart_display = gr.Markdown("🛒 Cart is empty", elem_classes=["cart-section"])
                            total_display = gr.Markdown("💵 Total: ₹0")

                            # Coupon section
                            with gr.Group():
                                gr.Markdown("### 🎫 Apply Coupon")
                                coupon_input = gr.Textbox(placeholder="Enter coupon code", label="Coupon Code")
                                apply_coupon_btn = gr.Button("Apply Coupon", variant="secondary")
                                coupon_message = gr.Markdown("")

                            # Checkout section
                            with gr.Group():
                                gr.Markdown("### 📋 Checkout")
                                customer_name = gr.Textbox(placeholder="Your full name", label="Name")

                                # Address management
                                with gr.Row():
                                    saved_addresses = gr.Dropdown(choices=[], label="Saved Addresses", interactive=True)
                                    refresh_addresses_btn = gr.Button("🔄", size="sm")

                                customer_address = gr.Textbox(placeholder="Delivery address", label="Address", lines=2)

                                with gr.Row():
                                    save_address_btn = gr.Button("Save Address", variant="secondary", size="sm")
                                    place_order_btn = gr.Button("Place Order", variant="primary", size="lg")

                            # Order confirmation
                            order_message = gr.Markdown("")
                            qr_code_display = gr.HTML("")
                            whatsapp_btn = gr.HTML("")

                # My Orders Tab
                with gr.Tab("📋 My Orders"):
                    gr.HTML("""
                    <div class="section-header">
                        <h2>📋 Your Order History</h2>
                        <p>Track your orders and view status updates</p>
                    </div>
                    """)

                    with gr.Row():
                        refresh_my_orders_btn = gr.Button("🔄 Refresh Orders", variant="primary", elem_classes=["refresh-button"])

                    user_orders_display = gr.Markdown("Loading your orders...")

                # Rewards Tab
                with gr.Tab("🎯 Rewards"):
                    gr.HTML("""
                    <div class="rewards-section">
                        <h2>🎰 Spin the Wheel of Fortune!</h2>
                        <p>Use your order ID to spin and win amazing rewards!</p>
                    </div>
                    """)

                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### 🎰 Regular Spin")
                            spin_btn = gr.Button("🎰 SPIN THE WHEEL!", variant="primary", size="lg",
                                               elem_classes=["spin-button"])
                            spin_result = gr.Markdown("")

                            gr.Markdown("---")

                            gr.Markdown("### 🎯 Order ID Spin")
                            gr.Markdown("Have an order ID? Get guaranteed rewards!")
                            order_id_input = gr.Textbox(placeholder="Enter your order ID", label="Order ID")
                            spin_with_order_btn = gr.Button("🎰 SPIN WITH ORDER ID!", variant="secondary", size="lg")
                            order_spin_result = gr.Markdown("")

                # Profile Tab
                with gr.Tab("👤 Profile"):
                    profile_info = gr.Markdown("")

                    with gr.Group():
                        gr.Markdown("### 📝 Update Profile")
                        profile_name = gr.Textbox(label="Full Name", value="")
                        save_profile_btn = gr.Button("Save Profile", variant="primary")
                        profile_save_message = gr.Markdown("")

                    with gr.Group():
                        gr.Markdown("### 📍 Manage Addresses")
                        current_addresses_display = gr.Markdown("")
                        new_address_input = gr.Textbox(placeholder="Enter new address", label="New Address", lines=2)
                        add_address_btn = gr.Button("Add Address", variant="secondary")
                        address_message = gr.Markdown("")

                # Admin Tab (only visible to admin)
                with gr.Tab("🔧 Admin", visible=False) as admin_tab:
                    # Admin login
                    admin_login_section = gr.Group(visible=True)
                    with admin_login_section:
                        gr.Markdown("### 🔒 Admin Login")
                        admin_username_input = gr.Textbox(label="Admin Username")
                        admin_password_input = gr.Textbox(label="Admin Password", type="password")
                        admin_login_btn = gr.Button("Admin Login", variant="primary")
                        admin_login_message = gr.Markdown("")

                    # Admin dashboard
                    admin_dashboard = gr.Group(visible=False)
                    with admin_dashboard:
                        gr.Markdown("### 🔧 Admin Dashboard")

                        with gr.Tabs():
                            with gr.Tab("📊 Analytics"):
                                analytics_display = gr.Markdown("")
                                refresh_analytics_btn = gr.Button("Refresh Analytics", variant="primary", elem_classes=["refresh-button"])

                            with gr.Tab("📋 Orders"):
                                orders_display = gr.Markdown("")
                                refresh_orders_btn = gr.Button("Refresh Orders", variant="primary", elem_classes=["refresh-button"])

                                with gr.Row():
                                    order_id_admin_input = gr.Textbox(label="Order ID")
                                    order_status_input = gr.Dropdown(
                                        choices=["pending", "accepted", "preparing", "delivered", "cancelled"],
                                        label="New Status"
                                    )
                                    update_order_btn = gr.Button("Update Status", variant="primary")

                                order_update_message = gr.Markdown("")

                            with gr.Tab("👥 Users"):
                                users_display = gr.Markdown("")
                                refresh_users_btn = gr.Button("Refresh Users", variant="primary", elem_classes=["refresh-button"])

        # Helper functions for login/logout and address management
        def successful_login(username):
            """Handle successful login"""
            admin_tab_visible = username == ADMIN_USERNAME
            return (
                gr.update(visible=False),  # Hide landing page
                gr.update(visible=True),   # Show main app
                f"<div class='user-info-bar'>Welcome, <strong>{username}</strong>! 🎯 Points: {current_user.get('loyalty_points', 0)}</div>",
                gr.update(visible=admin_tab_visible)  # Show admin tab only for admin
            )

        def get_user_addresses():
            """Get user addresses for dropdown"""
            if current_user and current_user.get('addresses'):
                return gr.update(choices=current_user['addresses'])
            return gr.update(choices=[])

        def select_saved_address(address):
            """Select address from dropdown"""
            return gr.update(value=address or "")

        def save_new_address(address):
            """Save new address"""
            if not current_user or not address.strip():
                return "Please enter a valid address", gr.update()

            addresses = current_user.get('addresses', [])
            if address not in addresses:
                addresses.append(address.strip())
                update_user_addresses(addresses)
                return f"✅ Address saved! You now have {len(addresses)} saved addresses.", gr.update(choices=addresses)
            else:
                return "Address already exists", gr.update()


        # Configure add to cart buttons
        for add_btn, item_name in add_buttons:
            add_btn.click(
                fn=lambda x, cart, name=item_name: add_to_cart(name, cart),
                inputs=[gr.State(), cart_state],
                outputs=[cart_state, cart_display, total_display]
            )

        # Authentication event handlers
        register_btn.click(
            fn=register_user,
            inputs=[reg_username, reg_password, reg_confirm],
            outputs=[register_message]
        )

        login_btn.click(
            fn=login_user,
            inputs=[login_username, login_password],
            outputs=[user_logged_in, login_message]
        ).then(
            fn=lambda logged_in: successful_login(current_user['username']) if logged_in and current_user else (gr.update(), gr.update(), "", gr.update(visible=False)),
            inputs=[user_logged_in],
            outputs=[landing_page, main_app, user_info_bar, admin_tab]
        ).then(
            fn=display_user_orders,
            outputs=[user_orders_display]
        ).then(
            fn=get_user_addresses,
            outputs=[saved_addresses]
        ).then(
            fn=display_profile_info,
            outputs=[profile_info]
        ).then(
            fn=lambda: gr.update(value=current_user.get('full_name', '')) if current_user else gr.update(value=""),
            outputs=[profile_name]
        )

        # Logout handler
        logout_btn.click(
            fn=logout_user,
            outputs=[landing_page, main_app, user_info_bar, user_logged_in]
        )

        # Address management
        saved_addresses.change(
            fn=select_saved_address,
            inputs=[saved_addresses],
            outputs=[customer_address]
        )

        refresh_addresses_btn.click(
            fn=get_user_addresses,
            outputs=[saved_addresses]
        )

        save_address_btn.click(
            fn=save_new_address,
            inputs=[customer_address],
            outputs=[address_message, saved_addresses]
        )

        # My Orders functionality
        refresh_my_orders_btn.click(
            fn=display_user_orders,
            outputs=[user_orders_display]
        )

        # Coupon application
        apply_coupon_btn.click(
            fn=apply_coupon,
            inputs=[coupon_input, cart_state],
            outputs=[coupon_state, cart_state, coupon_message]
        ).then(
            fn=format_cart,
            inputs=[cart_state],
            outputs=[cart_display]
        ).then(
            fn=get_total_display,
            inputs=[cart_state, coupon_state],
            outputs=[total_display]
        )

        # Order placement
        place_order_btn.click(
            fn=process_payment,
            inputs=[customer_name, customer_address, cart_state, coupon_state],
            outputs=[cart_state, coupon_state, order_message, qr_code_display, whatsapp_btn, cart_display, total_display]
        ).then(
            fn=display_user_orders,
            outputs=[user_orders_display]
        ).then(
            fn=get_user_addresses,
            outputs=[saved_addresses]
        )

        # Spin functionality
        spin_btn.click(
            fn=spin_wheel,
            outputs=[spin_result]
        )

        spin_with_order_btn.click(
            fn=spin_wheel_with_order_id,
            inputs=[order_id_input],
            outputs=[order_spin_result]
        )

        # Profile functionality
        save_profile_btn.click(
            fn=save_profile,
            inputs=[profile_name],
            outputs=[profile_save_message]
        ).then(
            fn=display_profile_info,
            outputs=[profile_info]
        )

        add_address_btn.click(
            fn=add_address,
            inputs=[new_address_input],
            outputs=[address_message, new_address_input]
        ).then(
            fn=get_user_addresses,
            outputs=[saved_addresses]
        ).then(
            fn=display_profile_info,
            outputs=[profile_info]
        )

        # Admin functionality
        admin_login_btn.click(
            fn=admin_login,
            inputs=[admin_username_input, admin_password_input],
            outputs=[admin_dashboard, admin_login_section, admin_login_message, analytics_display, orders_display, users_display]
        )

        refresh_analytics_btn.click(
            fn=get_admin_analytics,
            outputs=[analytics_display]
        )

        refresh_orders_btn.click(
            fn=get_admin_orders,
            outputs=[orders_display]
        )

        update_order_btn.click(
            fn=admin_update_order_status,
            inputs=[order_id_admin_input, order_status_input],
            outputs=[order_update_message]
        ).then(
            fn=get_admin_orders,
            outputs=[orders_display]
        )

        refresh_users_btn.click(
            fn=get_admin_users,
            outputs=[users_display]
        )

        return app

# =============== MAIN ===============
if __name__ == "__main__":
    # Initialize database
    init_database()

    # Create interface
    interface = create_interface()

    # Launch with Gradio sharing
    interface.launch(share=True)
