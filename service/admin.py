from django.contrib import admin
from .models import UserProfile, Service, Workshop, ServiceBooking, Review, Payment


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username', 'user__email')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('icon', 'name', 'price', 'duration', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active',)


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'total_slots', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')
    list_editable = ('is_active',)


@admin.register(ServiceBooking)
class ServiceBookingAdmin(admin.ModelAdmin):
    list_display = ('customer', 'service', 'workshop', 'car_model', 'appointment_date', 'status', 'created_at')
    list_filter = ('status', 'service', 'workshop', 'payment_status')
    search_fields = ('customer__username', 'car_model', 'car_number')
    list_editable = ('status',)
    ordering = ('-created_at',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'booking', 'amount', 'payment_method', 'transaction_id', 'payment_status', 'payment_date')
    list_filter = ('payment_method', 'payment_status')
    search_fields = ('user__username', 'transaction_id', 'booking__id')
    readonly_fields = ('payment_date',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('booking', 'rating', 'created_at')
    list_filter = ('rating',)
