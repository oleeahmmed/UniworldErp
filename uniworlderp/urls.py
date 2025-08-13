from django.urls import path
from uniworlderp.views import customer_views, sales_employee_views,product_views,sales_order_views,invoice_views,purchase_views,materials_purchase_views,report_views
from uniworlderp.views import sales_order_report_views
from . import views

app_name = 'customer_vendor'

urlpatterns = [
    path('customers-vendors/', customer_views.CustomerVendorListView.as_view(), name='customer_list'),
    path('customers-vendors/create/', customer_views.CustomerVendorCreateView.as_view(), name='customer_create'),
    path('customers-vendors/edit/<uuid:pk>/', customer_views.CustomerVendorUpdateView.as_view(), name='customer_edit'),
    path('customers-vendors/delete/<uuid:pk>/', customer_views.CustomerVendorDeleteView.as_view(), name='customer_delete'),
    path('customers-vendors/print/<uuid:pk>/', customer_views.CustomerVendorPrintView.as_view(), name='customer_print'),
    path('customers-vendors/view/<uuid:pk>/', customer_views.CustomerVendorDetailView.as_view(), name='customer_view'),
    path('customers-vendors/<uuid:pk>/sales-orders/', customer_views.SalesOrderListView.as_view(), name='sales_order_list'),
    path('customers-vendors/<uuid:pk>/purchase-orders/', customer_views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('customers-vendors/<uuid:pk>/invoices/', customer_views.InvoiceListView.as_view(), name='invoice_list'),
    # SalesEmployee URLs
    path('sales-employees/', sales_employee_views.SalesEmployeeListView.as_view(), name='sales_employee_list'),
    path('sales-employees/create/', sales_employee_views.SalesEmployeeCreateView.as_view(), name='sales_employee_create'),
    path('sales-employees/edit/<int:pk>/', sales_employee_views.SalesEmployeeUpdateView.as_view(), name='sales_employee_edit'),
    path('sales-employees/delete/<int:pk>/', sales_employee_views.SalesEmployeeDeleteView.as_view(), name='sales_employee_delete'),
    path('sales-employees/print/<int:pk>/', sales_employee_views.SalesEmployeePrintView.as_view(), name='sales_employee_print'),
    path('sales-employees/view/<int:pk>/', sales_employee_views.SalesEmployeeDetailView.as_view(), name='sales_employee_view'),
    
    # Product URLs
    path('products/', product_views.ProductListView.as_view(), name='product_list'),
    path('products/create/', product_views.ProductCreateView.as_view(), name='product_create'),
    path('products/edit/<uuid:pk>/', product_views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/delete/<uuid:pk>/', product_views.ProductDeleteView.as_view(), name='product_delete'),
    path('products/print/<uuid:pk>/', product_views.ProductPrintView.as_view(), name='product_print'),
    path('products/view/<uuid:pk>/', product_views.ProductDetailView.as_view(), name='product_view'),
    path('products/stock-transfer/', product_views.StockTransactionListView.as_view(), name='stock_transfer_detailed_list'),
    path('product-search/', product_views.product_search, name='product_search'),
    path('get-product-info/', product_views.get_product_info, name='get_product_info'),   
    path('add-stock/', product_views.AddStockView.as_view(), name='add_stock'),
    
    # Sales Order URLs
    path('sales-orders/', sales_order_views.SalesOrderListView.as_view(), name='sales_order_list'),
    path('sales-orders/create/', sales_order_views.SalesOrderCreateView.as_view(), name='sales_order_create'),
    path('sales-orders/update/<int:pk>/', sales_order_views.SalesOrderUpdateView.as_view(), name='sales_order_update'),
    path('sales-orders/view/<int:pk>/', sales_order_views.SalesOrderDetailView.as_view(), name='sales_order_view'),
    path('sales-orders/delete/<int:pk>/', sales_order_views.SalesOrderDeleteView.as_view(), name='sales_order_delete'),    
    path('sales-orders/print/<int:pk>/', sales_order_views.SalesOrderPrintView.as_view(), name='sales_order_print'),     
    path('sales-orders/detailed/', sales_order_views.SalesOrderItemDetailedListView.as_view(), name='sales_order_detailed_list'),
    
    #return
    path('sales-orders/return/<int:sales_order_id>/', sales_order_views.ReturnSalesCreateView.as_view(), name='sales_order_return'),
    path('sales-orders/view-return/<int:sales_order_id>/', sales_order_views.ReturnSalesDetailView.as_view(), name='sales_order_view_return'),

    # Invoice URLs
    path('invoices/', invoice_views.ARInvoiceListView.as_view(), name='invoice_list'),
    path('invoices/create/', invoice_views.ARInvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/create/<int:sales_order_id>/', invoice_views.ARInvoiceCreateView.as_view(), name='invoice_create_from_sales_order'),
    path('invoices/update/<int:pk>/', invoice_views.ARInvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/view/<int:pk>/', invoice_views.ARInvoiceDetailView.as_view(), name='invoice_view'),
    path('invoices/delete/<int:pk>/', invoice_views.ARInvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoices/print/<int:pk>/', invoice_views.ARInvoicePrintView.as_view(), name='invoice_print'),
    path('invoices/search/', invoice_views.ARInvoiceSearchView.as_view(), name='invoice_search'),   

    # Purchase Order URLs
  

    path('purchase-orders/', purchase_views.PurchaseOrderListView.as_view(), name='purchase_order_list'),
    path('purchase-orders/create/', purchase_views.PurchaseOrderCreateView.as_view(), name='purchase_order_create'),
    path('purchase-orders/<int:pk>/update/', purchase_views.PurchaseOrderUpdateView.as_view(), name='purchase_order_update'),
    path('purchase-orders/<int:pk>/', purchase_views.PurchaseOrderDetailView.as_view(), name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/delete/', purchase_views.PurchaseOrderDeleteView.as_view(), name='purchase_order_delete'),
    path('purchase-orders/<int:pk>/receive/', purchase_views.PurchaseOrderReceiveView.as_view(), name='purchase_order_receive'),
    path('purchase-orders/detailed-list/', purchase_views.PurchaseOrderItemDetailedListView.as_view(), name='purchase_order_detailed_list'),
    path('purchase-orders/<int:pk>/print/', purchase_views.PurchaseOrderPrintView.as_view(), name='purchase_order_print'),    


    # MaterialsPurchase URLs
    path('materials-purchases/', materials_purchase_views.MaterialsPurchaseListView.as_view(), name='materials_purchase_list'),
    path('materials-purchases/create/', materials_purchase_views.MaterialsPurchaseCreateView.as_view(), name='materials_purchase_create'),
    path('materials-purchases/<int:pk>/update/', materials_purchase_views.MaterialsPurchaseUpdateView.as_view(), name='materials_purchase_update'),
    path('materials-purchases/<int:pk>/delete/', materials_purchase_views.MaterialsPurchaseDeleteView.as_view(), name='materials_purchase_delete'),
    path('materials-purchases/<int:pk>/', materials_purchase_views.MaterialsPurchaseDetailView.as_view(), name='materials_purchase_view'),
    path('materials-purchases/<int:pk>/print/', materials_purchase_views.MaterialsPurchasePrintView.as_view(), name='materials_purchase_print'),
    path('materials-purchases/report/', materials_purchase_views.MaterialsPurchaseReportView.as_view(), name='materials_purchase_report'),
    path('reports/', report_views.ReportView.as_view(), name='sales_report'),
    
    # Stock Report URLs
    path('reports/stock/', report_views.StockReportView.as_view(), name='stock_report'),
    path('reports/stock/print/', report_views.StockReportPrintView.as_view(), name='stock_report_print'),
    
    # Single Product Report Print URL
    path('reports/single-product/print/', report_views.SingleProductReportPrintView.as_view(), name='single_product_report_print'),
    
    # Single Product Stock Report Print URL  
    path('reports/single-product-stock/print/', report_views.SingleProductStockReportPrintView.as_view(), name='single_product_stock_report_print'),
    
    # Customer Report URLs
    path('reports/customers/', report_views.CustomerReportView.as_view(), name='customer_report'),
    path('reports/customers/print/', report_views.CustomerReportPrintView.as_view(), name='customer_report_print'),
    path('reports/customers/excel/', report_views.CustomerReportExcelView.as_view(), name='customer_report_excel'),
    
    # Sales Order Report URLs
    path('reports/sales-orders/', sales_order_report_views.SalesOrderReportView.as_view(), name='sales_order_report'),
    path('reports/sales-orders/print/', sales_order_report_views.SalesOrderReportPrintView.as_view(), name='sales_order_report_print'),
    path('reports/sales-orders/excel/', sales_order_report_views.SalesOrderReportExcelView.as_view(), name='sales_order_report_excel'),
    
    # Product-wise Report URLs
    path('reports/product-wise/', report_views.ProductWiseReportView.as_view(), name='product_wise_report'),
    path('reports/product-wise/print/', report_views.ProductWiseReportPrintView.as_view(), name='product_wise_report_print'),
    path('reports/product-wise/excel/', report_views.ProductWiseReportExcelView.as_view(), name='product_wise_report_excel'),
    
    # Customer-wise Report URLs
    path('reports/customer-wise/', report_views.CustomerWiseReportView.as_view(), name='customer_wise_report'),
    path('reports/customer-wise/print/', report_views.CustomerWiseReportPrintView.as_view(), name='customer_wise_report_print'),
    path('reports/customer-wise/excel/', report_views.CustomerWiseReportExcelView.as_view(), name='customer_wise_report_excel'),

]
