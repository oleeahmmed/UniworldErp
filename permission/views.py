from django.contrib.auth.models import Permission, Group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
import json
from django.http import Http404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required



from django.contrib.auth import login, authenticate,get_backends
from .forms import LoginForm, RegistrationForm

def user_permissions_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Check if the logged-in user is a superuser or has the "Can change permission" permission
    can_change_permission = request.user.is_superuser or request.user.has_perm('auth.change_permission')

    if request.method == 'POST' and can_change_permission:
        # Update user permissions
        assigned_permissions = request.POST.get('assigned_permissions')
        if assigned_permissions:
            permission_ids = json.loads(assigned_permissions)
            user.user_permissions.set(permission_ids)

        # Update user groups
        assigned_groups = request.POST.get('assigned_groups')
        if assigned_groups:
            group_ids = json.loads(assigned_groups)
            user.groups.set(group_ids)

    # Fetch permissions
    all_permissions = Permission.objects.select_related('content_type')
    user_permissions = user.user_permissions.all()
    available_permissions = all_permissions.exclude(id__in=user_permissions.values_list('id', flat=True))

    # Fetch groups
    all_groups = Group.objects.all()
    user_groups = user.groups.all()
    available_groups = all_groups.exclude(id__in=user_groups.values_list('id', flat=True))

    # Format permissions
    def format_permission(permission):
        return {
            'id': permission.id,
            'name': f"{permission.content_type.app_label} | {permission.content_type.model} | {permission.name}"
        }

    formatted_available_permissions = [format_permission(p) for p in available_permissions]
    formatted_user_permissions = [format_permission(p) for p in user_permissions]

    context = {
        'user': user,
        'available_permissions': formatted_available_permissions,
        'assigned_permissions': formatted_user_permissions,
        'available_groups': available_groups,
        'assigned_groups': user_groups,
        'can_change_permission': can_change_permission,
    }
    return render(request, 'permissions.html', context)


def group_permissions_view(request, group_id):
    try:
        # Try to get the group, if it doesn't exist, return a 404 error
        group = get_object_or_404(Group, id=group_id)
    except Http404:
        # If the group does not exist, show a message and redirect back
        messages.error(request, "The group you are looking for does not exist.")
        return redirect('group_list')  # Replace 'group_list' with your actual group list URL name

    # Check if the logged-in user is a superuser or has the "Can change permission" permission
    can_change_permission = request.user.is_superuser or request.user.has_perm('auth.change_permission')

    if request.method == 'POST' and can_change_permission:
        # Update group permissions
        assigned_permissions = request.POST.get('assigned_permissions')
        if assigned_permissions:
            permission_ids = json.loads(assigned_permissions)
            group.permissions.set(permission_ids)

    # Fetch all permissions for display
    all_permissions = Permission.objects.select_related('content_type')
    group_permissions = group.permissions.all()

    # Filter available permissions
    available_permissions = all_permissions.exclude(id__in=group_permissions.values_list('id', flat=True))

    # Format permissions
    def format_permission(permission):
        return {
            'id': permission.id,
            'name': f"{permission.content_type.app_label} | {permission.content_type.model} | {permission.name}"
        }

    formatted_available_permissions = [format_permission(p) for p in available_permissions]
    formatted_group_permissions = [format_permission(p) for p in group_permissions]

    context = {
        'group': group,
        'available_permissions': formatted_available_permissions,
        'assigned_permissions': formatted_group_permissions,
        'can_change_permission': can_change_permission,
    }

    return render(request, 'group_permissions.html', context)

from django.urls import reverse_lazy
from django.contrib.auth.models import User, Group
from django.views.generic import ListView, CreateView, UpdateView,DeleteView
from .forms import UserForm, GroupForm  
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
# Class-based Views for User
class UserListView(PermissionRequiredMixin,ListView):
    model = User
    template_name = 'user/userlist.html'
    context_object_name = 'users'
    permission_required = 'auth.view_user'
class UserCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'form.html'
    success_url = reverse_lazy('permission:user_list')
    permission_required = 'auth.add_user'

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.change_user')  # Check if user has permission to change users
        return context

    def form_valid(self, form):
        """
        Process the valid form data and set the password for the new user.
        """
        user = form.save(commit=False)

        # Set the password if provided
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        # Save the user to the database
        user.save()

        messages.success(self.request, "User created successfully.")
        return super().form_valid(form)

class UserUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'form.html'
    success_url = reverse_lazy('permission:user_list')
    permission_required = 'auth.change_user'

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.change_user')  # Check if user has permission to change users
        return context

    def form_valid(self, form):
        """
        Process the valid form data and update the user's password if provided.
        """
        user = form.save(commit=False)

        # Update the password if provided
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        user.save()

        messages.success(self.request, "User updated successfully.")
        return super().form_valid(form)

class UserDeleteView(PermissionRequiredMixin, SuccessMessageMixin,DeleteView):
    model = User
    template_name = 'confirm_delete.html'
    success_url =  reverse_lazy('permission:user_list') 
    success_message = "User deleted successfully!"
    permission_required = 'auth.delete_user'  
    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form, making it dynamic for any model.
        """
        context = super().get_context_data(**kwargs)
        
        # Dynamically get model name
        model_name = self.model._meta.verbose_name.title()
        context['model_name'] = model_name
        
        # Add the object name dynamically based on the model
        context['object_name'] = str(self.object)

        # Dynamically check if the user has permission for this action
        context['can_delete'] = self.request.user.has_perm('auth.delete_user')
        # Add dynamic cancel URL based on the model
        context['cancel_url'] = self.get_cancel_url()

        return context

    def get_cancel_url(self):
        """
        Returns the URL to redirect to when the user cancels the deletion.
        The URL depends on the model being used.
        """
        model_name = self.model._meta.model_name
        return reverse_lazy(f'permission:user_list')
# Class-based Views for Group
class GroupListView(ListView):
    model = Group
    template_name = 'group/grouplist.html'
    context_object_name = 'groups'
    paginate_by = 10 

# Group Create View
class GroupCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'form.html'
    success_url = reverse_lazy('permission:group_list')  # Redirect after successful creation
    permission_required = 'auth.add_group'  # Permission required for creating a group

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.change_group')  # Check if user has permission to change groups
        return context

# Group Update View
class GroupUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'form.html'
    success_url = reverse_lazy('permission:group_list')  # Redirect after successful update
    permission_required = 'auth.change_group'  # Permission required for updating a group

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.change_group')  # Check if user has permission to change groups
        return context

# Group Delete View
class GroupDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Group
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('permission:group_list')  # Redirect after successful deletion
    success_message = "Group deleted successfully!"
    permission_required = 'auth.delete_group'  # Permission required for deleting a group

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form, making it dynamic for any model.
        """
        context = super().get_context_data(**kwargs)
        
        # Dynamically get model name
        model_name = self.model._meta.verbose_name.title()
        context['model_name'] = model_name
        
        # Add the object name dynamically based on the model
        context['object_name'] = str(self.object)

        # Dynamically check if the user has permission for this action
        context['can_delete'] = self.request.user.has_perm('auth.delete_group')
        
        # Add dynamic cancel URL based on the model
        context['cancel_url'] = self.success_url  # Corrected: Removed parentheses

        return context

    def get_cancel_url(self):
        """
        Returns the URL to redirect to when the user cancels the deletion.
        The URL depends on the model being used.
        """
        model_name = self.model._meta.model_name
        return reverse_lazy(f'{model_name}_list')


from .forms import PermissionForm



class PermissionListView(ListView):
    model = Permission
    template_name = 'permission/permission_list.html'
    context_object_name = 'permissions'
    paginate_by = 10

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        if search_query:
            return Permission.objects.filter(name__icontains=search_query)
        return Permission.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class PermissionCreateView(PermissionRequiredMixin, CreateView):
    model = Permission
    form_class = PermissionForm 
    template_name = 'form.html'  
    success_url = reverse_lazy('permission:permission_list') 
    permission_required = 'auth.add_permission' 
    
    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Get model name dynamically
        context['can_edit'] = self.request.user.has_perm('auth.add_permission')  # Check if user has permission to change users

        return context    
