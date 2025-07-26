from .common_imports import *
from uniworlderp.models import ARInvoice, ARInvoiceItem, Product, StockTransaction, SalesEmployee, SalesOrder
from uniworlderp.forms import ARInvoiceForm, ARInvoiceItemFormSet,ARInvoiceItemForm,get_ar_invoice_item_formset
from company.models import Company, Branch, ContactPerson

class ARInvoiceListView(ListView):
    model = ARInvoice
    template_name = 'invoice/list.html'
    context_object_name = 'invoices'
    paginate_by = 100

    def get_queryset(self):
        search_query = self.request.GET.get('search', '')
        queryset = ARInvoice.objects.all().order_by('-invoice_date')

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) |
                Q(customer__name__icontains=search_query) |
                Q(sales_employee__user__username__icontains=search_query) |
                Q(invoice_date__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context
from django.forms import inlineformset_factory

class ARInvoiceCreateView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = ARInvoice
    form_class = ARInvoiceForm
    template_name = 'invoice/form.html'
    success_url = reverse_lazy('customer_vendor:sales_order_list')
    permission_required = 'uniworlderp.add_arinvoice'
    success_message = "Invoice added successfully!"

    def get_initial(self):
        initial = super().get_initial()
        sales_order_id = self.kwargs.get('sales_order_id')
        if sales_order_id:
            try:
                sales_order = get_object_or_404(SalesOrder, id=sales_order_id)
                if ARInvoice.objects.filter(sales_order=sales_order).exists():
                    messages.error(self.request, "An invoice already exists for this sales order.")
                    return {}
                initial.update({
                    'customer': sales_order.customer,
                    'sales_employee': sales_order.sales_employee,
                    'sales_order': sales_order,
                    'invoice_date': sales_order.order_date,
                    'due_date': sales_order.order_date + timedelta(days=30)
                })
            except Exception as e:
                messages.error(self.request, f"Error initializing form: {str(e)}")
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales_order_id = self.kwargs.get('sales_order_id')
        
        if self.request.POST:
            context['formset'] = ARInvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            if sales_order_id:
                try:
                    sales_order = get_object_or_404(SalesOrder, id=sales_order_id)
                    order_items = sales_order.order_items.all()
                    
                    initial_data = [
                        {
                            'product': item.product,
                            'quantity': item.quantity,
                            'unit_price': item.unit_price,
                        }
                        for item in order_items
                    ]
                    
                    context['formset'] = ARInvoiceItemFormSet(initial=initial_data)
                    context['formset'].extra = len(initial_data)
                    
                except Exception as e:
                    messages.error(self.request, f"Error loading sales order items: {str(e)}")
                    context['formset'] = ARInvoiceItemFormSet()
            else:
                context['formset'] = ARInvoiceItemFormSet()
        
        context.update(self.get_common_context())
        context['action'] = 'Add'
        context['products'] = Product.objects.all()
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
                    instances = formset.save(commit=False)
                    
                    total_amount = Decimal('0.00')
                    for instance in instances:
                        instance.total_amount = instance.quantity * instance.unit_price
                        total_amount += instance.total_amount
                        instance.save()
                    
                    for obj in formset.deleted_objects:
                        obj.delete()
                    
                    self.object.total_amount = total_amount
                    self.object.save()
                    
                    messages.success(self.request, self.success_message)
                    return super().form_valid(form)
            except Exception as e:
                messages.error(self.request, f"Error creating invoice: {str(e)}")
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
        
        return self.render_to_response(self.get_context_data(form=form))

    def get_common_context(self):
        invoices = ARInvoice.objects.all().order_by('id')
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('uniworlderp.add_arinvoice'),
            'can_edit': self.request.user.has_perm('uniworlderp.change_arinvoice'),
            'can_view': self.request.user.has_perm('uniworlderp.view_arinvoice'),
            'list_url': reverse_lazy('customer_vendor:invoice_list'),
            'create_url': reverse_lazy('customer_vendor:invoice_create'),
            'edit_url_name': 'customer_vendor:invoice_update',
            'view_url_name': 'customer_vendor:invoice_view',
            'print_url_name': 'customer_vendor:invoice_print',
            'search_url': reverse_lazy('customer_vendor:invoice_search'),
            'first_id': invoices.first().id if invoices.exists() else None,
            'last_id': invoices.last().id if invoices.exists() else None,
            'prev_id': None,
            'next_id': None,
            'current_id': None,
        }


class ARInvoiceUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ARInvoice
    form_class = ARInvoiceForm
    template_name = 'invoice/form.html'
    success_url = reverse_lazy('customer_vendor:sales_order_list')
    permission_required = 'uniworlderp.change_arinvoice'
    success_message = "Invoice updated successfully!"

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to edit this invoice.")
        return redirect('customer_vendor:sales_order_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = ARInvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = ARInvoiceItemFormSet(instance=self.object)
        context.update(self.get_common_context())
        context['action'] = 'Edit'
        context['products'] = Product.objects.all()
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            self.object = form.save(commit=False)
            
            # Check if the sales order has changed and if there's already an invoice for the new sales order
            if 'sales_order' in form.changed_data:
                new_sales_order = form.cleaned_data['sales_order']
                if new_sales_order and ARInvoice.objects.filter(sales_order=new_sales_order).exclude(pk=self.object.pk).exists():
                    messages.error(self.request, "An invoice already exists for the selected sales order.")
                    return self.form_invalid(form)
            
            # Calculate total_amount
            total_amount = Decimal('0.00')
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    quantity = form.cleaned_data.get('quantity', 0)
                    unit_price = form.cleaned_data.get('unit_price', 0)
                    total_amount += Decimal(str(quantity * unit_price))
            
            self.object.total_amount = total_amount
            self.object.save()
            
            formset.instance = self.object
            formset.save()

            # messages.success(self.request, self.success_message)
            return super().form_valid(form)
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
        return self.render_to_response(self.get_context_data(form=form))

    def get_common_context(self):
        invoices = ARInvoice.objects.all().order_by('id')
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('uniworlderp.add_arinvoice'),
            'can_edit': self.request.user.has_perm('uniworlderp.change_arinvoice'),
            'can_view': self.request.user.has_perm('uniworlderp.view_arinvoice'),
            'list_url': reverse_lazy('customer_vendor:invoice_list'),
            'create_url': reverse_lazy('customer_vendor:invoice_create'),
            'edit_url_name': 'customer_vendor:invoice_update',
            'view_url_name': 'customer_vendor:invoice_view',
            'print_url_name': 'customer_vendor:invoice_print',
            'search_url': reverse_lazy('customer_vendor:invoice_search'),
            'first_id': invoices.first().id if invoices.exists() else None,
            'last_id': invoices.last().id if invoices.exists() else None,
            'prev_id': None,
            'next_id': None,
            'current_id': None,
        }

class ARInvoiceDetailView(PermissionRequiredMixin, DetailView):
    model = ARInvoice
    template_name = 'invoice/form.html'
    permission_required = 'uniworlderp.view_arinvoice'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to view this invoice.")
        return redirect('customer_vendor:invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_common_context())
        context['action'] = 'View'
        context['form'] = ARInvoiceForm(instance=self.object)
        context['formset'] = ARInvoiceItemFormSet(instance=self.object)
        for form in context['formset']:
            for field in form.fields.values():
                field.widget.attrs['disabled'] = 'disabled'
        for field in context['form'].fields.values():
            field.widget.attrs['disabled'] = 'disabled'
        return context

    def get_common_context(self):
        invoices = ARInvoice.objects.all().order_by('id')
        current_invoice = self.object
        return {
            'model_name': self.model._meta.verbose_name.title(),
            'can_add': self.request.user.has_perm('uniworlderp.add_arinvoice'),
            'can_edit': self.request.user.has_perm('uniworlderp.change_arinvoice'),
            'can_view': self.request.user.has_perm('uniworlderp.view_arinvoice'),
            'list_url': reverse_lazy('customer_vendor:invoice_list'),
            'create_url': reverse_lazy('customer_vendor:invoice_create'),
            'edit_url_name': 'customer_vendor:invoice_update',
            'view_url_name': 'customer_vendor:invoice_view',
            'print_url_name': 'customer_vendor:invoice_print',
            'first_id': invoices.first().id if invoices.exists() else None,
            'last_id': invoices.last().id if invoices.exists() else None,
            'prev_id': invoices.filter(id__lt=current_invoice.id).last().id if invoices.filter(id__lt=current_invoice.id).exists() else None,
            'next_id': invoices.filter(id__gt=current_invoice.id).first().id if invoices.filter(id__gt=current_invoice.id).exists() else None,
            'current_id': current_invoice.id,
        }

class ARInvoiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ARInvoice
    template_name = 'confirm_delete.html'
    success_url = reverse_lazy('customer_vendor:invoice_list')
    success_message = "Invoice deleted successfully!"
    permission_required = 'uniworlderp.delete_arinvoice'

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to delete this invoice.")
        return redirect('customer_vendor:invoice_list')

    def delete(self, request, *args, **kwargs):
        # messages.success(self.request, self.success_message)
        return super(ARInvoiceDeleteView, self).delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model_name'] = self.model._meta.verbose_name.title()
        context['cancel_url'] = reverse_lazy('customer_vendor:invoice_list')
        return context

class ARInvoicePrintView(LoginRequiredMixin, DetailView):
    model = ARInvoice
    template_name = 'invoice/print.html'
    context_object_name = 'invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = Company.objects.first()  # Assuming you have only one company
        items = self.object.invoice_items.all()
        subtotal = sum(item.total_amount for item in items)
        tax = subtotal * Decimal('0.0')  # 12% tax
        total = subtotal + tax

        context.update({
            'company': company,
            'items': items,
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
        })
        return context

class ARInvoiceSearchView(ListView):
    model = ARInvoice
    template_name = 'invoice/search_results.html'
    context_object_name = 'invoices'
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return ARInvoice.objects.filter(
                Q(id__icontains=query) |
                Q(customer__name__icontains=query) |
                Q(invoice_date__icontains=query) |
                Q(total_amount__icontains=query)
            ).order_by('-invoice_date')
        return ARInvoice.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context



