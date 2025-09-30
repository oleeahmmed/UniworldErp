from .common_imports import *
from company.models import Company
from uniworlderp.models import StockTransaction, Product, SalesOrder, CustomerVendor, SalesEmployee
from uniworlderp.forms import ProductForm
from uuid import UUID

class ProductListView(ListView):
    model = Product
    template_name = 'product/list.html'
    context_object_name = 'products'
    paginate_by = 50

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        queryset = Product.objects.all().order_by('name')  # Ensure alphabetical ordering

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            ).order_by('name')  # Maintain alphabetical ordering after search

        # Annotate stock status
        queryset = queryset.annotate(
            need_reorder=Case(
                When(stock_quantity__lt=F('reorder_level'), then=Value(True)),
                default=Value(False)
            ),
        )
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['entity_type'] = self.request.GET.get('entity_type', '')
        context['verbose_name'] = self.model._meta.verbose_name_plural
        context['urls'] = {
            'add': 'customer_vendor:product_create',
            'add_stock': 'customer_vendor:add_stock',
            'view_stock_transfer': 'customer_vendor:stock_transfer_detailed_list',

        }
        return context        

class ProductCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('customer_vendor:product_list')
    success_message = "Product added successfully!"
    permission_required = 'uniworlderp.add_product'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to add a product.")
        return redirect('customer_vendor:product_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = self.request.user.has_perm('uniworlderp.add_product')
        context['can_edit'] = False
        context['can_view'] = False
        return context

    def get_common_context(self):
        products = Product.objects.all().order_by('name')  # Alphabetical ordering
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': reverse_lazy('customer_vendor:product_list'),
            'create_url': reverse_lazy('customer_vendor:product_create'),
            'edit_url_name': 'customer_vendor:product_edit',
            'view_url_name': 'customer_vendor:product_view',
            'print_url_name': 'customer_vendor:product_print',
            'first_id': products.first().id if products.exists() else None,
            'last_id': products.last().id if products.exists() else None,
            'prev_id': None,
            'next_id': None,
            'current_id': None,
        }

class ProductUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'common/form.html'
    success_url = reverse_lazy('customer_vendor:product_list')
    success_message = "Product updated successfully!"
    permission_required = 'uniworlderp.change_product'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to edit this product.")
        return redirect('customer_vendor:product_list')

    def form_valid(self, form):
        if not form.instance.owner:
            form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = False
        context['can_edit'] = self.request.user.has_perm('uniworlderp.change_product')
        context['can_view'] = False
        return context

    def get_common_context(self):
        products = Product.objects.all().order_by('name')  # Alphabetical ordering
        current_product = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': reverse_lazy('customer_vendor:product_list'),
            'create_url': reverse_lazy('customer_vendor:product_create'),
            'edit_url_name': 'customer_vendor:product_edit',
            'view_url_name': 'customer_vendor:product_view',
            'print_url_name': 'customer_vendor:product_print',
            'first_id': products.first().id if products.exists() else None,
            'last_id': products.last().id if products.exists() else None,
            'prev_id': products.filter(id__lt=current_product.id).last().id if products.filter(id__lt=current_product.id).exists() else None,
            'next_id': products.filter(id__gt=current_product.id).first().id if products.filter(id__gt=current_product.id).exists() else None,
            'current_id': current_product.id,
        }

class ProductDetailView(PermissionRequiredMixin, DetailView):
    model = Product
    template_name = 'common/form.html'
    permission_required = 'uniworlderp.view_product'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to view this product.")
        return redirect('customer_vendor:product_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['can_add'] = False
        context['can_edit'] = False
        context['can_view'] = self.request.user.has_perm('uniworlderp.view_product')
        context['form'] = ProductForm(instance=self.object)
        for field in context['form'].fields.values():
            field.widget.attrs['disabled'] = 'disabled'
        return context

    def get_common_context(self):
        products = Product.objects.all().order_by('name')  # Alphabetical ordering
        current_product = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'list_url': 'customer_vendor:product_list',
            'create_url': reverse_lazy('customer_vendor:product_create'),
            'edit_url_name': 'customer_vendor:product_edit',
            'view_url_name': 'customer_vendor:product_view',
            'print_url_name': 'customer_vendor:product_print',
            'first_id': products.first().id if products.exists() else None,
            'last_id': products.last().id if products.exists() else None,
            'prev_id': products.filter(id__lt=current_product.id).last().id if products.filter(id__lt=current_product.id).exists() else None,
            'next_id': products.filter(id__gt=current_product.id).first().id if products.filter(id__gt=current_product.id).exists() else None,
            'current_id': current_product.id,
        }

class ProductDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Product
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('customer_vendor:product_list')
    success_message = "Product deleted successfully!"
    permission_required = 'uniworlderp.delete_product'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to delete this product.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['object_name'] = str(self.object)
        context['can_delete'] = self.request.user.has_perm(self.permission_required)
        context['cancel_url'] = self.get_cancel_url()
        return context

    def get_cancel_url(self):
        return reverse_lazy('customer_vendor:product_list')

    def get_success_message(self, cleaned_data):
        return self.success_message

class ProductPrintView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'product/print.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = Company.objects.first()  # Assuming you have only one company
        context.update({
            'company': company,
            'model_name': self.model._meta.verbose_name.title(),
        })
        return context

class StockTransactionListView(ListView):
    model = StockTransaction
    template_name = 'product/detailed_list.html'
    context_object_name = 'stock_transactions'

    def get_queryset(self):
        queryset = StockTransaction.objects.prefetch_related(
            'product__salesorderitem_set__sales_order',  # Ensure reverse lookup is correct
            'product__salesorderitem_set__sales_order__customer',  # Correct reverse lookup
            'product__salesorderitem_set__sales_order__sales_employee',  # Correct reverse lookup
        ).all()

        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(product__name__icontains=search_query) |
                Q(reference__icontains=search_query) |
                Q(product__salesorderitem_set__sales_order__customer__name__icontains=search_query) |
                Q(product__salesorderitem_set__sales_order__sales_employee__full_name__icontains=search_query)
            )

        return queryset.order_by('-transaction_date')  # Sorting by transaction date in descending order


from django.http import JsonResponse
from django.db.models import Q
import uuid

def product_search(request):
    query = request.GET.get('q', '')
    if query:
        try:
            # Check if the query is a valid UUID
            product_id = uuid.UUID(query)
            # If it's a UUID, fetch the specific product
            product = Product.objects.filter(id=product_id).values(
                'id', 'name', 'description', 'price', 'stock_quantity', 'reorder_level', 'discount_amount'
            ).first()
            if product:
                # Minimal fix: handle None discount_amount
                if product['discount_amount'] is None:
                    product['discount_amount'] = 0.0
                return JsonResponse([product], safe=False)
        except ValueError:
            # If it's not a UUID, perform a search as before
            products = Product.objects.filter(
                Q(name__icontains=query) | Q(sku__icontains=query)
            ).values(
                'id', 'name', 'description', 'price', 'stock_quantity', 'reorder_level', 'discount_amount'
            )[:10]  # Limit to 10 results for performance
            # Minimal fix: handle None discount_amount in list
            products_list = list(products)
            for product in products_list:
                if product['discount_amount'] is None:
                    product['discount_amount'] = 0.0
            return JsonResponse(products_list, safe=False)
    
    return JsonResponse([], safe=False)



# views.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError


def get_product_info(request):
    sku = request.GET.get('sku')
    
    if not sku:
        return JsonResponse({'error': 'Product SKU is required'}, status=400)

    try:
        product = get_object_or_404(Product, sku=sku)
        
        product_data = {
            'id': str(product.id),  # Convert UUID to string
            'name': product.name,
            'description': product.description,
            'price': float(product.price),
            'stock_quantity': product.stock_quantity,
            'reorder_level': product.reorder_level,
            'discount_amount': float(product.discount_amount) if product.discount_amount is not None else 0.0,

        }
        print(f"Product data: {product_data}")  # Debugging line
        return JsonResponse(product_data)
    except Product.DoesNotExist:
        return JsonResponse({'error': f'No product found with SKU: {sku}'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)



    
    
from django.views.generic import FormView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import transaction
from uniworlderp.forms import AddStockFormSet
from uniworlderp.models import Product, StockTransaction    
class AddStockView(PermissionRequiredMixin, SuccessMessageMixin,FormView):
    template_name = 'product/add_stock.html'
    form_class = AddStockFormSet
    success_url = reverse_lazy('customer_vendor:add_stock')
    success_message = "Product added successfully!"
    permission_required = 'uniworlderp.add_product'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['queryset'] = StockTransaction.objects.none()
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['formset'] = AddStockFormSet(self.request.POST)
        else:
            data['formset'] = AddStockFormSet(queryset=StockTransaction.objects.none())
        return data

    @transaction.atomic
    def form_valid(self, formset):
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                if instance.quantity and instance.quantity > 0:
                    instance.transaction_type = 'IN'
                    instance.owner = self.request.user
                    instance.save()
                   
            return super().form_valid(formset)
        return self.form_invalid(formset)

    def form_invalid(self, formset):
        for form in formset:
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(formset)    