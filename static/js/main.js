// Global variables
let cart = [];
let isSpinning = false;

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    updateCartDisplay();
    bindEventListeners();
    loadNotifications();
}

// Event listeners
function bindEventListeners() {
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', function() {
            const itemName = this.getAttribute('data-item');
            addToCart(itemName);
        });
    });

    // Remove from cart buttons
    document.querySelectorAll('.remove-from-cart').forEach(button => {
        button.addEventListener('click', function() {
            const itemName = this.getAttribute('data-item');
            removeFromCart(itemName);
        });
    });

    // Quantity controls
    document.querySelectorAll('.quantity-increase').forEach(button => {
        button.addEventListener('click', function() {
            const itemName = this.getAttribute('data-item');
            changeQuantity(itemName, 1);
        });
    });

    document.querySelectorAll('.quantity-decrease').forEach(button => {
        button.addEventListener('click', function() {
            const itemName = this.getAttribute('data-item');
            changeQuantity(itemName, -1);
        });
    });

    // Coupon validation
    const couponInput = document.getElementById('coupon-code');
    if (couponInput) {
        couponInput.addEventListener('blur', validateCoupon);
    }

    // Order form submission
    const orderForm = document.getElementById('order-form');
    if (orderForm) {
        orderForm.addEventListener('submit', placeOrder);
    }

    // Spin wheel
    const spinButton = document.getElementById('spin-btn');
    if (spinButton) {
        spinButton.addEventListener('click', spinWheel);
    }

    // Support form
    const supportForm = document.getElementById('support-form');
    if (supportForm) {
        supportForm.addEventListener('submit', submitSupportTicket);
    }

    // Order rating
    const ratingStars = document.querySelectorAll('.rating-star');
    ratingStars.forEach(star => {
        star.addEventListener('click', function() {
            const rating = this.getAttribute('data-rating');
            setRating(rating);
        });
    });

    // Modal controls
    document.querySelectorAll('.modal-trigger').forEach(trigger => {
        trigger.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal');
            openModal(modalId);
        });
    });

    document.querySelectorAll('.modal-close').forEach(closeBtn => {
        closeBtn.addEventListener('click', function() {
            const modal = this.closest('.modal');
            closeModal(modal.id);
        });
    });

    // Close modal on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal(this.id);
            }
        });
    });
}

// Cart functions
function addToCart(itemName) {
    showLoading();
    
    fetch('/customer/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ item_name: itemName })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            updateCartCounter(data.cart_count);
            showNotification('Item added to cart!', 'success');
        } else {
            showNotification(data.error || 'Failed to add item to cart', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('Failed to add item to cart', 'error');
    });
}

function removeFromCart(itemName) {
    fetch('/customer/remove_from_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ item_name: itemName })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCounter(data.cart_count);
            updateCartSubtotal(data.subtotal);
            // Remove item from DOM
            const cartItem = document.querySelector(`[data-cart-item="${itemName}"]`);
            if (cartItem) {
                cartItem.remove();
            }
            showNotification('Item removed from cart', 'info');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to remove item', 'error');
    });
}

function changeQuantity(itemName, change) {
    if (change > 0) {
        addToCart(itemName);
    } else {
        // Implement decrease quantity logic if needed
        console.log('Decrease quantity for:', itemName);
    }
}

function updateCartCounter(count) {
    const counter = document.getElementById('cart-counter');
    if (counter) {
        counter.textContent = count;
        counter.style.display = count > 0 ? 'flex' : 'none';
    }
}

function updateCartSubtotal(subtotal) {
    const subtotalElement = document.getElementById('cart-subtotal');
    if (subtotalElement) {
        subtotalElement.textContent = `₹${subtotal}`;
    }
}

function updateCartDisplay() {
    // This would typically fetch cart data from server or localStorage
    // For now, we'll just ensure the counter is properly displayed
    const cartItems = document.querySelectorAll('.cart-item');
    updateCartCounter(cartItems.length);
}

// Coupon validation
function validateCoupon() {
    const couponInput = document.getElementById('coupon-code');
    const couponCode = couponInput.value.trim();
    
    if (!couponCode) {
        clearCouponFeedback();
        return;
    }

    showCouponValidating();

    fetch('/api/check_coupon', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ coupon_code: couponCode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.valid) {
            showCouponValid(data.reward_name, data.effect);
            calculateTotalWithCoupon(data.effect);
        } else {
            showCouponInvalid(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showCouponInvalid('Error validating coupon');
    });
}

function showCouponValidating() {
    const feedback = document.getElementById('coupon-feedback');
    if (feedback) {
        feedback.innerHTML = '<div class="text-info">Validating coupon...</div>';
    }
}

function showCouponValid(rewardName, effect) {
    const feedback = document.getElementById('coupon-feedback');
    if (feedback) {
        let discountText = '';
        if (effect.discount) {
            discountText = ` (₹${effect.discount} off)`;
        } else if (effect.item) {
            discountText = ` (Free ${effect.item})`;
        }
        feedback.innerHTML = `<div class="text-success">✅ Valid: ${rewardName}${discountText}</div>`;
    }
}

