from django import forms
import uuid
from django.utils.text import slugify
from django.conf import settings


from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from django.db.models.functions import Concat
from django.db.models import Value, CharField
from django.db.models import F
from django.utils.safestring import mark_safe

from .models import (
    CustomerVendor, SalesEmployee, Product, SalesOrder, SalesOrderItem, ReturnSales, ReturnSalesItem,
    ARInvoice, ARInvoiceItem, PurchaseOrder, PurchaseOrderItem,StockTransaction
)
from decimal import Decimal, InvalidOperation

# Common CSS classes
BASE_FIELD_CLASSES = (
    'block w-full px-3 py-2  border border-gray-200 rounded-md '
    'text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 '
    'focus:ring-[#800000] focus:border-transparent transition duration-200 '
    'ease-in-out shadow-sm hover:bg-white'
)

FILE_UPLOAD_CLASSES = (
    'mt-1 block w-full text-sm text-[hsl(var(--muted-foreground))] '
    'file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 '
    'file:text-sm file:font-semibold file:bg-[hsl(var(--secondary))] '
    'file:text-[hsl(var(--secondary-foreground))] hover:file:bg-[hsl(var(--accent))]'
)

class BaseStyleForm(forms.ModelForm):
    """Base form class with common styling functionality"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_base_styles()

    def apply_base_styles(self):
        for field in self.fields.values():
            if isinstance(field.widget, (forms.ClearableFileInput, forms.FileInput)):
                field.widget.attrs.update({'class': FILE_UPLOAD_CLASSES})
            else:
                field.widget.attrs.update({'class': BASE_FIELD_CLASSES})

class BaseOrderItemForm(BaseStyleForm):
    """Base form for order items with common functionality"""
    display_total = forms.DecimalField(
        label='Total',
        disabled=True,
        required=False,
        widget=forms.NumberInput(attrs={'class': BASE_FIELD_CLASSES, 'readonly': True})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['display_total'].initial = getattr(self.instance, 'total', 0)

class CustomerVendorForm(BaseStyleForm):
    class Meta:
        model = CustomerVendor
        fields = ['name', 'email', 'phone_number', 'entity_type', 'address']

class SalesEmployeeForm(BaseStyleForm):
    class Meta:
        model = SalesEmployee
        exclude = ['user', 'owner']
        widgets = {
            'date_of_joining': forms.DateInput(attrs={'type': 'date'}),
            'sales_target': forms.NumberInput(attrs={'step': '0.01'}),
            'sales_achieved': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].widget.attrs.update({'class': 'ml-2'})

class ProductForm(BaseStyleForm):
    class Meta:
        model = Product
        fields = ['sku', 'name', 'description', 'category', 'stock_quantity', 'price', 'discount_amount', 'reorder_level', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter product description...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_field_placeholders()
        if not self.instance.pk:
            self.fields['sku'].initial = self.generate_unique_sku()

    def set_field_placeholders(self):
        placeholders = {
            'sku': 'Enter SKU',
            'name': 'Enter product name',
            'stock_quantity': 'Enter stock quantity',
            'price': 'Enter product price',
            'reorder_level': 'Enter reorder level',
            'discount_amount': 'Enter discount amount',
        }
        for field_name, placeholder in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['placeholder'] = placeholder

    @staticmethod
    def generate_unique_sku():
        while True:
            unique_sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"
            if not Product.objects.filter(sku=unique_sku).exists():
                return unique_sku

    def clean(self):
        cleaned_data = super().clean()
        stock_quantity = cleaned_data.get('stock_quantity')
        reorder_level = cleaned_data.get('reorder_level')
        return cleaned_data

class SalesOrderForm(forms.ModelForm):
    order_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-input',
            },
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'],
    )
    
    discount = forms.DecimalField(
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        })
    )
    
    shipping = forms.DecimalField(
        required=False,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        })
    )
    
    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount is None or discount == '':
            return Decimal('0.00')
        return discount
    
    def clean_shipping(self):
        shipping = self.cleaned_data.get('shipping')
        if shipping is None or shipping == '':
            return Decimal('0.00')
        return shipping

    class Meta:
        model = SalesOrder
        fields = ['customer', 'sales_employee', 'delivery_status', 'order_date', 'discount', 'shipping', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = CustomerVendor.objects.filter(entity_type='customer').order_by('name')
        self.fields['sales_employee'].queryset = SalesEmployee.objects.all().order_by('full_name')
        if self.instance.order_date:
            self.fields['order_date'].initial = self.instance.order_date.strftime('%Y-%m-%d')
        else:
            self.fields['order_date'].initial = timezone.now().strftime('%Y-%m-%d')
class CustomSelectWithSKU(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option['attrs']['sku'] = value.instance.sku
        return option
    
class SalesOrderItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.all().order_by('name'),
        widget=CustomSelectWithSKU(attrs={'class': 'form-select'})
    )
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-input'}))
    unit_price = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'form-input'}))
    stock_quantity = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-input', 'readonly': 'readonly'}))
    display_total = forms.DecimalField(max_digits=10, decimal_places=2, required=False, widget=forms.NumberInput(attrs={'class': 'form-input', 'readonly': 'readonly'}))
    total_discount = forms.DecimalField(max_digits=10, decimal_places=2, required=False, widget=forms.NumberInput(attrs={'class': 'form-input', 'readonly': 'readonly'}))
    class Meta:
        model = SalesOrderItem
        fields = ['product', 'quantity', 'unit_price', 'stock_quantity', 'display_total', 'total_discount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].label_from_instance = lambda obj: f"{obj.name} - {obj.sku}"

    def clean_product(self):
        product = self.cleaned_data.get('product')
        if product:
            try:
                # Ensure the product ID is a valid UUID
                uuid.UUID(str(product.id))
            except (ValueError, AttributeError):
                raise ValidationError("Invalid product selection")
        return product

    def clean_unit_price(self):
        unit_price = self.cleaned_data.get('unit_price')
        try:
            return Decimal(str(unit_price)).quantize(Decimal('0.01'))
        except InvalidOperation:
            raise ValidationError("Invalid unit price. Please enter a valid number.")

    def clean_display_total(self):
        display_total = self.cleaned_data.get('display_total')
        if display_total is not None:
            try:
                return Decimal(str(display_total)).quantize(Decimal('0.01'))
            except InvalidOperation:
                raise ValidationError("Invalid total. Please enter a valid number.")
        return display_total




class ARInvoiceForm(BaseStyleForm):
    class Meta:
        model = ARInvoice
        fields = ['customer', 'sales_employee', 'sales_order','payment_status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = CustomerVendor.objects.filter(entity_type='customer')

class ARInvoiceItemForm(BaseOrderItemForm):
    class Meta:
        model = ARInvoiceItem
        fields = ['product', 'quantity', 'unit_price']

def get_ar_invoice_item_formset(extra=1, min_num=1, **kwargs):
    return forms.inlineformset_factory(
        ARInvoice,
        ARInvoiceItem,
        form=ARInvoiceItemForm,
        extra=extra,
        min_num=min_num,
        validate_min=True,
        can_delete=True,
        fields=['product', 'quantity', 'unit_price'],
        widgets={
            'product': forms.Select(attrs={'class': BASE_FIELD_CLASSES}),
            'quantity': forms.NumberInput(attrs={'class': BASE_FIELD_CLASSES, 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': BASE_FIELD_CLASSES, 'step': '0.01'}),
        },
        **kwargs
    )

ARInvoiceItemFormSet = get_ar_invoice_item_formset()

class PurchaseOrderForm(BaseStyleForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier','delivery_status']

class PurchaseOrderItemForm(BaseOrderItemForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_price']

# Form factories
SalesOrderItemFormSet = forms.inlineformset_factory(
    SalesOrder, SalesOrderItem, form=SalesOrderItemForm,
    extra=1, can_delete=True
)



PurchaseOrderItemFormSet = forms.inlineformset_factory(
    PurchaseOrder, PurchaseOrderItem, form=PurchaseOrderItemForm,
    extra=1, can_delete=True
)


class AddStockForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={
                'class': BASE_FIELD_CLASSES,  # Using the global base field classes for consistency
            }),
            'quantity': forms.NumberInput(attrs={
                'class': BASE_FIELD_CLASSES,  # Using the global base field classes for consistency
                'min': '0'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].empty_label = "Select Product"

AddStockFormSet = forms.modelformset_factory(
    StockTransaction,
    form=AddStockForm,
    extra=1,
    can_delete=True
)

from .models import MaterialsPurchase, MaterialsPurchaseItem

class MaterialsPurchaseForm(forms.ModelForm):
    class Meta:
        model = MaterialsPurchase
        fields = ['vendor_name', 'purchase_date']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
        }

class MaterialsPurchaseItemForm(forms.ModelForm):
    class Meta:
        model = MaterialsPurchaseItem
        fields = ['product_name', 'unit_price', 'quantity']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-input'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': '1'}),
        }

MaterialsPurchaseItemFormSet = forms.inlineformset_factory(
    MaterialsPurchase,
    MaterialsPurchaseItem,
    form=MaterialsPurchaseItemForm,
    extra=1,
    can_delete=True
)

# Return Sales
from django.db.models import Sum

class ReturnSalesForm(forms.ModelForm):
    return_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-input',
            },
            format='%Y-%m-%d'
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'],
    )
    
    class Meta:
        model = ReturnSales
        fields = ['return_employee', 'return_date']

    def clean(self):
        cleaned_data = super().clean()
        return_employee = cleaned_data.get('return_employee')
        
        if not return_employee:
            self.add_error('return_employee', 'A return employee must be selected.')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['return_employee'].queryset = SalesEmployee.objects.all().order_by('full_name')
        if self.instance.return_date:
            self.fields['return_date'].initial = self.instance.return_date.strftime('%Y-%m-%d')
        else:
            self.fields['return_date'].initial = timezone.now().strftime('%Y-%m-%d')


class ReturnSalesItemForm(forms.ModelForm):
    max_returnable = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-input', 'readonly': 'readonly'}), required=False)
    display_total = forms.DecimalField(max_digits=10, decimal_places=2, required=False, widget=forms.NumberInput(attrs={'class': 'form-input', 'readonly': 'readonly'}))
    product_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-input', 'readonly': 'readonly'}), required=False)
    
    class Meta:
        model = ReturnSalesItem
        fields = ['sales_order_item', 'quantity', 'unit_price', 'max_returnable', 'display_total', 'product_name']
        widgets = {
            'sales_order_item': forms.HiddenInput(),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),  # Changed min to 0
            'unit_price': forms.NumberInput(attrs={'class': 'form-input', 'readonly': 'readonly'}),
        }
    
    def __init__(self, *args, **kwargs):
        sales_order = kwargs.pop('sales_order', None)
        super().__init__(*args, **kwargs)
        
        if sales_order:
            self.fields['sales_order_item'].queryset = SalesOrderItem.objects.filter(sales_order=sales_order)
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        sales_order_item = self.cleaned_data.get('sales_order_item')
        
        if not sales_order_item:
            return quantity
        
        if quantity is None:
            quantity = 0
            
        # If quantity is 0, no need to validate further
        if quantity == 0:
            return quantity
            
        # Calculate max returnable quantity
        previously_returned = ReturnSalesItem.objects.filter(
            sales_order_item=sales_order_item
        ).exclude(id=self.instance.id if self.instance.id else None).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        max_returnable = sales_order_item.quantity - previously_returned
        
        if quantity > max_returnable:
            raise ValidationError(("Return quantity exceeds available quantity. Maximum returnable: %(max)d") % {
                'max': max_returnable
            })
        
        return quantity
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Calculate the total value before saving
        if instance.quantity and instance.unit_price:
            instance.total = Decimal(instance.quantity) * instance.unit_price
        else:
            instance.total = Decimal('0.00')
            
        if commit:
            instance.save()
        return instance

ReturnSalesItemFormSet = forms.inlineformset_factory(
    ReturnSales,
    ReturnSalesItem,
    form=ReturnSalesItemForm,
    extra=0,
    can_delete=True,
    min_num=0, 
    validate_min=False
)


def get_return_sales_item_formset(sales_order=None, **kwargs):
    # Count the number of items in the sales order
    item_count = 0
    if sales_order:
        item_count = sales_order.order_items.count()
    
    # Create the formset with the appropriate number of forms
    return forms.inlineformset_factory(
        ReturnSales,
        ReturnSalesItem,
        form=ReturnSalesItemForm,
        extra=item_count,  # Dynamic extra based on order items
        can_delete=True,
        min_num=0,
        validate_min=False
    )(**kwargs)