from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime

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

    visitor_cookie_handler(request)
    #context_dict['visits'] = request.session['visits']
    
    response = render(request, 'rango/index.html', context=context_dict)
    return response

def about(request):
    visitor_cookie_handler(request)
    context_dict = {'visits': request.session['visits']}
    return render(request, 'rango/about.html', context=context_dict)

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

@login_required
def add_category(request):
    form = CategoryForm()
    
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        
        # have we been provided with a valid form?
        if form.is_valid():
            # save to database
            form.save(commit=True)
            # now that the category is saved, we could confirm this.
            # for now, let's just redirect to the index page
            return redirect('/rango/')
        else:
            # The supplied form contained errors -
            # print the errors to the terminal
            print(form.errors)
    # will handle the bad form, new form or no form supplied cases.
    # render the form with error messages (if any)
    return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):
    try:
        category = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        category = None
    
    # you can't add a page to a Category that doesn't exist
    if category is None:
        return redirect(reverse('rango:index'))
    
    form = PageForm()
    
    if request.method == 'POST':
        form = PageForm(request.POST)
        
        if form.is_valid():
            if category:
                page = form.save(commit=False)
                page.category = category
                page.views = 0
                page.save()
                
                return redirect(reverse('rango:show_category',
                                        kwargs={'category_name_slug':
                                                category_name_slug}))
        else:
            print(form.errors)
    
    context_dict = {'form': form, 'category': category}
    return render(request, 'rango/add_page.html', context=context_dict)

def register(request):
    registered = False
    
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            
            profile = profile_form.save(commit=False)
            profile.user = user
            
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']
            
            profile.save()
            
            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        # not http post
        user_form = UserForm()
        profile_form = UserProfileForm()
    
    return render(request, 'rango/register.html', context={'user_form': user_form,
                                                           'profile_form': profile_form,
                                                           'registered': registered})

def user_login(request):
    # if it's a POST, receive information
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # check if the credentials are correct
        user = authenticate(username=username, password=password)
        
        # if the creds are correct, user is a User object.
        # otherwise, user is None.
        
        if user:
            # check if the user is active (not deactivated)
            if user.is_active:
                #if the account is valid and active then we can login
                login(request, user)
                return redirect(reverse('rango:index'))
            else:
                # not logging in a deactivated user
                return HttpResponse("Your Rango account is disabled.")
        else:
            # bad login details.
            print(f"Invalid login details: {username}, {password}")
            # isn't this a vulnerability? if a user mistypes their password, should their almost-password be stored in plaintext in the server logs??
            return HttpResponse("Invalid login details supplied.")
    else:
        # not a post request (probably GET)
        # just show login form
        return render(request, 'rango/login.html')

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')

@login_required
def user_logout(request):
    # since we know the user is logged in, we can just log them out
    logout(request)
    # take the user back to the homepage
    return redirect(reverse('rango:index'))

# helper method
def get_server_side_cookie(request, cookie, default_val=None):
    val = request.session.get(cookie)
    if not val:
        val = default_val
    return val

def visitor_cookie_handler(request):
    visits = int(get_server_side_cookie(request, 'visits', '1'))
    last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
    last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')
    
    # if more than a day since last visited
    if (datetime.now() - last_visit_time).days > 0:
        visits += 1
        request.session['last_visit'] = str(datetime.now())
    else:
        request.session['last_visit'] = last_visit_cookie
    
    request.session['visits'] = visits

























