from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel, DealerReview
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, get_dealer_by_id, get_dealers_by_state, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json
#from uuid import uuid4
# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your views here.

# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    # Handles POST request
    if request.method == "POST":
        # Get username and password from request.POST dictionary
        username = request.POST['username']
        password = request.POST['psw']
        # Try to check if provide credential can be authenticated
        user = authenticate(username=username, password=password)
        if user is not None:
            # If user is valid, call login method to login current user
            login(request, user)
            return redirect('djangoapp:index')
        else:
            # If not, return to login page again
            return render(request, 'djangoapp/login.html', context)
    else:
        return render(request, 'djangoapp/login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    print("Log out the user `{}`".format(request.user.username))
    # Logout user in the request
    logout(request)
    # Redirect user back to course list view
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/ff5958e3-f780-4c19-bb7e-26530708ae27/dealership-package/get-dealership"
        # Get dealers from the URL
        context["dealerships"] = get_dealers_from_cf(url)
        # Concat all dealer's short name
        #dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)

# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        context = {}
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/ff5958e3-f780-4c19-bb7e-26530708ae27/dealership-package/get-review.json"
        url2 = "https://us-south.functions.appdomain.cloud/api/v1/web/ff5958e3-f780-4c19-bb7e-26530708ae27/dealership-package/get-dealership"
        # Get dealers from the URL
        reviews = get_dealer_reviews_from_cf(url, dealer_id=dealer_id)
        context = {
            "reviews":  reviews, 
            "dealer_id": dealer_id,
            "dealer": get_dealer_by_id(url2, dealer_id=dealer_id),
        }
        # Concat all dealer's short name
        #review_names = ' '.join([rev.review for rev in reviews])
        #review_sent = ' '.join([rev.sentiment for rev in reviews])
        # Return a list of dealer short name
        #result = f"Review Names: {review_names}, Review Sentiments: {review_sent}"
        return render(request, 'djangoapp/dealer_details.html', context)
# ...

# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    if request.user.is_authenticated:
        if request.method == "GET":
            # Get dealer details from the API
            url = "https://us-south.functions.appdomain.cloud/api/v1/web/ff5958e3-f780-4c19-bb7e-26530708ae27/dealership-package/get-dealership"
            context = {
                "cars": CarModel.objects.all(),
                "dealer": get_dealer_by_id(url, dealer_id=dealer_id),
                "dealer_id": dealer_id
            }
            #print(get_dealer_by_id(url, dealer_id=dealer_id))
            #return HttpResponse(context["dealer"])
            return render(request, 'djangoapp/add_review.html', context)
        if request.method == "POST":
            form = request.POST
            review = dict()
            review = {
                "id": int(datetime.now().timestamp()),
                "name": f"{request.user.username}",
                "dealership": dealer_id,
                "review": form["content"],
                "purchase": form.get("purchasecheck"),
                }
            if form.get("purchasecheck"):
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
                review["purchase"] = True
            else: 
                review["purchase_date"] = None
                review["purchase"] = False
            car = CarModel.objects.get(pk=form["car"])
            review["car_make"] = car.carmake.name
            review["car_model"] = car.name
            review["car_year"] = car.year
            json_payload = {"review": review}  # Create a JSON payload that contains the review data
            #print(json_payload)
            url = "https://us-south.functions.appdomain.cloud/api/v1/web/ff5958e3-f780-4c19-bb7e-26530708ae27/dealership-package/post-review.json"  # API Cloud Function route

            # Performing a POST request with the review
            result = post_request(url, json_payload, dealerId=dealer_id)
            if int(result.status_code) == 200:
                print("Review posted successfully.")
            # After posting the review the user is redirected back to the dealer details page
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
    else:
        # If user isn't logged in, redirect to login page
        print("User must be authenticated before posting a review. Please log in.")
        return redirect("/djangoapp/login")
# ...
