# UniWorld ERP System - Project Index

## Overview
This is a comprehensive Django-based ERP (Enterprise Resource Planning) system for managing sales, inventory, purchases, and customer relationships. The system is designed for small to medium-sized businesses requiring integrated business management capabilities.

## Project Structure

### Core Information
- **Framework**: Django 5.1.4
- **Database**: SQLite (default), PostgreSQL support available
- **Python Version**: 3.12+ (based on migration files)
- **Main Project**: `myproject`
- **Main App**: `uniworlderp`

### Directory Structure
```
D:\7-4-25-uniworld\
├── myproject/                 # Main Django project
│   ├── settings.py           # Project settings
│   ├── urls.py               # URL configuration
│   └── wsgi.py               # WSGI configuration
├── uniworlderp/              # Main ERP application
│   ├── models.py             # Database models
│   ├── views/                # View modules
│   ├── templates/            # HTML templates
│   ├── migrations/           # Database migrations
│   ├── forms.py              # Django forms
│   ├── admin.py              # Django admin configuration
│   └── urls.py               # App URL patterns
├── company/                  # Company-related functionality
├── permission/               # Permission management
├── templates/                # Global templates
├── static/                   # Static files (CSS, JS, images)
├── media/                    # User-uploaded files
├── venv/                     # Virtual environment
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── db.sqlite3                # SQLite database
└── .gitignore               # Git ignore rules
```

## Key Features

### 1. Customer & Vendor Management
- **Model**: `CustomerVendor`
- Unified model for both customers and vendors
- Contact information management
- File attachments support
- Entity type differentiation

### 2. Sales Management
- **Models**: `SalesOrder`, `SalesOrderItem`, `SalesEmployee`
- Complete sales order lifecycle
- Sales employee assignment
- Order item management with discounts
- Return sales functionality
- Sales target tracking

### 3. Inventory Management
- **Models**: `Product`, `StockTransaction`
- Product catalog with categories
- Stock level tracking
- Automated stock transactions
- Reorder level management
- Barcode support

### 4. Purchase Management
- **Models**: `PurchaseOrder`, `PurchaseOrderItem`
- Purchase order creation and management
- Supplier management
- Inventory receipt processing
- Purchase order status tracking

### 5. Financial Management
- **Models**: `ARInvoice`, `ARInvoiceItem`
- Accounts Receivable invoice generation
- Payment status tracking
- Invoice item management
- Due date management

### 6. Materials Purchase
- **Models**: `MaterialsPurchase`, `MaterialsPurchaseItem`
- Separate materials purchasing workflow
- Vendor management
- Purchase tracking and reporting

### 7. Return Management
- **Models**: `ReturnSales`, `ReturnSalesItem`
- Sales return processing
- Return quantity validation
- Stock adjustment for returns
- Return authorization tracking

## Database Models

### Core Models
1. **CustomerVendor**: Unified customer/vendor management
2. **SalesEmployee**: Sales team management with targets
3. **Product**: Product catalog with inventory
4. **StockTransaction**: Inventory movement tracking

### Transaction Models
5. **SalesOrder**: Sales order management
6. **SalesOrderItem**: Order line items
7. **PurchaseOrder**: Purchase order management
8. **PurchaseOrderItem**: Purchase line items
9. **ARInvoice**: Accounts receivable invoices
10. **ARInvoiceItem**: Invoice line items
11. **MaterialsPurchase**: Materials purchasing
12. **MaterialsPurchaseItem**: Materials purchase items
13. **ReturnSales**: Sales returns
14. **ReturnSalesItem**: Return line items

### Supporting Models
15. **CustomerVendorAttachment**: File attachments

## Key Functionalities

### Inventory Management
- Real-time stock tracking
- Automatic stock adjustments on sales/purchases
- Reorder level alerts
- Product categorization
- Barcode scanning support

### Sales Process
- Order creation and management
- Customer assignment
- Sales employee tracking
- Discount management
- Order fulfillment status

### Financial Operations
- Invoice generation from sales orders
- Payment status tracking
- Due date management
- Customer credit management

### Purchase Operations
- Purchase order creation
- Supplier management
- Goods receipt processing
- Purchase order status tracking

### Return Processing
- Sales return authorization
- Return quantity validation
- Automatic stock adjustment
- Return documentation

## Technical Features

### Security
- User authentication and authorization
- Owner-based data isolation
- Permission management system
- Secure file upload handling

### Data Integrity
- Database transactions for critical operations
- Validation rules for business logic
- Referential integrity constraints
- Automated total calculations

### Performance
- Database indexing for key fields
- Optimized queries with select_related
- Efficient data retrieval patterns
- Caching for static data

## Development Information

### Dependencies
- Django 5.1.4
- Pillow (image handling)
- python-decouple (configuration)
- dj-database-url (database configuration)
- gunicorn (WSGI server)
- whitenoise (static file serving)
- psycopg2-binary (PostgreSQL support)

### Database Migrations
- 31 migration files documenting schema evolution
- Comprehensive field additions and modifications
- Index optimizations
- Constraint implementations

### View Architecture
- Modular view structure in `views/` directory
- Separate modules for different functionalities:
  - `customer_views.py`
  - `sales_order_views.py`
  - `product_views.py`
  - `invoice_views.py`
  - `purchase_views.py`
  - `report_views.py`
  - `materials_purchase_views.py`

### Template Organization
- Organized by functionality
- Reusable template components
- Print-friendly templates
- Form templates with validation

## Configuration

### Environment Variables
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode toggle
- `DATABASE_URL`: Database connection string

### Static Files
- WhiteNoise for static file serving
- Organized in `static/` directory
- Collectstatic configuration for production

### Media Files
- User uploads in `media/` directory
- Product images support
- Document attachments

## Installation & Setup

1. **Virtual Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

2. **Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   python manage.py migrate
   ```

4. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

## Business Logic

### Stock Management
- Automatic stock deduction on sales
- Stock return on sales cancellation
- Purchase order receipt processing
- Stock adjustment capabilities

### Order Processing
- Sales order validation
- Inventory availability checking
- Customer credit verification
- Order fulfillment tracking

### Financial Calculations
- Automatic total calculations
- Discount processing
- Tax calculations (if applicable)
- Payment tracking

## Reporting Capabilities
- Sales reports
- Inventory reports
- Customer reports
- Purchase reports
- Financial reports

## Future Enhancements
- REST API implementation (commented out)
- Real-time notifications
- Advanced reporting dashboard
- Multi-company support
- Mobile application support

## Contact & Support
This is a comprehensive ERP system built with Django, providing integrated business management capabilities for sales, inventory, purchasing, and customer relationship management.

---
*Last Updated: July 15, 2025*
*Generated by: AI Assistant*
