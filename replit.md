# Overview

Biryani Club is a comprehensive food delivery web application built with Flask. The system manages online food ordering with features including user authentication, order management, delivery tracking, customer support, loyalty rewards (spin wheel), and administrative controls. It's designed as a multi-role platform serving customers, delivery personnel, and administrators.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Template Engine**: Jinja2 with Flask for server-side rendering
- **CSS Framework**: Bootstrap 5 for responsive design with custom CSS styling
- **JavaScript**: Vanilla JavaScript for interactive features like cart management, spin wheel, and order tracking
- **Component Structure**: Modular template system with base template and component includes for notifications

## Backend Architecture
- **Framework**: Flask web framework with application factory pattern
- **Database ORM**: SQLAlchemy with declarative base for database operations
- **Authentication**: Session-based authentication with bcrypt password hashing
- **Blueprint Structure**: Organized into separate blueprints for main, admin, delivery, customer, and support routes
- **Configuration Management**: Environment-based configuration with default values

## Database Design
- **Database**: SQLite for development (configurable to other databases via DATABASE_URL)
- **Key Models**:
  - Users table with role-based access (admin, delivery, customer)
  - Orders table with status tracking and customer information
  - Support tickets for customer service
  - Notifications system for real-time updates
  - Coupons table for promotional campaigns

## Authentication & Authorization
- **Role-Based Access Control**: Three distinct user roles with specific permissions
- **Session Management**: Flask sessions with configurable lifetime (24 hours default)
- **Password Security**: bcrypt hashing for secure password storage
- **Route Protection**: Decorators for login requirements and role-specific access

## Business Logic
- **Menu Management**: Configuration-driven menu system with categories and pricing
- **Order Processing**: Complete order lifecycle from cart to delivery
- **Loyalty System**: Spin wheel rewards system tied to completed orders
- **Support System**: Ticket-based customer support with status tracking

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web framework and extensions (SQLAlchemy, session management)
- **bcrypt**: Password hashing and verification
- **SQLAlchemy**: Database ORM and model management

## Frontend Dependencies
- **Bootstrap 5**: CSS framework via CDN
- **Font Awesome 6**: Icon library via CDN
- **Custom JavaScript**: Cart management, notifications, and interactive features

## Potential Integrations
- **Payment Gateway**: UPI integration configured (currently using static UPI ID)
- **SMS Service**: WhatsApp integration for customer support
- **QR Code Generation**: Built-in QR code functionality for orders

## Development Tools
- **Database**: SQLite for development (production-ready for other databases)
- **Session Storage**: Flask sessions (configurable for Redis/other stores)
- **File Storage**: Local file system (expandable to cloud storage)

## Configuration Management
- **Environment Variables**: DATABASE_URL, SECRET_KEY support
- **Default Credentials**: Admin and delivery accounts with configurable credentials
- **Business Settings**: Support phone, UPI details, and operational parameters