from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from uniworlderp.models import SalesOrder, CustomerVendor, Product, SalesEmployee, SalesOrderItem
from django.db.models import Sum, F, Q
from datetime import datetime, date
from django.utils import timezone
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
import io

class SalesOrderReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for generating and displaying sales order reports with customer-wise analysis."""
    template_name = 'reports/sales_order_report.html'
    permission_required = 'uniworlderp.view_salesorder'
    
    def get(self, request, *args, **kwargs):
        """Display sales order report form and results."""
        # Get filter parameters
        customer_id = request.GET.get('customer', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # Get all customers for the filter dropdown
        customers = CustomerVendor.objects.filter(entity_type='customer', owner=request.user).order_by('name')
        
        # Start with all sales orders
        sales_orders = SalesOrder.objects.filter(owner=request.user).select_related(
            'customer', 'sales_employee'
        ).prefetch_related('order_items__product').order_by('-order_date')
        
        # Apply customer filter
        if customer_id:
            sales_orders = sales_orders.filter(customer_id=customer_id)
        
        # Apply date range filter
        if start_date:
            sales_orders = sales_orders.filter(order_date__gte=start_date)
        if end_date:
            sales_orders = sales_orders.filter(order_date__lte=end_date)
        
        # Calculate summary data
        total_orders = sales_orders.count()
        total_amount = sales_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Get customer information for header if customer is selected
        customer_info = None
        if customer_id:
            try:
                customer_info = CustomerVendor.objects.get(id=customer_id, owner=request.user)
            except CustomerVendor.DoesNotExist:
                pass
        
        # Prepare context
        context = {
            'sales_orders': sales_orders,
            'customers': customers,
            'selected_customer': customer_id,
            'start_date': start_date,
            'end_date': end_date,
            'total_orders': total_orders,
            'total_amount': total_amount,
            'customer_info': customer_info,
        }
        
        return render(request, self.template_name, context)

class SalesOrderReportPrintView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for printing sales order reports."""
    template_name = 'reports/sales_order_report_print.html'
    permission_required = 'uniworlderp.view_salesorder'
    
    def get(self, request, *args, **kwargs):
        """Display printable sales order report."""
        # Get filter parameters
        customer_id = request.GET.get('customer', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # Get customer information for header if customer is selected
        customer_info = None
        if customer_id:
            try:
                customer_info = CustomerVendor.objects.get(id=customer_id, owner=request.user)
            except CustomerVendor.DoesNotExist:
                pass
        
        # Start with all sales orders
        sales_orders = SalesOrder.objects.filter(owner=request.user).select_related(
            'customer', 'sales_employee'
        ).prefetch_related('order_items__product').order_by('-order_date')
        
        # Apply filters
        if customer_id:
            sales_orders = sales_orders.filter(customer_id=customer_id)
        if start_date:
            sales_orders = sales_orders.filter(order_date__gte=start_date)
        if end_date:
            sales_orders = sales_orders.filter(order_date__lte=end_date)
        
        # Calculate summary data
        total_orders = sales_orders.count()
        total_amount = sales_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        
        context = {
            'sales_orders': sales_orders,
            'customer_info': customer_info,
            'start_date': start_date,
            'end_date': end_date,
            'total_orders': total_orders,
            'total_amount': total_amount,
        }
        
        return render(request, self.template_name, context)

class SalesOrderReportExcelView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """View for exporting sales order reports to Excel."""
    permission_required = 'uniworlderp.view_salesorder'
    
    def get(self, request, *args, **kwargs):
        """Export sales order report to Excel."""
        # Get filter parameters
        customer_id = request.GET.get('customer', '')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        
        # Get customer information for header if customer is selected
        customer_info = None
        if customer_id:
            try:
                customer_info = CustomerVendor.objects.get(id=customer_id, owner=request.user)
            except CustomerVendor.DoesNotExist:
                pass
        
        # Start with all sales orders
        sales_orders = SalesOrder.objects.filter(owner=request.user).select_related(
            'customer', 'sales_employee'
        ).prefetch_related('order_items__product').order_by('-order_date')
        
        # Apply filters
        if customer_id:
            sales_orders = sales_orders.filter(customer_id=customer_id)
        if start_date:
            sales_orders = sales_orders.filter(order_date__gte=start_date)
        if end_date:
            sales_orders = sales_orders.filter(order_date__lte=end_date)
        
        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Sales Order Report"
        
        # Add customer information header if customer is selected
        if customer_info:
            ws.cell(row=1, column=1, value=f"Customer: {customer_info.name}")
            ws.cell(row=2, column=1, value=f"Mobile: {customer_info.phone_number}")
            ws.cell(row=3, column=1, value=f"Address: {customer_info.address or 'N/A'}")
            ws.cell(row=4, column=1, value="")
            header_row = 5
        else:
            header_row = 1
        
        # Add headers
        headers = [
            'SL', 'Order Date', 'Order ID', 'Customer', 'Product Details', 
            'Qty', 'Unit Price', 'Sub Total', 'Discount', 'Net Amount', 'Sales Employee'
        ]
        
        # Style headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
        
        # Add data
        row_num = header_row + 1
        for i, order in enumerate(sales_orders, 1):
            for item in order.order_items.all():
                row = [
                    i,
                    order.order_date.strftime('%Y-%m-%d') if order.order_date else '',
                    order.id,
                    order.customer.name if order.customer else '',
                    item.product.name if item.product else '',
                    item.quantity,
                    float(item.unit_price),
                    float(item.total),
                    float(item.discount_amount) if item.discount_amount else 0,
                    float(order.total_amount),
                    order.sales_employee.full_name if order.sales_employee else '',
                ]
                for col, value in enumerate(row, 1):
                    ws.cell(row=row_num, column=col, value=value)
                row_num += 1
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = min(adjusted_width, 50)
        
        # Save to buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Create response
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=sales_order_report.xlsx'
        
        return response
