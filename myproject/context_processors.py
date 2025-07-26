from django.apps import apps
from django.urls import reverse, resolve

def app_menu_context(request):
    # Initialize the menu visibility flags
    show_company_menu = False
    show_permission_menu = False
    show_dashboard_link = False
    show_customer_menu = False
    show_sales_employee_menu = False
    show_product_menu = False
    show_sales_order_menu = False 
    show_purchase_menu = False   
    show_invoice_menu   = False     
    # Check permissions only if the user is authenticated
    if request.user.is_authenticated:
        # Check for the 'company' app and its view permission
        if apps.is_installed('company'):
            show_company_menu = request.user.has_perm('company.view_company')
        # Check for the 'permission' app and its view permission
        if apps.is_installed('permission'):
            show_permission_menu = request.user.has_perm('auth.view_permission')
        # Check if 'dashboard' URL exists
        try:
            reverse('permission:dashboard')  # Trying to resolve the 'dashboard' URL
            show_dashboard_link = True
        except:
            show_dashboard_link = False

        # Check for 'uniworlderp' app and its permissions
        if apps.is_installed('uniworlderp'):
            # Check if the user has permission to view customers
            show_customer_menu = request.user.has_perm('uniworlderp.view_customervendor')
            # Check if the user has permission to view sales employees
            show_sales_employee_menu = request.user.has_perm('uniworlderp.view_salesemployee')
            # Check if the user has permission to view products
            show_product_menu = request.user.has_perm('uniworlderp.view_product')
            # Check if the user has permission to view sales orders
            show_sales_order_menu = request.user.has_perm('uniworlderp.view_salesorder')       
            show_invoice_menu = request.user.has_perm('uniworlderp.view_arinvoice')    
            show_purchase_menu = request.user.has_perm('uniworlderp.view_purchaseorder')               
    # Return these values in the context
    return {
        'show_company_menu': show_company_menu,
        'show_permission_menu': show_permission_menu,
        'show_dashboard_link': show_dashboard_link,  
        
        'show_customer_menu': show_customer_menu,  
        'show_sales_employee_menu': show_sales_employee_menu, 
        'show_product_menu': show_product_menu,      
        'show_sales_order_menu': show_sales_order_menu,  
        'show_invoice_menu': show_invoice_menu,  
        'show_purchase_menu': show_purchase_menu,  

    }
