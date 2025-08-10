import os
import string
import random
from datetime import timedelta

# Environment configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'biryani-club-secret-key-2024')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///biryani_club.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Authentication settings
    ADMIN_USERNAME = "cupadmin"
    ADMIN_PASSWORD = "cupadmin123"
    
    # Delivery person credentials
    DELIVERY_USERNAME = "delivery"
    DELIVERY_PASSWORD = "delivery123"
    
    # Customer support
    SUPPORT_PHONE = "9241169665"
    
    # Payment settings
    UPI_ID = "7903102794-2@ybl"
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

# Menu configuration with enhanced structure
MENU_CONFIG = {
    "Biryani": [
        {"name": "Veg Biryani", "price": 110, "emoji": "🍛", "category": "vegetarian", "description": "Aromatic basmati rice with mixed vegetables and spices"},
        {"name": "Egg Biryani", "price": 150, "emoji": "🍳", "category": "egg", "description": "Flavorful rice with boiled eggs and traditional spices"},
        {"name": "Chicken Biryani (Half)", "price": 120, "emoji": "🍗", "category": "non-vegetarian", "description": "Half portion of tender chicken biryani"},
        {"name": "Chicken Biryani (Full)", "price": 200, "emoji": "🍗", "category": "non-vegetarian", "description": "Full portion of succulent chicken biryani"},
        {"name": "Chicken Fry Biryani", "price": 220, "emoji": "🍗🔥", "category": "non-vegetarian", "description": "Special fried chicken biryani with extra spices"},
        {"name": "Double Egg Biryani", "price": 170, "emoji": "🍳🍳", "category": "egg", "description": "Biryani with double portion of eggs"},
        {"name": "Paneer Biryani", "price": 160, "emoji": "🧀", "category": "vegetarian", "description": "Rich paneer biryani with cottage cheese"},
    ],
    "Rolls & Snacks": [
        {"name": "Veg Roll", "price": 50, "emoji": "🌯", "category": "vegetarian", "description": "Fresh vegetable wrap with chutneys"},
        {"name": "Egg Roll", "price": 60, "emoji": "🌯🍳", "category": "egg", "description": "Scrambled egg roll with spices"},
        {"name": "Paneer Roll", "price": 70, "emoji": "🌯🧀", "category": "vegetarian", "description": "Paneer tikka roll with mint chutney"},
        {"name": "Chicken Roll", "price": 80, "emoji": "🌯🍗", "category": "non-vegetarian", "description": "Chicken tikka roll with special sauce"},
    ],
    "Chowmein": [
        {"name": "Veg Chowmein", "price": 70, "emoji": "🍜", "category": "vegetarian", "description": "Stir-fried noodles with fresh vegetables"},
        {"name": "Egg Chowmein", "price": 80, "emoji": "🍜🍳", "category": "egg", "description": "Noodles with scrambled eggs and vegetables"},
        {"name": "Chicken Chowmein", "price": 90, "emoji": "🍜🍗", "category": "non-vegetarian", "description": "Chicken chowmein with tender pieces"},
    ],
    "Extras & Drinks": [
        {"name": "Soft Drink (500 ml)", "price": 35, "emoji": "🥤", "category": "beverage", "description": "Chilled soft drink of your choice"},
        {"name": "Extra Raita", "price": 10, "emoji": "🥣", "category": "extra", "description": "Cool yogurt-based side dish"},
        {"name": "Extra Gravy (Salan)", "price": 10, "emoji": "🍼", "category": "extra", "description": "Traditional curry gravy"},
    ],
}

# Spin wheel rewards with balanced weights
SPIN_REWARDS = [
    {"name": "Free Soft Drink", "emoji": "🥤", "effect": {"item": "Soft Drink (500 ml)"}, "weight": 25},
    {"name": "₹20 off", "emoji": "💸", "effect": {"discount": 20}, "weight": 20},
    {"name": "Free Veg Roll", "emoji": "🌯", "effect": {"item": "Veg Roll"}, "weight": 15},
    {"name": "Better luck next time", "emoji": "❌", "effect": None, "weight": 30},
    {"name": "RARE ★ Free Chicken Biryani", "emoji": "🎉⭐", "effect": {"item": "Chicken Biryani (Full)"}, "weight": 3},
    {"name": "₹50 off", "emoji": "🔥", "effect": {"discount": 50}, "weight": 5},
    {"name": "Free Paneer Roll", "emoji": "🧀", "effect": {"item": "Paneer Roll"}, "weight": 2},
]

def generate_coupon_code():
    """Generate a secure 15-digit alphanumeric coupon code"""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(15))

def generate_order_id():
    """Generate unique order ID"""
    return f"BC{random.randint(100000, 999999)}"
