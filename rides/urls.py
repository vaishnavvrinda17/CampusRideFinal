
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('find-ride/', views.find_ride, name='find_ride'),
    path('offer-ride/', views.offer_ride, name='offer_ride'),
    path('errand/', views.share_errand, name='share_errand'),
    path('nearby-rides/', views.nearby_rides, name='nearby_rides'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path(
    'request-ride/<int:ride_id>/',
    views.request_ride,
    name='request_ride'
    ),

    path(
       'my-ride-requests/',
        views.my_ride_requests,
        name='my_ride_requests'
    ),
    path(
        'respond-to-request/<int:request_id>/',
        views.respond_to_request,
        name='respond_to_request'
    ),

    path('live-tracking/', views.live_tracking, name='live_tracking'),
    path("find-errands/", views.find_errands, name="find_errands"),
    path(
    "accept-errand/<int:errand_id>/",
    views.accept_errand,
    name="accept_errand"
    ),
    path(
    "verify-email/<uidb64>/<token>/",
    views.verify_email,
    name="verify_email"
    ),


]
