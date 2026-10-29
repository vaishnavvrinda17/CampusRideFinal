
from django.contrib import admin
from .models import Ride, Errand
from django.contrib import admin
from .models import Ride, Errand, RideRequest


admin.site.register(RideRequest)


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = (
        'student_name',
        'pickup_location',
        'destination',
        'travel_date',
        'travel_time',
        'available_seats',
    )
    search_fields = (
        'student_name',
        'pickup_location',
        'destination',
    )
    list_filter = ('travel_date',)


@admin.register(Errand)
class ErrandAdmin(admin.ModelAdmin):
    list_display = (
        'student_name',
        'category',
        'task_description',
        'pickup_location',
        'delivery_location',
        'required_date',
    )
    search_fields = (
        'student_name',
        'task_description',
        'pickup_location',
        'delivery_location',
    )
    list_filter = ('category', 'required_date')
