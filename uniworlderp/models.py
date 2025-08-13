from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from django.core.exceptions import ValidationError
import uuid
from django.db.models import F, Sum
from django.db import models, transaction
from django.db.utils import IntegrityError
from django.db.models import Prefetch
from django.utils.translation import gettext_lazy as _
class CustomerVendor(models.Model):
    ENTITY_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
    ]
    
    BUSINESS_TYPE_CHOICES = [
        ('retailer', 'Retailer'),
        ('wholesaler', 'Wholesaler'),
        ('manufacturer', 'Manufacturer'),
        ('others', 'Others'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone_number = models.CharField(max_length=15, verbose_name='Phone Number')
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    business_type = models.CharField(
        max_length=20, 
        choices=BUSINESS_TYPE_CHOICES, 
        default='others',
        verbose_name='Business Type'
    )

    entity_type = models.CharField(max_length=10, choices=ENTITY_TYPE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_vendors')


    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = 'Customer/Vendor'
        verbose_name_plural = ' Customers/Vendors'
        indexes = [
            models.Index(fields=['name', 'email', 'entity_type']),
        ]

class CustomerVendorAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_vendor = models.ForeignKey(CustomerVendor, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='customer_vendor_attachments/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Attachment for {self.customer_vendor.name}: {self.file_name}"

    class Meta:
        verbose_name = 'Customer/Vendor Attachment'
        verbose_name_plural = 'Customer/Vendor Attachments'
        indexes = [
            models.Index(fields=['customer_vendor', 'file_type']),
        ]

class SalesEmployee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='sales_employee', 
        null=True, 
        blank=True
    )
    full_name = models.CharField(max_length=255, blank=True, null=True)  # New field for full name
    
    email = models.EmailField(max_length=255, blank=True, null=True)  # New optional email field
    
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)  # State or region
    country = models.CharField(max_length=100, blank=True, null=True)  # Country

    date_of_joining = models.DateField(blank=True, null=True)  # Joining date
    sales_target = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Monthly sales target
    sales_achieved = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Sales achieved

    # Administrative fields
    is_active = models.BooleanField(default=True)  # Employee active/inactive status
    notes = models.TextField(blank=True, null=True)  # Additional notes or remarks
    profile_picture = models.ImageField(upload_to='sales_employee_pictures/', blank=True, null=True)  # Profile image
              
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales_employee_owner',default=None,blank=True,null=True)

    def save(self, *args, **kwargs):
        # Check if an authenticated user is available
        request = kwargs.pop('request', None)
        if request and request.user.is_authenticated:
            self.owner = request.user
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name or "Unnamed Employee"

    class Meta:
        verbose_name = ' Sales Employee'
        verbose_name_plural = 'Sales Employees'

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Chemical', 'Chemical'),
        ('RawMaterials', 'Raw Materials'),
        ('Others', 'Others'),
    ]
    
    UNIT_CHOICES = [
        ('PC', 'PC'),
        ('CTN', 'CTN'),
        ('TIN', 'TIN'),
        ('Others', 'Others'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True, verbose_name="Product Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description (Pack Size)")
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='Others',
        help_text="Select a category for the product."
    )   
    stock_quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Sales Price")
    unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default='PC',
        verbose_name="Unit"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='products')
    sku = models.CharField(max_length=50, unique=True, db_index=True, verbose_name="Product Code")
    is_active = models.BooleanField(default=True, help_text="Whether the product is active and available.")
    barcode = models.CharField(max_length=128, unique=True, null=True, blank=True)
    reorder_level = models.PositiveIntegerField(default=10, help_text="Stock level at which reorder is required.")  
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        null=True,
        blank=True,
        help_text="Discount amount for the product."
        )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']  # Alphabetical ordering by name
        indexes = [
            models.Index(fields=['name', 'price']),
        ]

class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJ', 'Adjustment'),
        ('RET', 'Return'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_transactions')
    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    previous_stock = models.PositiveIntegerField(default=0, help_text="Stock quantity before the transaction")
    current_stock = models.PositiveIntegerField(default=0, help_text="Stock quantity after the transaction")
    transaction_date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=50, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stock_transactions')

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} ({self.quantity})"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Capture previous stock before the transaction
            self.previous_stock = self.product.stock_quantity
            
            # Calculate the new stock quantity after the transaction
            if self.transaction_type == 'IN':
                self.current_stock = self.product.stock_quantity + self.quantity
            elif self.transaction_type == 'OUT':
                self.current_stock = self.product.stock_quantity - self.quantity
            elif self.transaction_type == 'ADJ':
                self.current_stock = self.quantity
            elif self.transaction_type == 'RET':
                self.current_stock = self.product.stock_quantity + self.quantity
            
            # Save the transaction record with previous and current stock
            super().save(*args, **kwargs)
            
            # Update the product's stock quantity
            self.product.stock_quantity = self.current_stock
            self.product.save()

    class Meta:
        verbose_name = 'Stock Transaction'
        verbose_name_plural = 'Stock Transactions'
        indexes = [
            models.Index(fields=['product', 'transaction_type', 'transaction_date']),
        ]

