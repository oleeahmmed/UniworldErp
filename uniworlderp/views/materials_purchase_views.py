from decimal import Decimal
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, F
from django.urls import reverse_lazy
from uniworlderp.models import MaterialsPurchase, MaterialsPurchaseItem
from uniworlderp.forms import MaterialsPurchaseForm, MaterialsPurchaseItemFormSet

class MaterialsPurchaseListView(ListView):
    model = MaterialsPurchase
    template_name = 'materials_purchase/list.html'
    context_object_name = 'purchases'
    paginate_by = 20

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        queryset = MaterialsPurchase.objects.all().order_by('-purchase_date')

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) |
                Q(vendor_name__icontains=search_query) |
                Q(purchase_date__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context

class MaterialsPurchaseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = MaterialsPurchase
    form_class = MaterialsPurchaseForm
    template_name = 'materials_purchase/form.html'
    success_url = reverse_lazy('customer_vendor:materials_purchase_list')
    permission_required = 'add_materialspurchase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = MaterialsPurchaseItemFormSet(self.request.POST)
        else:
            context['formset'] = MaterialsPurchaseItemFormSet()
        context.update(self.get_common_context())
        context['action'] = 'Add'
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    self.object = form.save(commit=False)
                    self.object.owner = self.request.user
                    self.object.save()
                    formset.instance = self.object
                    formset.save()
                    self.object.total_amount = sum(item.total_price for item in self.object.items.all())
                    self.object.save()
                messages.success(self.request, 'Materials Purchase created successfully.')
                return super().form_valid(form)
            except Exception as e:
                messages.error(self.request, f'Error creating Materials Purchase: {str(e)}')
                return self.form_invalid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(self.request, f"{field}: {error}")
        if not formset.is_valid():
            for i, form_errors in enumerate(formset.errors):
                if form_errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(self.request, f"Item {i+1} - {field}: {error}")
        return super().form_invalid(form)

    def get_common_context(self):
        purchases = MaterialsPurchase.objects.all().order_by('-purchase_date')
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('add_materialspurchase'),
            'can_edit': self.request.user.has_perm('change_materialspurchase'),
            'can_view': self.request.user.has_perm('view_materialspurchase'),
            'list_url': reverse_lazy('customer_vendor:materials_purchase_list'),
            'create_url': reverse_lazy('customer_vendor:materials_purchase_create'),
            'edit_url_name': 'customer_vendor:materials_purchase_update',
            'view_url_name': 'customer_vendor:materials_purchase_view',
            'print_url_name': 'customer_vendor:materials_purchase_print',
            'search_url': reverse_lazy('customer_vendor:materials_purchase_list'),
            'first_id': purchases.first().id if purchases.exists() else None,
            'last_id': purchases.last().id if purchases.exists() else None,
            'prev_id': None,
            'next_id': None,
            'current_id': None,
        }

class MaterialsPurchaseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = MaterialsPurchase
    form_class = MaterialsPurchaseForm
    template_name = 'materials_purchase/form.html'
    success_url = reverse_lazy('customer_vendor:materials_purchase_list')
    permission_required = 'change_materialspurchase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = MaterialsPurchaseItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = MaterialsPurchaseItemFormSet(instance=self.object)
        context.update(self.get_common_context())
        context['action'] = 'Edit'
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            self.object.total_amount = sum(item.total_price for item in self.object.items.all())
            self.object.save()
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def get_common_context(self):
        purchases = MaterialsPurchase.objects.all().order_by('-purchase_date')
        current_purchase = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('add_materialspurchase'),
            'can_edit': self.request.user.has_perm('change_materialspurchase'),
            'can_view': self.request.user.has_perm('view_materialspurchase'),
            'list_url': reverse_lazy('customer_vendor:materials_purchase_list'),
            'create_url': reverse_lazy('customer_vendor:materials_purchase_create'),
            'edit_url_name': 'customer_vendor:materials_purchase_update',
            'view_url_name': 'customer_vendor:materials_purchase_view',
            'print_url_name': 'customer_vendor:materials_purchase_print',
            'search_url': reverse_lazy('customer_vendor:materials_purchase_list'),
            'first_id': purchases.first().id if purchases.exists() else None,
            'last_id': purchases.last().id if purchases.exists() else None,
            'prev_id': purchases.filter(purchase_date__lt=current_purchase.purchase_date).last().id if purchases.filter(purchase_date__lt=current_purchase.purchase_date).exists() else None,
            'next_id': purchases.filter(purchase_date__gt=current_purchase.purchase_date).first().id if purchases.filter(purchase_date__gt=current_purchase.purchase_date).exists() else None,
            'current_id': current_purchase.id,
        }

