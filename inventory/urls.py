from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:pk>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:pk>/', views.delete_product, name='delete_product'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Supplier URLs
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.add_supplier, name='add_supplier'),
    
    # Transaction URLs
    path('transactions/sale/', views.record_sale, name='record_sale'),
    path('transactions/purchase/', views.record_purchase, name='record_purchase'),
    path('transactions/sales-history/', views.sales_history, name='sales_history'),
    path('transactions/purchase-history/', views.purchase_history, name='purchase_history'),
    
    # Report URLs
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/purchase/', views.purchase_report, name='purchase_report'),
    
    # Export URLs
    path('export/inventory-csv/', views.export_inventory_csv, name='export_inventory_csv'),
    path('export/sales-csv/', views.export_sales_csv, name='export_sales_csv'),
]
