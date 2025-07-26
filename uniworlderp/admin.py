from django.contrib import admin
from .models import (
    CustomerVendor, CustomerVendorAttachment, SalesEmployee, Product,
    SalesOrder, SalesOrderItem, PurchaseOrder, PurchaseOrderItem,
    ARInvoice, ARInvoiceItem
)

class CustomerVendorAttachmentInline(admin.TabularInline):
    model = CustomerVendorAttachment
    extra = 1

@admin.register(CustomerVendor)
class CustomerVendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'entity_type', 'created_at')
    list_filter = ('entity_type', 'created_at')
    search_fields = ('name', 'email', 'phone_number')
    inlines = [CustomerVendorAttachmentInline]

@admin.register(SalesEmployee)
class SalesEmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone_number')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_quantity', 'price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')

class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'sales_employee', 'order_date', 'delivery_status')
    list_filter = ('delivery_status', 'order_date')
    search_fields = ('customer__name', 'sales_employee__user__username')
    inlines = [SalesOrderItemInline]

# class PurchaseOrderItemInline(admin.TabularInline):
#     model = PurchaseOrderItem
#     extra = 1

# @admin.register(PurchaseOrder)
# class PurchaseOrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'supplier', 'order_date', 'created_at')
#     list_filter = ('order_date', 'created_at')
#     search_fields = ('supplier__name',)
#     inlines = [PurchaseOrderItemInline]

class ARInvoiceItemInline(admin.TabularInline):
    model = ARInvoiceItem
    extra = 1

@admin.register(ARInvoice)
class ARInvoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'sales_employee', 'invoice_date', 'due_date', 'total_amount', 'payment_status')
    list_filter = ('payment_status', 'invoice_date', 'due_date')
    search_fields = ('customer__name', 'sales_employee__user__username')
    inlines = [ARInvoiceItemInline]

# Register the remaining models
admin.site.register(CustomerVendorAttachment)
admin.site.register(SalesOrderItem)
admin.site.register(PurchaseOrderItem)
admin.site.register(ARInvoiceItem)