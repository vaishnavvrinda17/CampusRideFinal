from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.shortcuts import render, redirect
from .models import Ride, Errand
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.shortcuts import get_object_or_404
from .models import RideRequest
from django.utils import timezone
from datetime import datetime
from django.views.decorators.http import require_POST
from .forms import StudentRegistrationForm
from .models import StudentProfile

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from django.contrib.auth import get_user_model
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode




def home(request):
    return render(request, 'home.html')


def find_ride(request):
    now = timezone.localtime()

    rides = Ride.objects.filter(
        available_seats__gt=0
    ).order_by('travel_date', 'travel_time')

    pickup = request.GET.get('pickup', '').strip()
    destination = request.GET.get('destination', '').strip()
    travel_date = request.GET.get('travel_date', '').strip()

    # Hide rides whose departure date/time has passed.
    future_rides = []

    for ride in rides:
        ride_datetime = timezone.make_aware(
            datetime.combine(ride.travel_date, ride.travel_time),
            timezone.get_current_timezone()
        )

        if ride_datetime > now:
            future_rides.append(ride.pk)

    rides = rides.filter(pk__in=future_rides)
    if pickup:
        rides = rides.filter(pickup_location__icontains=pickup)

    if destination:
        rides = rides.filter(destination__icontains=destination)

    travel_time = request.GET.get('travel_time', '').strip()

    if travel_time:
        try:
            selected_time = datetime.strptime(
                travel_time.upper().replace(" ", ""),
                '%I:%M%p'
            ).time()

            rides = rides.filter(
                travel_time__gte=selected_time
            )
        except ValueError:
            pass

    return render(request, 'find_ride.html', {
        'rides': rides,
        'request': request,
    })

   

@login_required
def offer_ride(request):
    if request.method == 'GET' and request.GET.get('success') == '1':
        return render(request, 'offer_ride.html', {'success': True})

    if request.method == 'POST':
        student_name = request.POST.get('student_name', '').strip()
        pickup_location = request.POST.get('pickup_location', '').strip()
        destination = request.POST.get('destination', '').strip()
        travel_date = request.POST.get('travel_date', '').strip()
        travel_time = request.POST.get('travel_time', '').strip()
        try:
            travel_time = datetime.strptime(
                travel_time.strip().upper().replace(" ", ""),
                '%I:%M%p'
            ).time()
        except ValueError:
            return render(request, 'offer_ride.html', {
                'error': 'Please enter time like 10:30 PM.'
            })
        available_seats = request.POST.get('available_seats', '').strip()

        pickup_lat = request.POST.get('pickup_latitude', '').strip()
        pickup_lon = request.POST.get('pickup_longitude', '').strip()
        destination_lat = request.POST.get('destination_latitude', '').strip()
        destination_lon = request.POST.get('destination_longitude', '').strip()

        if not all([
            student_name, pickup_location, destination,
            travel_date, travel_time, available_seats
        ]):
            return render(request, 'offer_ride.html', {
                'error': 'Please fill in all required fields.'
            })

        try:
            seats = int(available_seats)
            if seats < 1:
                raise ValueError
        except (ValueError, TypeError):
            return render(request, 'offer_ride.html', {
                'error': 'Available seats must be a whole number greater than zero.'
            })

        if bool(pickup_lat) != bool(pickup_lon):
            return render(request, 'offer_ride.html', {
                'error': 'Enter both pickup latitude and longitude.'
            })

        if bool(destination_lat) != bool(destination_lon):
            return render(request, 'offer_ride.html', {
                'error': 'Enter both destination latitude and longitude.'
            })

        pickup_point = None
        destination_point = None

        try:
            if pickup_lat and pickup_lon:
                lat = float(pickup_lat)
                lon = float(pickup_lon)

                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError

                pickup_point = Point(lon, lat, srid=4326)

            if destination_lat and destination_lon:
                lat = float(destination_lat)
                lon = float(destination_lon)

                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError

                destination_point = Point(lon, lat, srid=4326)

        except (ValueError, TypeError):
            return render(request, 'offer_ride.html', {
                'error': 'Invalid coordinates. Latitude must be -90 to 90 and longitude -180 to 180.'
            })
        
        print("DEBUG travel_time:", repr(travel_time), type(travel_time))
        Ride.objects.create(
            student_name=student_name,
            pickup_location=pickup_location,
            destination=destination,
            travel_date=travel_date,
            travel_time=travel_time,
            available_seats=seats,
            pickup_point=pickup_point,
            destination_point=destination_point,
            offered_by=request.user
        )

        return redirect('/offer-ride/?success=1')

    return render(request, 'offer_ride.html')



