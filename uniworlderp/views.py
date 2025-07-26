from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from .models import MaterialsPurchase
from .forms import MaterialsPurchaseForm, MaterialsPurchaseItemFormSet

class MaterialsPurchaseListView(LoginRequiredMixin, ListView):
    model = MaterialsPurchase
    template_name = 'materials_purchase/list.html'
    context_object_name = 'purchases'

class MaterialsPurchaseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = MaterialsPurchase
    form_class = MaterialsPurchaseForm
    template_name = 'materials_purchase/form.html'
    success_url = reverse_lazy('materials_purchase_list')
    permission_required = 'add_materialspurchase'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = MaterialsPurchaseItemFormSet(self.request.POST)
        else:
            data['items'] = MaterialsPurchaseItemFormSet()
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            form.instance.owner = self.request.user
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
        return super().form_valid(form)

class MaterialsPurchaseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = MaterialsPurchase
    form_class = MaterialsPurchaseForm
    template_name = 'materials_purchase/form.html'
    success_url = reverse_lazy('materials_purchase_list')
    permission_required = 'change_materialspurchase'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = MaterialsPurchaseItemFormSet(self.request.POST, instance=self.object)
        else:
            data['items'] = MaterialsPurchaseItemFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
        return super().form_valid(form)

class MaterialsPurchaseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = MaterialsPurchase
    template_name = 'materials_purchase/confirm_delete.html'
    success_url = reverse_lazy('materials_purchase_list')
    permission_required = 'delete_materialspurchase'

class MaterialsPurchaseDetailView(LoginRequiredMixin, DetailView):
    model = MaterialsPurchase
    template_name = 'materials_purchase/detail.html'
    context_object_name = 'purchase'

