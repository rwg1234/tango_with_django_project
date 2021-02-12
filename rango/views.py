from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page

def index(request):
    # Query the database for a list of ALL categories currently stored.
    # Order the categories by the number of likes in descending order.
    # Retrieve the top 5 only -- or all if less than 5.
    # Place the lsit in our context_dict dicitonary (with our boldmessage!)
    # that will be passed to the template engine.
    category_list = Category.objects.order_by('-likes')[:5]
    
    # do the same thing for pages
    page_list = Page.objects.order_by('-views')[:5]
    
    context_dict = {}
    context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
    context_dict['categories'] = category_list
    context_dict['pages'] = page_list

    return render(request, 'rango/index.html', context=context_dict)

def about(request):
    return render(request, 'rango/about.html')

def show_category(request, category_name_slug):
    # create a context dictionary which we can pass to the template rendering engine
    context_dict = {}
    
    try:
        # can we find a category name slug with the given name?
        # if not, then the .get() method raises DoesNotExist.
        # the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)
        
        # Retrieve all of the associated pages
        # the filter() returns a list of page objects or an empty list.
        pages = Page.objects.filter(category=category)
        
        # add our results list to the template context under name pages
        context_dict['pages'] = pages
        # we also add the category object form the DB to the context dictionary.
        # we use this in the template to verify that the category exists
        context_dict['category'] = category
    except Category.DoesNotExist:
        # we get here if we didn't find the specified category
        # don't do anything here, the template will show a no-category message for use
        context_dict['category'] = None
        context_dict['pages'] = None
    
    # go render the response
    return render(request, 'rango/category.html', context=context_dict)