function showCouponInvalid(message) {
    const feedback = document.getElementById('coupon-feedback');
    if (feedback) {
        feedback.innerHTML = `<div class="text-danger">❌ ${message}</div>`;
    }
}

function clearCouponFeedback() {
    const feedback = document.getElementById('coupon-feedback');
    if (feedback) {
        feedback.innerHTML = '';
    }
}

function calculateTotalWithCoupon(effect) {
    const subtotalElement = document.getElementById('cart-subtotal');
    const totalElement = document.getElementById('cart-total');
    
    if (subtotalElement && totalElement) {
        const subtotal = parseFloat(subtotalElement.textContent.replace('₹', ''));
        let discount = 0;
        
        if (effect.discount) {
            discount = Math.min(effect.discount, subtotal);
        }
        
        const total = Math.max(0, subtotal - discount);
        totalElement.innerHTML = discount > 0 ? 
            `Subtotal: ₹${subtotal}<br>Discount: -₹${discount}<br><strong>Total: ₹${total}</strong>` :
            `<strong>Total: ₹${subtotal}</strong>`;
    }
}

// Order placement
function placeOrder(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const orderData = {
        customer_name: formData.get('customer_name'),
        customer_phone: formData.get('customer_phone'),
        customer_address: formData.get('customer_address'),
        payment_method: formData.get('payment_method') || 'cash',
        coupon_code: formData.get('coupon_code') || ''
    };

    // Validate required fields
    if (!orderData.customer_name || !orderData.customer_phone || !orderData.customer_address) {
        showNotification('Please fill all required fields', 'error');
        return;
    }

    showLoading();

    fetch('/customer/place_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showOrderSuccess(data);
        } else {
            showNotification(data.error || 'Failed to place order', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('Failed to place order', 'error');
    });
}

function showOrderSuccess(data) {
    const modal = document.getElementById('order-success-modal');
    if (modal) {
        document.getElementById('order-id-display').textContent = data.order_id;
        document.getElementById('order-total-display').textContent = `₹${data.total}`;
        document.getElementById('order-qr-code').innerHTML = `<img src="data:image/png;base64,${data.qr_code}" alt="QR Code">`;
        document.getElementById('estimated-delivery').textContent = `${data.estimated_delivery} minutes`;
        openModal('order-success-modal');
        
        // Clear cart
        updateCartCounter(0);
    }
}

// Spin wheel functionality
function spinWheel() {
    if (isSpinning) return;

    const orderIdInput = document.getElementById('order-id-input');
    const orderId = orderIdInput ? orderIdInput.value.trim() : '';

    if (!orderId) {
        showNotification('Please enter your order ID', 'error');
        return;
    }

    isSpinning = true;
    const wheel = document.getElementById('spin-wheel');
    const spinBtn = document.getElementById('spin-btn');

    // Disable button and show loading
    spinBtn.disabled = true;
    spinBtn.textContent = 'Spinning...';

    fetch('/customer/spin_wheel', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ order_id: orderId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Animate wheel spinning
            const randomRotation = Math.floor(Math.random() * 360) + 1440; // At least 4 full rotations
            wheel.style.transform = `rotate(${randomRotation}deg)`;
            
            // Show result after animation
            setTimeout(() => {
                showSpinResult(data.result);
                isSpinning = false;
                spinBtn.disabled = false;
                spinBtn.textContent = 'Spin Wheel';
            }, 3000);
        } else {
            showNotification(data.error || 'Failed to spin wheel', 'error');
            isSpinning = false;
            spinBtn.disabled = false;
            spinBtn.textContent = 'Spin Wheel';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to spin wheel', 'error');
        isSpinning = false;
        spinBtn.disabled = false;
        spinBtn.textContent = 'Spin Wheel';
    });
}

function showSpinResult(result) {
    const modal = document.getElementById('spin-result-modal');
    if (modal) {
        document.getElementById('result-emoji').textContent = result.emoji;
        document.getElementById('result-name').textContent = result.reward_name;
        
        let resultText = '';
        if (result.effect) {
            if (result.coupon_code) {
                resultText = `Your coupon code: <strong>${result.coupon_code}</strong><br>Valid for 72 hours!`;
            }
        } else {
            resultText = 'Try again with your next order!';
        }
        
        document.getElementById('result-description').innerHTML = resultText;
        openModal('spin-result-modal');
    }
}

// Support ticket submission
function submitSupportTicket(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const ticketData = {
        customer_name: formData.get('customer_name'),
        customer_phone: formData.get('customer_phone'),
        customer_email: formData.get('customer_email'),
        order_id: formData.get('order_id'),
        category: formData.get('category'),
        subject: formData.get('subject'),
        description: formData.get('description')
    };

    showLoading();

    fetch('/support/create_ticket', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(ticketData)
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showNotification(`Support ticket created: ${data.ticket_id}`, 'success');
            event.target.reset();
        } else {
            showNotification(data.error || 'Failed to create support ticket', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showNotification('Failed to create support ticket', 'error');
    });
}