@login_required
def share_errand(request):
    if request.method == 'GET' and request.GET.get('success') == '1':
        return render(request, 'errand.html', {'success': True})

    if request.method == 'POST':
        student_name = request.POST.get('student_name', '').strip()
        task_description = request.POST.get('task_description', '').strip()
        pickup_location = request.POST.get('pickup_location', '').strip()
        delivery_location = request.POST.get('delivery_location', '').strip()
        category = request.POST.get('category', 'other').strip()
        required_date = request.POST.get('required_date', '').strip()

        pickup_lat = request.POST.get('pickup_latitude', '').strip()
        pickup_lon = request.POST.get('pickup_longitude', '').strip()
        delivery_lat = request.POST.get('delivery_latitude', '').strip()
        delivery_lon = request.POST.get('delivery_longitude', '').strip()

        if not all([
            student_name, task_description, pickup_location,
            delivery_location, required_date, category
        ]):
            return render(request, 'errand.html', {
                'error': 'Please fill in all required fields.'
            })

        valid_categories = {'shopping', 'documents', 'food', 'other'}
        if category not in valid_categories:
            return render(request, 'errand.html', {
                'error': 'Please select a valid category.'
            })

        try:
            from datetime import date

            required_date_value = date.fromisoformat(required_date)

            def parse_coordinate(value, minimum, maximum):
                if not value:
                    return None
                number = float(value)
                if not minimum <= number <= maximum:
                    raise ValueError
                return number

            pickup_lat_value = parse_coordinate(pickup_lat, -90, 90)
            pickup_lon_value = parse_coordinate(pickup_lon, -180, 180)
            delivery_lat_value = parse_coordinate(delivery_lat, -90, 90)
            delivery_lon_value = parse_coordinate(delivery_lon, -180, 180)

            if bool(pickup_lat_value is not None) != bool(pickup_lon_value is not None):
                raise ValueError

            if bool(delivery_lat_value is not None) != bool(delivery_lon_value is not None):
                raise ValueError

        except (ValueError, TypeError):
            return render(request, 'errand.html', {
                'error': 'Please check the date and location coordinates.'
            })

        Errand.objects.create(
            student_name=student_name,
            task_description=task_description,
            pickup_location=pickup_location,
            delivery_location=delivery_location,
            pickup_latitude=pickup_lat_value,
            pickup_longitude=pickup_lon_value,
            delivery_latitude=delivery_lat_value,
            delivery_longitude=delivery_lon_value,
            category=category,
            required_date=required_date_value,
        )

        return redirect('/errand/?success=1')

    return render(request, 'errand.html')


def nearby_rides(request):
    latitude = request.GET.get('latitude', '').strip()
    longitude = request.GET.get('longitude', '').strip()

    if not latitude or not longitude:
        return render(request, 'nearby_rides.html', {
            'error': 'Please enter your latitude and longitude.'
        })

    try:
        latitude = float(latitude)
        longitude = float(longitude)

        if not (-90 <= latitude <= 90):
            raise ValueError

        if not (-180 <= longitude <= 180):
            raise ValueError

    except (ValueError, TypeError):
        return render(request, 'nearby_rides.html', {
            'error': 'Please enter valid latitude and longitude values.'
        })

    user_point = Point(longitude, latitude, srid=4326)

    rides = Ride.objects.filter(
        pickup_point__distance_lte=(user_point, D(km=5))
    ).exclude(
        pickup_point__isnull=True
    ).annotate(
        distance=Distance('pickup_point', user_point)
    ).order_by('distance')

    return render(request, 'nearby_rides.html', {
        'rides': rides,
        'latitude': latitude,
        'longitude': longitude,
        'radius': 5,
    })


def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.save()

            StudentProfile.objects.create(
                user=user,
                enrollment_number=form.cleaned_data['enrollment_number']
            )

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            verification_path = reverse(
            'verify_email',
            kwargs={'uidb64': uid, 'token': token}
            )
            verification_url = request.build_absolute_uri(verification_path)

            send_mail(
            subject='Verify your CampusRide account',
            message=(
                f'Hi {user.username},\n\n'
                'Please verify your email by opening this link:\n'
                f'{verification_url}\n\n'
                'If you did not create this account, ignore this email.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
            )



def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'form': form})


def user_logout(request):
    if request.method == 'POST':
        logout(request)

    return redirect('home')

    
@login_required
def request_ride(request, ride_id):
    if request.method != 'POST':
        return redirect('find_ride')

    ride = get_object_or_404(Ride, id=ride_id)

    if ride.offered_by_id == request.user.id:
        messages.error(request, "You cannot request your own ride.")
        return redirect('find_ride')

    if ride.offered_by is None:
        messages.error(
            request,
            "This ride has no registered owner. Please choose another ride."
        )
        return redirect('find_ride')

    existing_request = RideRequest.objects.filter(
        ride=ride,
        requester=request.user
    ).first()

    if existing_request:
        messages.info(request, "You have already requested this ride.")
    else:
        RideRequest.objects.create(
            ride=ride,
            requester=request.user
        )
        messages.success(request, "Ride request sent successfully!")

    return redirect('find_ride')

    
@login_required
def my_ride_requests(request):
    rides = Ride.objects.filter(offered_by=request.user).prefetch_related(
        'ride_requests__requester'
    )
    return render(
        request,
        'my_ride_requests.html',
        {'rides': rides}
    )


@login_required
def respond_to_request(request, request_id):
    if request.method != 'POST':
        return redirect('my_ride_requests')

    ride_request = get_object_or_404(
        RideRequest,
        id=request_id,
        ride__offered_by=request.user
    )

    action = request.POST.get('action')

    if action == 'accept':
        ride_request.status = 'accepted'
        ride_request.save()
        messages.success(request, 'Ride request accepted successfully!')
    elif action == 'reject':
        ride_request.status = 'rejected'
        ride_request.save()
        messages.success(request, 'Ride request rejected.')
    else:
        messages.error(request, 'Invalid action.')

    return redirect('my_ride_requests')

    
def live_tracking(request):
    return render(request, "live_tracking.html")


def find_errands(request):
    errands = Errand.objects.all().order_by("-created_at")

    return render(request, "find_errands.html", {
        "errands": errands
    })


@login_required
@require_POST
def accept_errand(request, errand_id):
    errand = get_object_or_404(Errand, id=errand_id)

    if errand.status == 'available':
        errand.status = 'accepted'
        errand.accepted_by = request.user
        errand.save(update_fields=['status', 'accepted_by'])

    return redirect('find_errands')



def verify_email(request, uidb64, token):
    User = get_user_model()

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])

        return render(
            request,
            'email_verified.html',
            {'message': 'Your email has been verified! You can now log in.'}
        )

    return render(
        request,
        'email_verified.html',
        {'message': 'This verification link is invalid or has expired.'}
    )