class MaterialsPurchaseDetailView(PermissionRequiredMixin, DetailView):
    model = MaterialsPurchase
    template_name = 'materials_purchase/form.html'
    permission_required = 'view_materialspurchase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['action'] = 'View'
        context['form'] = MaterialsPurchaseForm(instance=self.object)
        context['formset'] = MaterialsPurchaseItemFormSet(instance=self.object)
        for form in context['formset']:
            for field in form.fields.values():
                field.widget.attrs['disabled'] = 'disabled'
        for field in context['form'].fields.values():
            field.widget.attrs['disabled'] = 'disabled'
        return context

    def get_common_context(self):
        purchases = MaterialsPurchase.objects.all().order_by('-purchase_date')
        current_purchase = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('add_materialspurchase'),
            'can_edit': self.request.user.has_perm('change_materialspurchase'),
            'can_view': self.request.user.has_perm('view_materialspurchase'),
            'list_url': reverse_lazy('customer_vendor:materials_purchase_list'),
            'create_url': reverse_lazy('customer_vendor:materials_purchase_create'),
            'edit_url_name': 'customer_vendor:materials_purchase_update',
            'view_url_name': 'customer_vendor:materials_purchase_view',
            'print_url_name': 'customer_vendor:materials_purchase_print',
            'first_id': purchases.first().id if purchases.exists() else None,
            'last_id': purchases.last().id if purchases.exists() else None,
            'prev_id': purchases.filter(purchase_date__lt=current_purchase.purchase_date).last().id if purchases.filter(purchase_date__lt=current_purchase.purchase_date).exists() else None,
            'next_id': purchases.filter(purchase_date__gt=current_purchase.purchase_date).first().id if purchases.filter(purchase_date__gt=current_purchase.purchase_date).exists() else None,
            'current_id': current_purchase.id,
        }

class MaterialsPurchaseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = MaterialsPurchase
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('customer_vendor:materials_purchase_list')
    success_message = "Materials purchase deleted successfully!"
    permission_required = 'delete_materialspurchase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['cancel_url'] = reverse_lazy('customer_vendor:materials_purchase_list')
        return context

class MaterialsPurchasePrintView(LoginRequiredMixin, DetailView):
    model = MaterialsPurchase
    template_name = 'materials_purchase/print.html'
    context_object_name = 'purchase'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = self.object.items.all()
        subtotal = sum(item.total_price for item in items)
        tax = subtotal * Decimal('0.0')  # 0% tax, adjust as needed
        total = subtotal + tax

        context.update({
            'items': items,
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
        })
        return context

from django.views.generic import TemplateView
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncMonth
class MaterialsPurchaseReportView(TemplateView):
    template_name = 'materials_purchase/report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Top 5 products by purchase amount
        context['top_products'] = MaterialsPurchaseItem.objects.values('product_name')\
            .annotate(total_amount=Sum('total_price'), quantity=Sum('quantity'))\
            .order_by('-total_amount')[:5]

        # Top 5 vendors by purchase amount
        context['top_vendors'] = MaterialsPurchase.objects.values('vendor_name')\
            .annotate(total_amount=Sum('total_amount'), purchase_count=Count('id'))\
            .order_by('-total_amount')[:5]

        # Last 30 days purchases
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        context['recent_purchases'] = MaterialsPurchase.objects.filter(purchase_date__gte=thirty_days_ago)\
            .order_by('-purchase_date')

        # Monthly purchase amounts for the last 12 months
        twelve_months_ago = timezone.now().date() - timedelta(days=365)
        monthly_purchases = MaterialsPurchase.objects.filter(purchase_date__gte=twelve_months_ago)\
            .annotate(month=TruncMonth('purchase_date'))\
            .values('month')\
            .annotate(total_amount=Sum('total_amount'))\
            .order_by('month')
        
        context['monthly_purchases'] = monthly_purchases

        return context