class PermissionUpdateView(PermissionRequiredMixin, UpdateView):
    model = Permission
    form_class = PermissionForm  # Use the custom PermissionForm instead of 'fields'
    template_name = 'form.html'  # Your template for the form
    success_url = reverse_lazy('permission:permission_list')  # Redirect after successful update
    permission_required = 'auth.change_permission'  # Required permission for this view

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form.
        """
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()  # Pass model name to template
        context['can_edit'] = self.request.user.has_perm('auth.change_permission')  # Check if user has permission to change groups
        return context

class PermissionDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Permission
    template_name = 'confirm_delete.html'  
    success_url = reverse_lazy('permission:permission_list')  
    success_message = "Permission deleted successfully!"
    permission_required = 'auth.delete_permission'  

    def handle_no_permission(self):
        """
        If the user does not have permission, display a message and redirect.
        """
        messages.error(self.request, "You do not have permission to perform this action.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        """
        Add additional context data for the form, making it dynamic for any model.
        """
        context = super().get_context_data(**kwargs)
        
        # Dynamically get model name
        model_name = self.model._meta.verbose_name.title()
        context['model_name'] = model_name
        
        # Add the object name dynamically based on the model
        context['object_name'] = str(self.object)

        # Dynamically check if the user has permission for this action
        context['can_delete'] = self.request.user.has_perm('auth.delete_permission')
        
        # Add dynamic cancel URL based on the model
        context['cancel_url'] = self.success_url  # Corrected: Removed parentheses

        return context

    def get_cancel_url(self):
        """
        Returns the URL to redirect to when the user cancels the deletion.
        The URL depends on the model being used.
        """
        model_name = self.model._meta.model_name
        return reverse_lazy(f'{model_name}_list')     
    
    

def login_view(request):
    if request.user.is_authenticated:  # Redirect authenticated users
        return redirect('permission:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Authenticate the user
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.username}!")
                    return redirect('permission:dashboard')
                else:
                    messages.error(request, "This account is inactive.")
            else:
                # Handle invalid credentials
                messages.error(request, "Incorrect username or password.")
        else:
            # If form is invalid, show errors
            messages.error(request, "Please correct the errors below.")
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Explicitly set the backend for the user
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")  # Success message
            return redirect('permission:dashboard')
        else:
            messages.error(request, "There was an error with your registration.")  # Error message
    else:
        form = RegistrationForm()
    return render(request, 'auth/register.html', {'form': form})
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('permission:login')

import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models, OperationalError
from django.db.models import Sum, Count, F, Q, Avg, DecimalField
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging

from django.contrib.auth.models import User
from uniworlderp.models import (
    CustomerVendor, SalesEmployee, Product, SalesOrder, SalesOrderItem,
    PurchaseOrder, ARInvoice, StockTransaction
)

logger = logging.getLogger(__name__)

class ProductEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Product):
            return {
                'id': str(obj.id),
                'name': obj.name,
                'stock_quantity': obj.stock_quantity,
                'price': float(obj.price) if obj.price is not None else None,
                'category': obj.category,
                'revenue': float(obj.revenue) if hasattr(obj, 'revenue') and obj.revenue is not None else None,
            }
        return super().default(obj)

class ChartJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, Product):
            return {
                'id': str(obj.id),
                'name': obj.name,
                'revenue': float(obj.revenue) if hasattr(obj, 'revenue') and obj.revenue is not None else 0
            }
        return super().default(obj)

@login_required
def dashboard_view(request):
    context = {}
    try:
        user = request.user
        current_date = timezone.now()
        start_of_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = current_date - timedelta(days=30)
        seven_days_ago = current_date - timedelta(days=7)
        start_of_year = current_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # User counts
        context['user'] = user
        context['total_users'] = User.objects.count()
        context['total_customers'] = CustomerVendor.objects.filter(entity_type='customer').count()
        context['total_vendors'] = CustomerVendor.objects.filter(entity_type='vendor').count()
        context['new_customers'] = CustomerVendor.objects.filter(entity_type='customer', created_at__gte=thirty_days_ago).count()

        # Sales Employee data
        context['sales_employees'] = SalesEmployee.objects.annotate(
            achievement_percentage=F('sales_achieved') / F('sales_target') * 100
        ).order_by('-achievement_percentage')[:5]

        # Product data
        context['total_products'] = Product.objects.count()
        context['low_stock_products'] = Product.objects.filter(stock_quantity__lte=F('reorder_level')).count()
        context['out_of_stock_products'] = Product.objects.filter(stock_quantity=0).count()

        # Sales Order data
        context['total_sales_orders'] = SalesOrder.objects.count()
        context['recent_sales_orders'] = SalesOrder.objects.select_related('customer').order_by('-order_date')[:10]
        context['current_month_sales'] = SalesOrder.objects.filter(order_date__gte=start_of_month).aggregate(
            total_value=Sum('total_amount')
        )['total_value'] or 0

        # Top selling products
        context['top_selling_products'] = Product.objects.annotate(
            total_sold=Sum('salesorderitem__quantity')
        ).order_by('-total_sold')[:5]

        # Purchase Order data
        context['total_purchase_orders'] = PurchaseOrder.objects.count()
        context['current_month_purchases'] = PurchaseOrder.objects.filter(order_date__gte=start_of_month).aggregate(
            total_value=Sum('total_amount')
        )['total_value'] or 0

        # AR Invoice data
        context['total_ar_invoices'] = ARInvoice.objects.count()
        context['pending_invoices'] = ARInvoice.objects.filter(payment_status='P').count()
        context['overdue_invoices'] = ARInvoice.objects.filter(due_date__lt=current_date, payment_status='P').count()

        # Stock Transaction data
        context['recent_stock_transactions'] = StockTransaction.objects.select_related('product').order_by('-transaction_date')[:10]

        # Monthly Sales Data (Line Chart)
        monthly_sales = list(SalesOrder.objects.filter(
            order_date__gte=start_of_year
        ).annotate(
            month=TruncMonth('order_date')
        ).values('month').annotate(
            total_sales=Sum('total_amount')
        ).order_by('month'))
        context['monthly_sales'] = json.dumps(monthly_sales, cls=ChartJSONEncoder)

        # Revenue Breakdown (Bar Chart)
        revenue_breakdown = list(Product.objects.annotate(
            revenue=Sum(F('salesorderitem__quantity') * F('salesorderitem__unit_price'))
        ).order_by('-revenue')[:5])
        context['revenue_breakdown'] = json.dumps(revenue_breakdown, cls=ChartJSONEncoder)

        # Top Sales Categories (Pie Chart)
        top_categories = list(Product.objects.values('category').annotate(
            total_sales=Sum(F('salesorderitem__quantity') * F('salesorderitem__unit_price'))
        ).order_by('-total_sales')[:5])
        context['top_categories'] = json.dumps(top_categories, cls=ChartJSONEncoder)

        # Sales Trend (Last 7 Days)
        sales_trend = list(SalesOrder.objects.filter(
            order_date__gte=seven_days_ago
        ).annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            daily_sales=Sum('total_amount')
        ).order_by('date'))
        context['sales_trend'] = json.dumps(sales_trend, cls=ChartJSONEncoder)

        # Additional metrics
        context['average_order_value'] = SalesOrder.objects.filter(order_date__gte=thirty_days_ago).aggregate(
            avg_value=Avg('total_amount')
        )['avg_value'] or 0

        context['customer_retention_rate'] = calculate_customer_retention_rate(thirty_days_ago)

        context['top_customers'] = CustomerVendor.objects.filter(entity_type='customer').annotate(
            total_purchases=Sum('sales_orders__total_amount')
        ).order_by('-total_purchases')[:5]

        context['inventory_turnover'] = calculate_inventory_turnover(thirty_days_ago)

    except OperationalError as e:
        logger.error(f"OperationalError in dashboard_view: {str(e)}")
        context['error'] = "An error occurred while fetching dashboard data. Please try again later."
    except Exception as e:
        logger.error(f"Unexpected error in dashboard_view: {str(e)}")
        context['error'] = "An unexpected error occurred. Please try again later."

    return render(request, 'auth/dashboard.html', context)

def calculate_customer_retention_rate(start_date):
    total_customers = CustomerVendor.objects.filter(entity_type='customer', created_at__lt=start_date).count()
    retained_customers = CustomerVendor.objects.filter(
        entity_type='customer',
        created_at__lt=start_date,
        sales_orders__order_date__gte=start_date
    ).distinct().count()
    
    return (retained_customers / total_customers * 100) if total_customers > 0 else 0

def calculate_inventory_turnover(start_date):
    cost_of_goods_sold = SalesOrderItem.objects.filter(
        sales_order__order_date__gte=start_date
    ).aggregate(total=Sum(F('quantity') * F('unit_price'), output_field=DecimalField()))['total'] or 0

    average_inventory = Product.objects.aggregate(
        avg_inventory=Avg(F('stock_quantity') * F('price'), output_field=DecimalField())
    )['avg_inventory'] or 1

    return cost_of_goods_sold / average_inventory