// Rating functionality
function setRating(rating) {
    const stars = document.querySelectorAll('.rating-star');
    stars.forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
    
    // Store rating value
    const ratingInput = document.getElementById('order-rating');
    if (ratingInput) {
        ratingInput.value = rating;
    }
}

function submitRating() {
    const orderId = document.getElementById('rating-order-id').value;
    const rating = document.getElementById('order-rating').value;
    const feedback = document.getElementById('order-feedback').value;

    if (!rating) {
        showNotification('Please select a rating', 'error');
        return;
    }

    fetch('/customer/rate_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            order_id: orderId,
            rating: parseInt(rating),
            feedback: feedback
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            closeModal('rating-modal');
        } else {
            showNotification(data.error || 'Failed to submit rating', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to submit rating', 'error');
    });
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type} fade-in`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="closeNotification(this)">×</button>
        </div>
    `;
    
    const container = getOrCreateNotificationContainer();
    container.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function closeNotification(button) {
    const notification = button.closest('.notification');
    if (notification) {
        notification.remove();
    }
}

function getOrCreateNotificationContainer() {
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    return container;
}

function loadNotifications() {
    // Add notification styles if not present
    if (!document.getElementById('notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            }
            
            .notification {
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin-bottom: 10px;
                overflow: hidden;
                border-left: 4px solid;
            }
            
            .notification-info { border-left-color: #3498db; }
            .notification-success { border-left-color: #27ae60; }
            .notification-warning { border-left-color: #f39c12; }
            .notification-error { border-left-color: #e74c3c; }
            
            .notification-content {
                padding: 16px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            
            .notification-message {
                flex: 1;
                font-size: 14px;
                line-height: 1.4;
            }
            
            .notification-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #999;
                margin-left: 12px;
            }
            
            .notification-close:hover {
                color: #666;
            }
        `;
        document.head.appendChild(styles);
    }
}

// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// Loading indicator
function showLoading() {
    const loader = document.getElementById('loading-spinner');
    if (loader) {
        loader.style.display = 'block';
    } else {
        // Create loading spinner if not exists
        const spinner = document.createElement('div');
        spinner.id = 'loading-spinner';
        spinner.className = 'loading-overlay';
        spinner.innerHTML = '<div class="spinner"></div>';
        document.body.appendChild(spinner);
    }
}

function hideLoading() {
    const loader = document.getElementById('loading-spinner');
    if (loader) {
        loader.style.display = 'none';
    }
}

// Utility functions
function formatCurrency(amount) {
    return `₹${parseFloat(amount).toFixed(2)}`;
}

function formatPhone(phone) {
    // Simple phone formatting for Indian numbers
    return phone.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');
}

function validatePhone(phone) {
    const phoneRegex = /^[6-9]\d{9}$/;
    return phoneRegex.test(phone.replace(/\D/g, ''));
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Order tracking
function trackOrder(orderId) {
    if (!orderId) {
        showNotification('Please enter an order ID', 'error');
        return;
    }

    fetch(`/api/order_status/${orderId}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification(data.error, 'error');
        } else {
            displayOrderStatus(data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Failed to track order', 'error');
    });
}

function displayOrderStatus(order) {
    const modal = document.getElementById('order-status-modal');
    if (modal) {
        document.getElementById('status-order-id').textContent = order.order_id;
        document.getElementById('status-customer-name').textContent = order.customer_name;
        document.getElementById('status-total').textContent = formatCurrency(order.total);
        document.getElementById('status-current').textContent = order.status_display;
        
        // Update timeline if present
        updateOrderTimeline(order.status);
        
        openModal('order-status-modal');
    }
}

function updateOrderTimeline(status) {
    const timeline = document.getElementById('order-timeline');
    if (!timeline) return;

    const statuses = ['pending', 'confirmed', 'preparing', 'out_for_delivery', 'delivered'];
    const currentIndex = statuses.indexOf(status);

    timeline.querySelectorAll('.timeline-item').forEach((item, index) => {
        item.classList.remove('active', 'current');
        if (index < currentIndex) {
            item.classList.add('active');
        } else if (index === currentIndex) {
            item.classList.add('current');
        }
    });
}

// Auto-refresh for admin/delivery dashboards
function startAutoRefresh() {
    if (window.location.pathname.includes('/admin/') || window.location.pathname.includes('/delivery/')) {
        setInterval(() => {
            // Refresh page data every 30 seconds
            location.reload();
        }, 30000);
    }
}

// Initialize auto-refresh if needed
startAutoRefresh();

// Export functions for global access
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.validateCoupon = validateCoupon;
window.placeOrder = placeOrder;
window.spinWheel = spinWheel;
window.submitSupportTicket = submitSupportTicket;
window.setRating = setRating;
window.submitRating = submitRating;
window.trackOrder = trackOrder;
window.openModal = openModal;
window.closeModal = closeModal;
window.closeNotification = closeNotification;
