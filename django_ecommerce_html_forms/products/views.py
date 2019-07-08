from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.http import HttpResponseNotFound

from products.models import Product, Category, ProductImage


def products(request):
    # Get all products from the DB using the Product model
    products = Product.objects.filter(active=True)

    # Get up to 4 `featured=true` Products to be displayed on top
    featured_products = products.filter(featured=True)[:4]

    return render(
        request,
        'products.html',
        context={'products': products, 'featured_products': featured_products}
    )


def create_product(request):
    # Get all categories from the DB
    categories = Category.objects.all()
    if request.method == 'GET':
        # Render 'create_product.html' template sending categories as context
        return render(request, 'create_product.html', context={'categories': categories})
    elif request.method == 'POST':
        # Validate that all fields below are given in request.POST dictionary,
        # and that they don't have empty values.

        # If any errors, build an errors dictionary with the following format
        # and render 'create_product.html' sending errors and categories as context

        # errors = {'name': 'This field is required.'}
        fields = ['name', 'sku', 'price']
        errors = {}
        for field in fields:
            if not request.POST.get(field):
                errors[field] = 'This field is required.'

        if errors:
            return render(request, 'create_product.html', context={'categories': categories, 'errors': errors})

        # If no errors so far, validate each field one by one and use the same
        # errors dictionary created above in case that any validation fails

        # name validation: can't be longer that 100 characters
        name = request.POST.get('name')
        if len(name) > 100:
            errors['name'] = "Name can't be longer than 100 characters."

        # SKU validation: it must contain 8 alphanumeric characters
        sku = request.POST.get('sku')
        if not len(sku) == 8 or not sku.isalnum():
            errors['sku'] = "SKU must contain 8 alphanumeric characters."

        # Price validation: positive float lower than 10000.00
        price = float(request.POST.get('price'))
        if not price >= 0 and not price < 10000:
            errors['price'] = "Price can't be negative or greater than or equal to $10,000."

        # if any errors so far, render 'create_product.html' sending errors and
        # categories as context
        if errors:
            return render(request, 'create_product.html', context={'categories': categories, 'errors': errors})

        description = request.POST.get('description')

        # If execution reaches this point, there aren't any errors.
        # Get category from DB based on category name given in payload.
        # Create product with data given in payload and proper category
        category = get_object_or_404(Category, name__iexact=request.POST.get('category'))
        product = Product.objects.create(name=name, sku=sku, price=price, category=category, description=description)
        product.save()

        # Up to three images URLs can come in payload with keys 'image-1', 'image-2', etc.
        # For each one, create a ProductImage object with proper URL and product
        for image in ['image_1', 'image_2', 'image_3']:
            url = request.POST.get(image)
            if url:
                product_image = ProductImage.objects.create(product=product, url=url)
                product_image.save()

        # Redirect to 'products' view
        return redirect('products')


def edit_product(request, product_id):
    # Get product with given product_id
    product = get_object_or_404(Product, id=product_id)

    # Get all categories from the DB
    categories = get_list_or_404(Category)
    if request.method == 'GET':
        # Render 'edit_product.html' template sending product, categories and
        # a 'images' list containing all product images URLs.

        # images = ['http://image/1', 'http://image/2', ...]
        return render(request, 'edit_product.html', context={
            'product': product,
            'categories': categories,
            'images': list(product.productimage_set.all())
        })  # static_form is just used as an example
    elif request.method == 'POST':
        # Validate following fields that come in request.POST in the very same
        # way that you've done it in create_product view
        fields = ['name', 'sku', 'price']
        errors = {}
        for field in fields:
            if not request.POST.get(field):
                errors[field] = 'This field is required.'

        if errors:
            return render(request, 'edit_product.html', context={'categories': categories, 'errors': errors})

        # If execution reaches this point, there aren't any errors.
        # Update product name, sku, price and description from the data that
        # come in request.POST dictionary.
        # Consider that ALL data is given as string, so you might format it
        # properly in some cases.
        product.name = request.POST.get('name')
        product.sku = request.POST.get('sku')
        product.price = float(request.POST.get('price'))
        product.description = request.POST.get('description')

        # Get proper category from the DB based on the category name given in
        # payload. Update product category.
        category = request.POST.get('category')
        product.category = get_object_or_404(Category, name__exact=category)
        product.save()

        # For updating the product images URLs, there are a couple of things that
        # you must consider:
        # 1) Create a ProductImage object for each URL that came in payload and
        #    is not already created for this product.
        # 2) Delete all ProductImage objects for URLs that are created but didn't
        #    come in payload
        # 3) Keep all ProductImage objects that are created and also came in payload
        product_images = product.productimage_set.all()
        urls = [request.POST.get(image) for image in ['image-1', 'image-2', 'image-3'] if request.POST.get(image)]

        # Delete unneeded images.
        product_images.exclude(url__in=urls).delete()

        # Create needed images.
        # Calling bulk_create() would be better if we know which ones we need to create.
        for url in urls:
            ProductImage.objects.get_or_create(product=product, url=url)

        # Redirect to 'products' view
        return redirect('products')


def delete_product(request, product_id):
    # Get product with given product_id
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'GET':
        # render 'delete_product.html' sending product as context
        return render(request, 'delete_product.html', context={'product': product})
    elif request.method == "POST":
        # Delete product and redirect to 'products' view
        product.delete()
        return redirect('products')


def toggle_featured(request, product_id):
    # Get product with given product_id
    product = get_object_or_404(Product, id=product_id)

    # Toggle product featured flag
    product.featured = not product.featured
    product.save()

    # Redirect to 'products' view
    return redirect('products')