class SalesOrder(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ('P', 'Pending'),
        ('D', 'Delivered'),
    ]

    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey('CustomerVendor', on_delete=models.CASCADE, related_name='sales_orders')
    sales_employee = models.ForeignKey('SalesEmployee', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_orders')
    order_date = models.DateField(default=timezone.now, db_index=True)
    delivery_status = models.CharField(max_length=1, choices=DELIVERY_STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sales_orders')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Discount amount to be subtracted from subtotal")
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Shipping amount to be added to subtotal after discount")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"SalesOrder #{self.id} - {self.customer.name}"

    def update_total_amount(self):
        subtotal = sum(item.total for item in self.order_items.all())
        # Calculate final total: subtotal - discount + shipping
        self.total_amount = subtotal - self.discount + self.shipping
        self.save(update_fields=['total_amount'])

    def save(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        if not self.owner_id:
            if request and hasattr(request, 'user'):
                self.owner = request.user
            else:
                raise ValidationError("Owner must be set explicitly or passed via 'request'.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete each item individually to trigger their custom delete methods
        for item in self.order_items.all():
            item.delete()
        # Then delete the sales order itself
        super().delete(*args, **kwargs)
    def clean(self):
        super().clean()
        # if self.sales_employee and self.sales_employee.is_active is False:
        #     raise ValidationError(_("The selected sales employee is not active."))


    class Meta:
        verbose_name = 'Sales Order'
        verbose_name_plural = 'Sales Orders'
        indexes = [
            models.Index(fields=['order_date', 'delivery_status']),
        ]

class SalesOrderItem(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    Unit_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        null=True,
        blank=True,
        help_text="Discount amount per unit for the product."
        )
    
    total_discount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        null=True,
        blank=True,
        help_text="Discount amount for the product."
        )

    def __str__(self):
        return f"{self.product.name} - {self.quantity} x {self.unit_price}"

    # def calculate_total_price(self):
    #     return Decimal(self.quantity) * self.unit_price
    
    def calculate_total_price(self):
        if self.product.discount_amount and self.product.discount_amount > 0:

            discounted_price = self.unit_price - self.product.discount_amount

            discounted_price = max(discounted_price, 0)

            self.total_discount = self.product.discount_amount * self.quantity

            return Decimal(self.quantity) * discounted_price
        else:
            return Decimal(self.quantity) * self.unit_price

    def clean(self):
        super().clean()
        if not self.product_id:
            raise ValidationError(_("Product must be selected."))
        
        # Only validate stock availability for new items or when increasing quantity
        is_new = self.pk is None
        if is_new:
            # For new items, check if there's enough stock
            if self.product.stock_quantity < self.quantity:
                raise ValidationError({
                    'quantity': _("Insufficient stock for %(product)s. Available: %(available)d, requested: %(requested)d") % {
                        'product': self.product.name,
                        'available': self.product.stock_quantity,
                        'requested': self.quantity
                    }
                })
        elif not is_new:
            # For existing items, only validate if quantity is being increased
            try:
                old_item = SalesOrderItem.objects.get(pk=self.pk)
                if old_item.quantity < self.quantity and self.product.stock_quantity < (self.quantity - old_item.quantity):
                    raise ValidationError({
                        'quantity': _("Insufficient stock for %(product)s. Available: %(available)d, requested: %(requested)d") % {
                            'product': self.product.name,
                            'available': self.product.stock_quantity,
                            'requested': self.quantity - old_item.quantity
                        }
                    })
            except SalesOrderItem.DoesNotExist:
                # If the item doesn't exist, treat it as a new item
                if self.product.stock_quantity < self.quantity:
                    raise ValidationError({
                        'quantity': _("Insufficient stock for %(product)s. Available: %(available)d, requested: %(requested)d") % {
                            'product': self.product.name,
                            'available': self.product.stock_quantity,
                            'requested': self.quantity
                        }
                    })

        if self.quantity is not None and self.unit_price is not None:
            self.Unit_discount = self.product.discount_amount
            self.total = self.calculate_total_price()
        else:
            raise ValidationError(_("Quantity and unit price must be set to calculate total price."))

    @transaction.atomic
    def save(self, *args, **kwargs):
        try:
            with transaction.atomic():
                is_new = self.pk is None
                self.clean()
                
                # Check if this is a new item or if quantity has changed
                quantity_changed = False
                if not is_new:
                    old_item = SalesOrderItem.objects.get(pk=self.pk)
                    quantity_diff = self.quantity - old_item.quantity
                    quantity_changed = quantity_diff != 0
                else:
                    quantity_diff = self.quantity
                    quantity_changed = True

                super().save(*args, **kwargs)

                # Only create stock transaction if quantity has changed
                if quantity_changed and quantity_diff != 0:
                    # Determine transaction type based on quantity change and context
                    if quantity_diff > 0:
                        # Quantity increased - stock goes out
                        transaction_type = 'OUT'
                    else:
                        # Quantity decreased - return excess stock using 'RET' type per Requirement 5.4
                        transaction_type = 'RET' if not is_new else 'IN'
                
                    StockTransaction.objects.create(
                        product=self.product,
                        transaction_type=transaction_type,
                        quantity=abs(quantity_diff),
                        reference=f"SO-{self.sales_order.id}{'-Update' if not is_new else ''}",
                        owner=self.sales_order.owner
                    )   

                self.sales_order.update_total_amount()

        except IntegrityError as e:
            raise ValidationError(_("Error saving SalesOrderItem: %(error)s") % {'error': str(e)})
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(_("Unexpected error saving SalesOrderItem: %(error)s") % {'error': str(e)})

    @transaction.atomic
    def delete(self, *args, **kwargs):
        try:
            with transaction.atomic():
                StockTransaction.objects.create(
                    product=self.product,
                    transaction_type='RET',
                    quantity=self.quantity,
                    reference=f"SO-{self.sales_order.id}-DeletedItem",
                    owner=self.sales_order.owner
                )

                sales_order = self.sales_order
                super().delete(*args, **kwargs)
                sales_order.update_total_amount()
        except Exception as e:
            raise ValidationError(_("Error deleting SalesOrderItem: %(error)s") % {'error': str(e)})


class PurchaseOrderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('supplier', 'owner')

class PurchaseOrder(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ('P', 'Pending'),
        ('R', 'Received'),
    ]

    id = models.BigAutoField(primary_key=True)
    supplier = models.ForeignKey('CustomerVendor', on_delete=models.CASCADE, related_name='purchase_orders', limit_choices_to={'entity_type': 'vendor'})
    order_date = models.DateField(default=timezone.now, db_index=True) 
    delivery_status = models.CharField(max_length=1, choices=DELIVERY_STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchase_orders')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    objects = models.Manager()

    def __str__(self):
        return f"PurchaseOrder #{self.id} - {self.supplier.name}"

    def receive_order(self):
        if self.delivery_status == 'P':
            for item in self.order_items.all():
                StockTransaction.objects.create(
                    product=item.product,
                    transaction_type='IN',
                    quantity=item.quantity,
                    reference=f"PO-{self.id}",
                    owner=self.owner
                )
            self.delivery_status = 'R'
            self.save()

    def update_total_amount(self):
        self.total_amount = self.order_items.aggregate(total=Sum(F('quantity') * F('unit_price')))['total'] or Decimal('0.00')
        self.save()

    class Meta:
        verbose_name = ' Purchase Order'
        verbose_name_plural = ' Purchase Orders'
        indexes = [
            models.Index(fields=['order_date', 'delivery_status']),
        ]

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='order_items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} x {self.unit_price}"

    def save(self, *args, **kwargs):
        if self.pk:
            old_quantity = PurchaseOrderItem.objects.get(pk=self.pk).quantity
            quantity_diff = self.quantity - old_quantity
            self.product.stock_quantity = F('stock_quantity') - quantity_diff
        else:
            self.product.stock_quantity = F('stock_quantity') - self.quantity
        
        self.product.save()
        self.total = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        self.sales_order.update_total_amount()

    def delete(self, *args, **kwargs):
        self.product.stock_quantity = F('stock_quantity') + self.quantity
        self.product.save()
        super().delete(*args, **kwargs)
        self.sales_order.update_total_amount()

    class Meta:
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'
        indexes = [
            models.Index(fields=['purchase_order', 'product']),
        ]
class ARInvoiceManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'sales_employee', 'owner')

class ARInvoice(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('P', 'Pending'),
        ('C', 'Completed'),
    ]

    id = models.BigAutoField(primary_key=True)
    customer = models.ForeignKey('CustomerVendor', on_delete=models.CASCADE, related_name='ar_invoices', limit_choices_to={'entity_type': 'customer'})
    sales_employee = models.ForeignKey('SalesEmployee', on_delete=models.SET_NULL, null=True, related_name='ar_invoices')
    sales_order = models.OneToOneField('SalesOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice')
    invoice_date = models.DateField(default=timezone.now, db_index=True) 
    due_date = models.DateTimeField(default=timezone.now,db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    payment_status = models.CharField(max_length=1, choices=PAYMENT_STATUS_CHOICES, default='P', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ar_invoices')

    objects = models.Manager()

    def __str__(self):
        return f"ARInvoice #{self.id} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.pk:
            super().save(*args, **kwargs)
        self.total_amount = self.invoice_items.aggregate(total=models.Sum('total_amount'))['total'] or Decimal('0.00')
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = ' AR Invoice'
        verbose_name_plural = ' AR Invoices'
        indexes = [
            models.Index(fields=['invoice_date', 'due_date', 'payment_status']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['sales_order'], name='unique_sales_order_invoice')
        ]

class ARInvoiceItem(models.Model):
    ar_invoice = models.ForeignKey(ARInvoice, on_delete=models.CASCADE, related_name='invoice_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.total_amount = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        self.ar_invoice.save()  # Update the invoice total

    def __str__(self):
        return f"{self.product.name} - {self.quantity} x {self.unit_price}"

    class Meta:
        verbose_name = 'AR Invoice Item'
        verbose_name_plural = 'AR Invoice Items'
        indexes = [
            models.Index(fields=['ar_invoice', 'product']),
        ]






class MaterialsPurchase(models.Model):
    vendor_name = models.CharField(max_length=255)
    purchase_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Purchase {self.id} - {self.vendor_name}"

class MaterialsPurchaseItem(models.Model):
    purchase = models.ForeignKey(MaterialsPurchase, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product_name} - {self.quantity}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


#Return Sales

class ReturnSales(models.Model):
    id = models.BigAutoField(primary_key=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='returns')
    return_date = models.DateField(default=timezone.now)
    return_employee = models.ForeignKey('SalesEmployee', on_delete=models.SET_NULL, null=True, blank=False, related_name='processed_returns')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    def __str__(self):
        return f"Return #{self.id} for SalesOrder #{self.sales_order.id}"
    
    def update_total_amount(self):
        self.total_amount = sum(item.total for item in self.return_items.all())
        self.save(update_fields=['total_amount'])
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Sales Return'
        verbose_name_plural = 'Sales Returns'
        indexes = [
            models.Index(fields=['return_date']),
        ]


class ReturnSalesItem(models.Model):
    return_sales = models.ForeignKey(ReturnSales, on_delete=models.CASCADE, related_name='return_items')
    sales_order_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE, related_name='returned_items')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    def __str__(self):
        return f"Return of {self.quantity} x {self.sales_order_item.product.name}"
    
    def calculate_total_price(self):
        return Decimal(self.quantity) * self.unit_price
    
    def clean(self):
        super().clean()

        
        
        if self.quantity is None:
            return
        
        if not self.sales_order_item_id:
            raise ValidationError(_("Sales order item must be selected."))
        
        # Check if return quantity doesn't exceed original quantity
        previously_returned = ReturnSalesItem.objects.filter(
            sales_order_item=self.sales_order_item
        ).exclude(id=self.id).aggregate(total=Sum('quantity'))['total'] or 0
        
        max_returnable = self.sales_order_item.quantity - previously_returned
        if self.quantity > max_returnable:
            raise ValidationError({
                'quantity': _("Return quantity exceeds available quantity. Maximum returnable: %(max)d") % {
                    'max': max_returnable
                }
            })
    
    @transaction.atomic
    def save(self, *args, **kwargs):
        try:
            with transaction.atomic():
                # Skip processing if quantity is zero
                if self.quantity == 0:
                    return self
                
                is_new = self.pk is None
                self.clean()
                
                # Calculate the total field before saving
                self.total = self.calculate_total_price()
                
                if not is_new:
                    old_item = ReturnSalesItem.objects.get(pk=self.pk)
                    quantity_diff = self.quantity - old_item.quantity
                else:
                    quantity_diff = self.quantity
                
                super().save(*args, **kwargs)
                
                if quantity_diff != 0:
                    # Create stock transaction for the return
                    StockTransaction.objects.create(
                        product=self.sales_order_item.product,
                        transaction_type='RET',
                        quantity=abs(quantity_diff),
                        reference=f"RET-{self.return_sales.id}{'-Update' if not is_new else ''}",
                        owner=self.return_sales.owner
                    )
                
                self.return_sales.update_total_amount()
                return self
        
        except IntegrityError as e:
            raise ValidationError(_("Error saving ReturnSalesItem: %(error)s") % {'error': str(e)})
        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(_("Unexpected error saving ReturnSalesItem: %(error)s") % {'error': str(e)})