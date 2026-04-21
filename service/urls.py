from django.urls import path
from . import views

urlpatterns = [
    # ── Public ────────────────────────────────────────────────────────────────
    path('', views.home, name='home'),
    path('register/', views.register_page, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('services/', views.services_list, name='services'),
    path('emergency/', views.emergency, name='emergency'),

    # ── Customer (login required) ──────────────────────────────────────────
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('book-service/', views.book_service, name='book_service'),
    path('booking-history/', views.booking_history, name='booking_history'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('review/<int:booking_id>/', views.add_review, name='add_review'),
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('process-payment/<int:booking_id>/', views.process_payment, name='process_payment'),

    # ── Admin ─────────────────────────────────────────────────────────────
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Users
    path('admin-users/', views.admin_users, name='admin_users'),
    path('admin-delete-user/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),

    # Services
    path('admin-services/', views.admin_services, name='admin_services'),
    path('admin-add-service/', views.admin_add_service, name='admin_add_service'),
    path('admin-edit-service/<int:service_id>/', views.admin_edit_service, name='admin_edit_service'),
    path('admin-delete-service/<int:service_id>/', views.admin_delete_service, name='admin_delete_service'),

    # Workshops
    path('admin-workshops/', views.admin_workshops, name='admin_workshops'),
    path('admin-add-workshop/', views.admin_add_workshop, name='admin_add_workshop'),
    path('admin-edit-workshop/<int:workshop_id>/', views.admin_edit_workshop, name='admin_edit_workshop'),
    path('admin-delete-workshop/<int:workshop_id>/', views.admin_delete_workshop, name='admin_delete_workshop'),

    # Bookings
    path('admin-bookings/', views.admin_bookings, name='admin_bookings'),
    path('admin-update-booking/<int:booking_id>/', views.admin_update_booking, name='admin_update_booking'),

    # Payments
    path('admin-payments/', views.admin_payments, name='admin_payments'),
    path('admin-update-payment/<int:payment_id>/', views.admin_update_payment, name='admin_update_payment'),
    path('payment/success/<int:booking_id>/', views.payment_success, name='payment_success'),
    path('payment/cancelled/<int:booking_id>/', views.payment_cancelled, name='payment_cancelled'),
]
