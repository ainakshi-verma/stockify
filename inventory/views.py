from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Supplier, Sale, Purchase
from django.db.models import Q, F, Sum
import csv
from django.http import HttpResponse

@login_required
def dashboard(request):
    products = Product.objects.filter(user=request.user)
    total_products = products.count()
    
    # Stock Status Logic
    low_stock_products = products.filter(quantity__lt=F('threshold'), quantity__gt=0)
    critical_stock_products = products.filter(quantity=0)
    safe_stock_count = products.filter(quantity__gte=F('threshold')).count()
    
    low_stock_count = low_stock_products.count()
    critical_stock_count = critical_stock_products.count()
    
    # Enhanced Stats
    sales = Sale.objects.filter(user=request.user)
    purchases = Purchase.objects.filter(user=request.user)
    
    total_sales_count = sales.count()
    total_sales_qty = sales.aggregate(Sum('quantity_sold'))['quantity_sold__sum'] or 0
    total_purchases_qty = purchases.aggregate(Sum('quantity_added'))['quantity_added__sum'] or 0

    recent_transactions = list(sales.order_by('-date')[:5]) + list(purchases.order_by('-date')[:5])
    recent_transactions.sort(key=lambda x: x.date, reverse=True)
    recent_transactions = recent_transactions[:5]

    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'critical_stock_count': critical_stock_count,
        'safe_stock_count': safe_stock_count,
        'low_stock_products': low_stock_products[:5],
        'critical_stock_products': critical_stock_products[:5],
        'total_sales_count': total_sales_count,
        'total_sales_qty': total_sales_qty,
        'total_purchases_qty': total_purchases_qty,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'dashboard.html', context)

@login_required
def product_list(request):
    query = request.GET.get('q')
    low_stock_only = request.GET.get('low_stock')
    
    products = Product.objects.filter(user=request.user)
    
    if query:
        products = products.filter(Q(name__icontains=query) | Q(category__icontains=query))
    
    if low_stock_only:
        products = products.filter(quantity__lt=F('threshold'))
        
    return render(request, 'product_list.html', {'products': products})

@login_required
def add_product(request):
    suppliers = Supplier.objects.filter(user=request.user)
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        threshold = request.POST.get('threshold')
        category = request.POST.get('category')
        supplier_id = request.POST.get('supplier')
        
        supplier = None
        if supplier_id:
            supplier = get_object_or_404(Supplier, id=supplier_id, user=request.user)

        Product.objects.create(
            name=name,
            description=description,
            price=price,
            quantity=quantity,
            threshold=threshold,
            category=category,
            supplier=supplier,
            user=request.user
        )
        messages.success(request, "Product added successfully!")
        return redirect('product_list')
    
    return render(request, 'add_product.html', {'suppliers': suppliers})

@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    suppliers = Supplier.objects.filter(user=request.user)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.quantity = request.POST.get('quantity')
        product.threshold = request.POST.get('threshold')
        product.category = request.POST.get('category')
        
        supplier_id = request.POST.get('supplier')
        if supplier_id:
            product.supplier = get_object_or_404(Supplier, id=supplier_id, user=request.user)
        else:
            product.supplier = None
            
        product.save()
        messages.success(request, "Product updated successfully!")
        return redirect('product_list')
    
    return render(request, 'edit_product.html', {'product': product, 'suppliers': suppliers})

@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, user=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect('product_list')
    return render(request, 'delete_confirm.html', {'product': product})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome {user.username}! Your account has been created.")
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')

# --- New Modules ---

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.filter(user=request.user)
    return render(request, 'supplier_list.html', {'suppliers': suppliers})

@login_required
def add_supplier(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        contact = request.POST.get('contact')
        email = request.POST.get('email')
        address = request.POST.get('address')
        
        Supplier.objects.create(
            name=name,
            contact=contact,
            email=email,
            address=address,
            user=request.user
        )
        messages.success(request, "Supplier added successfully!")
        return redirect('supplier_list')
    return render(request, 'add_supplier.html')

@login_required
def record_sale(request):
    products = Product.objects.filter(user=request.user)
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity'))
        product = get_object_or_404(Product, id=product_id, user=request.user)
        
        if product.quantity >= quantity:
            product.quantity -= quantity
            product.save()
            Sale.objects.create(product=product, quantity_sold=quantity, user=request.user)
            messages.success(request, f"Sale recorded: {quantity} units of {product.name}")
            return redirect('sales_history')
        else:
            messages.error(request, f"Error: Only {product.quantity} units available in stock.")
            
    return render(request, 'add_sale.html', {'products': products})

@login_required
def record_purchase(request):
    products = Product.objects.filter(user=request.user)
    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = int(request.POST.get('quantity'))
        product = get_object_or_404(Product, id=product_id, user=request.user)
        
        product.quantity += quantity
        product.save()
        Purchase.objects.create(product=product, quantity_added=quantity, user=request.user)
        messages.success(request, f"Purchase recorded: {quantity} units added to {product.name}")
        return redirect('purchase_history')
        
    return render(request, 'add_purchase.html', {'products': products})

@login_required
def sales_history(request):
    sales = Sale.objects.filter(user=request.user).order_by('-date')
    return render(request, 'sales_history.html', {'sales': sales})

@login_required
def purchase_history(request):
    purchases = Purchase.objects.filter(user=request.user).order_by('-date')
    return render(request, 'purchase_history.html', {'purchases': purchases})

# --- Reporting & Export Modules ---

@login_required
def inventory_report(request):
    products = Product.objects.filter(user=request.user)
    
    # Advanced Filtering
    category = request.GET.get('category')
    supplier_id = request.GET.get('supplier')
    status = request.GET.get('status')
    
    if category:
        products = products.filter(category=category)
    if supplier_id:
        products = products.filter(supplier_id=supplier_id)
    if status == 'low':
        products = products.filter(quantity__lt=F('threshold'), quantity__gt=0)
    elif status == 'critical':
        products = products.filter(quantity=0)
        
    categories = Product.objects.filter(user=request.user).values_list('category', flat=True).distinct()
    suppliers = Supplier.objects.filter(user=request.user)
    
    return render(request, 'reports/inventory_report.html', {
        'products': products,
        'categories': categories,
        'suppliers': suppliers
    })

@login_required
def sales_report(request):
    sales = Sale.objects.filter(user=request.user).order_by('-date')
    total_qty = sales.aggregate(Sum('quantity_sold'))['quantity_sold__sum'] or 0
    return render(request, 'reports/sales_report.html', {
        'sales': sales,
        'total_sales': sales.count(),
        'total_qty': total_qty
    })

@login_required
def purchase_report(request):
    purchases = Purchase.objects.filter(user=request.user).order_by('-date')
    total_qty = purchases.aggregate(Sum('quantity_added'))['quantity_added__sum'] or 0
    return render(request, 'reports/purchase_report.html', {
        'purchases': purchases,
        'total_purchases': purchases.count(),
        'total_qty': total_qty
    })

@login_required
def export_inventory_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Product Name', 'Category', 'Supplier', 'Price', 'Quantity', 'Threshold'])
    
    products = Product.objects.filter(user=request.user)
    for p in products:
        writer.writerow([p.name, p.category, p.supplier.name if p.supplier else '--', p.price, p.quantity, p.threshold])
        
    return response

@login_required
def export_sales_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Product', 'Quantity Sold'])
    
    sales = Sale.objects.filter(user=request.user).order_by('-date')
    for s in sales:
        writer.writerow([s.date.strftime('%Y-%m-%d %H:%M'), s.product.name, s.quantity_sold])
        
    return response
