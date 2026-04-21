from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from functools import wraps
from .models import Service, Workshop, ServiceBooking, Review, UserProfile, Payment
import stripe
from django.conf import settings
from django.urls import reverse


# ─── Decorators ──────────────────────────────────────────────────────────────

def admin_required(view_func):
    """Decorator: user must be authenticated staff member."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login')
        if not request.user.is_staff:
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Public Pages ─────────────────────────────────────────────────────────────

def home(request):
    services = Service.objects.filter(is_active=True)[:6]
    return render(request, 'Home.html', {'services': services})


def emergency(request):
    return render(request, 'emergency.html')


def services_list(request):
    query = request.GET.get('q', '').strip()
    services = Service.objects.filter(is_active=True)
    if query:
        services = services.filter(name__icontains=query)
    return render(request, 'services.html', {'services': services, 'query': query})


# ─── Customer Auth ────────────────────────────────────────────────────────────

def register_page(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not all([username, email, password1, password2]):
            error = "All fields are required."
        elif password1 != password2:
            error = "Passwords do not match."
        elif len(password1) < 6:
            error = "Password must be at least 6 characters."
        elif User.objects.filter(username=username).exists():
            error = "Username is already taken."
        elif User.objects.filter(email=email).exists():
            error = "An account with this email already exists."
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            UserProfile.objects.get_or_create(user=user)
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
    return render(request, 'register.html', {'error': error})


def login_view(request):
    error = None
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('customer_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('customer_dashboard')
        else:
            error = "Invalid username or password."
    return render(request, 'Customer Login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('home')


# ─── Customer Dashboard & Booking ────────────────────────────────────────────

@login_required(login_url='/login/')
def customer_dashboard(request):
    recent_bookings = ServiceBooking.objects.filter(customer=request.user).order_by('-created_at')[:5]
    featured_services = Service.objects.filter(is_active=True)[:4]
    total_bookings = ServiceBooking.objects.filter(customer=request.user).count()
    pending = ServiceBooking.objects.filter(customer=request.user, status='Pending').count()
    completed = ServiceBooking.objects.filter(customer=request.user, status='Completed').count()
    return render(request, 'customer_dashboard.html', {
        'recent_bookings': recent_bookings,
        'featured_services': featured_services,
        'total_bookings': total_bookings,
        'pending': pending,
        'completed': completed,
    })


@login_required(login_url='/login/')
def book_service(request):
    services = Service.objects.filter(is_active=True)
    workshops = Workshop.objects.filter(is_active=True)
    error = None
    success = False
    preselected_service = request.GET.get('service_id', '')

    if request.method == 'POST':
        service_id = request.POST.get('service_id', '').strip()
        workshop_id = request.POST.get('workshop_id', '').strip()
        car_model = request.POST.get('car_model', '').strip()
        car_number = request.POST.get('car_number', '').strip()
        appointment_date = request.POST.get('appointment_date', '').strip()
        appointment_time = request.POST.get('appointment_time', '').strip()
        notes = request.POST.get('notes', '').strip()

        if not all([service_id, workshop_id, car_model, car_number, appointment_date, appointment_time]):
            error = "Please fill in all required fields."
        else:
            try:
                service = Service.objects.get(id=service_id, is_active=True)
                workshop = Workshop.objects.get(id=workshop_id, is_active=True)
                ServiceBooking.objects.create(
                    customer=request.user,
                    service=service,
                    workshop=workshop,
                    car_model=car_model,
                    car_number=car_number,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    notes=notes,
                    status='Pending',
                )
                success = True
            except Service.DoesNotExist:
                error = "Selected service not found."
            except Workshop.DoesNotExist:
                error = "Selected workshop not found."
            except Exception as e:
                error = f"Something went wrong: {str(e)}"

    return render(request, 'bookservice.html', {
        'services': services,
        'workshops': workshops,
        'error': error,
        'success': success,
        'preselected_service': preselected_service,
    })


@login_required(login_url='/login/')
def booking_history(request):
    bookings = ServiceBooking.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'booking_history.html', {'bookings': bookings})


@login_required(login_url='/login/')
def cancel_booking(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id, customer=request.user)
    if request.method == 'POST':
        if booking.status == 'Pending':
            booking.status = 'Cancelled'
            booking.save()
            messages.success(request, "Booking cancelled successfully.")
        else:
            messages.error(request, "Only pending bookings can be cancelled.")
    return redirect('booking_history')


@login_required(login_url='/login/')
def add_review(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id, customer=request.user)
    error = None

    if booking.status != 'Completed':
        messages.error(request, "You can only review completed bookings.")
        return redirect('booking_history')

    if hasattr(booking, 'review'):
        messages.info(request, "You have already reviewed this booking.")
        return redirect('booking_history')

    if request.method == 'POST':
        rating = request.POST.get('rating', '').strip()
        comment = request.POST.get('comment', '').strip()
        if not rating or not comment:
            error = "Please provide both a rating and a comment."
        elif not rating.isdigit() or not (1 <= int(rating) <= 5):
            error = "Rating must be between 1 and 5."
        else:
            Review.objects.create(booking=booking, rating=int(rating), comment=comment)
            messages.success(request, "Thank you for your feedback!")
            return redirect('booking_history')

    return render(request, 'feedback.html', {'booking': booking, 'error': error})


@login_required(login_url='/login/')
def payment_page(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id, customer=request.user)
    
    if booking.payment_status == 'Paid':
        messages.info(request, "This booking has already been paid.")
        return redirect('booking_history')

    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        transaction_id = request.POST.get('transaction_id')
        amount = request.POST.get('amount')

        if not all([payment_method, transaction_id, amount]):
            messages.error(request, "Please fill in all payment details.")
        else:
            Payment.objects.create(
                booking=booking,
                user=request.user,
                amount=amount,
                payment_method=payment_method,
                transaction_id=transaction_id,
                payment_status='Approved'
            )
            # Update booking status immediately
            booking.payment_status = 'Paid'
            booking.transaction_id = transaction_id
            booking.save()
            
            messages.success(request, "Payment details submitted successfully! Payment marked as Done.")
            return redirect('booking_history')

    return render(request, 'payment.html', {'booking': booking})


@login_required(login_url='/login/')
def process_payment(request, booking_id):
    """Initializes Stripe Checkout session for a booking."""
    booking = get_object_or_404(ServiceBooking, id=booking_id, customer=request.user)
    
    if booking.payment_status == 'Paid':
        messages.info(request, "This booking has already been paid.")
        return redirect('booking_history')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'upi'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': f"{booking.service.name} - {booking.car_model}",
                        'description': f"Workshop: {booking.workshop.name}",
                    },
                    'unit_amount': int(booking.service.price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('payment_success', args=[booking.id])) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse('payment_cancelled', args=[booking.id])),
            metadata={
                'booking_id': booking.id,
                'customer_email': request.user.email
            }
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        messages.error(request, f"Error initializing payment: {str(e)}")
        return redirect('booking_history')


@login_required(login_url='/login/')
def payment_success(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id, customer=request.user)
    session_id = request.GET.get('session_id')
    
    if session_id:
        booking.payment_status = 'Paid'
        booking.transaction_id = session_id
        booking.save()
        
    return render(request, 'payment_success.html', {'booking': booking})


@login_required(login_url='/login/')
def payment_cancelled(request, booking_id):
    messages.info(request, "Payment was cancelled.")
    return redirect('booking_history')
# ─── Admin Login ──────────────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user_list = User.objects.filter(email=email)
        if not user_list.exists():
            error = "Invalid email or password."
        else:
            authenticated_user = None
            for u in user_list:
                user = authenticate(request, username=u.username, password=password)
                if user is not None:
                    authenticated_user = user
                    break
            
            if authenticated_user is not None:
                if authenticated_user.is_staff:
                    login(request, authenticated_user)
                    return redirect('admin_dashboard')
                else:
                    error = "You do not have admin privileges."
            else:
                error = "Invalid email or password."
    return render(request, 'admin login.html', {'error': error})


# ─── Admin Dashboard ──────────────────────────────────────────────────────────

@admin_required
def admin_dashboard(request):
    total = ServiceBooking.objects.count()
    pending = ServiceBooking.objects.filter(status='Pending').count()
    approved = ServiceBooking.objects.filter(status='Approved').count()
    in_progress = ServiceBooking.objects.filter(status='In Progress').count()
    completed = ServiceBooking.objects.filter(status='Completed').count()
    
    
    recent_bookings = ServiceBooking.objects.select_related(
        'customer', 'service', 'workshop'
    ).order_by('-created_at')[:10]
    total_users = User.objects.filter(is_staff=False).count()
    total_services = Service.objects.filter(is_active=True).count()
    total_workshops = Workshop.objects.filter(is_active=True).count()

    # Pass the labels and data for the chart to JS
    return render(request, 'admin_dashboard.html', {
        'total': total,
        'pending': pending,
        'approved': approved,
        'in_progress': in_progress,
        'completed': completed,
        'recent_bookings': recent_bookings,
        'total_users': total_users,
        'total_services': total_services,
        'total_workshops': total_workshops,
    })




# ─── Admin Users ──────────────────────────────────────────────────────────────

@admin_required
def admin_users(request):
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'admin_users.html', {'users': users})


@admin_required
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id, is_staff=False)
    if request.method == 'POST':
        user.delete()
        messages.success(request, f"User '{user.username}' deleted.")
    return redirect('admin_users')


# ─── Admin Services ───────────────────────────────────────────────────────────

@admin_required
def admin_services(request):
    services = Service.objects.all().order_by('name')
    return render(request, 'admin_services.html', {'services': services})


@admin_required
def admin_add_service(request):
    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        price = request.POST.get('price', '').strip()
        duration = request.POST.get('duration', '').strip()
        icon = request.POST.get('icon', '🔧').strip() or '🔧'

        if not all([name, description, price, duration]):
            error = "All fields are required."
        else:
            try:
                Service.objects.create(
                    name=name, description=description,
                    price=float(price), duration=duration, icon=icon
                )
                messages.success(request, "Service added successfully.")
                return redirect('admin_services')
            except ValueError:
                error = "Price must be a valid number."

    return render(request, 'admin_add_service.html', {'error': error, 'action': 'Add'})


@admin_required
def admin_edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    error = None
    if request.method == 'POST':
        service.name = request.POST.get('name', '').strip()
        service.description = request.POST.get('description', '').strip()
        service.duration = request.POST.get('duration', '').strip()
        service.icon = request.POST.get('icon', '🔧').strip() or '🔧'
        service.is_active = request.POST.get('is_active') == 'on'
        price = request.POST.get('price', '').strip()

        if not all([service.name, service.description, price, service.duration]):
            error = "All fields are required."
        else:
            try:
                service.price = float(price)
                service.save()
                messages.success(request, "Service updated successfully.")
                return redirect('admin_services')
            except ValueError:
                error = "Price must be a valid number."

    return render(request, 'admin_add_service.html', {'error': error, 'service': service, 'action': 'Edit'})


@admin_required
def admin_delete_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        service.delete()
        messages.success(request, "Service deleted.")
    return redirect('admin_services')


# ─── Admin Workshops ──────────────────────────────────────────────────────────

@admin_required
def admin_workshops(request):
    workshops = Workshop.objects.all().order_by('name')
    return render(request, 'admin_workshops.html', {'workshops': workshops})


@admin_required
def admin_add_workshop(request):
    error = None
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        total_slots = request.POST.get('total_slots', '10').strip()

        if not all([name, address, phone]):
            error = "Name, address, and phone are required."
        else:
            try:
                Workshop.objects.create(
                    name=name, address=address, phone=phone,
                    email=email or None, total_slots=int(total_slots)
                )
                messages.success(request, "Workshop added successfully.")
                return redirect('admin_workshops')
            except ValueError:
                error = "Total slots must be a valid number."

    return render(request, 'admin_add_workshop.html', {'error': error, 'action': 'Add'})


@admin_required
def admin_edit_workshop(request, workshop_id):
    workshop = get_object_or_404(Workshop, id=workshop_id)
    error = None
    if request.method == 'POST':
        workshop.name = request.POST.get('name', '').strip()
        workshop.address = request.POST.get('address', '').strip()
        workshop.phone = request.POST.get('phone', '').strip()
        workshop.email = request.POST.get('email', '').strip() or None
        workshop.is_active = request.POST.get('is_active') == 'on'
        total_slots = request.POST.get('total_slots', '10').strip()

        if not all([workshop.name, workshop.address, workshop.phone]):
            error = "Name, address, and phone are required."
        else:
            try:
                workshop.total_slots = int(total_slots)
                workshop.save()
                messages.success(request, "Workshop updated successfully.")
                return redirect('admin_workshops')
            except ValueError:
                error = "Total slots must be a valid number."

    return render(request, 'admin_add_workshop.html', {'error': error, 'workshop': workshop, 'action': 'Edit'})


@admin_required
def admin_delete_workshop(request, workshop_id):
    workshop = get_object_or_404(Workshop, id=workshop_id)
    if request.method == 'POST':
        workshop.delete()
        messages.success(request, "Workshop deleted.")
    return redirect('admin_workshops')


# ─── Admin Bookings ───────────────────────────────────────────────────────────

@admin_required
def admin_bookings(request):
    status_filter = request.GET.get('status', '').strip()
    bookings = ServiceBooking.objects.select_related(
        'customer', 'service', 'workshop'
    ).order_by('-created_at')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    status_choices = ServiceBooking.STATUS_CHOICES
    return render(request, 'admin_bookings.html', {
        'bookings': bookings,
        'status_filter': status_filter,
        'status_choices': status_choices,
    })


@admin_required
def admin_update_booking(request, booking_id):
    booking = get_object_or_404(ServiceBooking, id=booking_id)
    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        valid_statuses = [s[0] for s in ServiceBooking.STATUS_CHOICES]
        if new_status in valid_statuses:
            booking.status = new_status
            booking.save()
            messages.success(request, f"Booking status updated to '{new_status}'.")
        else:
            messages.error(request, "Invalid status.")
    return redirect('admin_bookings')

@admin_required
def admin_payments(request):
    payments = Payment.objects.select_related('user', 'booking', 'booking__service', 'booking__workshop').order_by('-payment_date')
    total_revenue = sum(p.amount for p in payments if p.payment_status == 'Approved')
    return render(request, 'admin_payments.html', {
        'payments': payments,
        'total_revenue': total_revenue
    })

@admin_required
def admin_update_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Approved', 'Rejected']:
            payment.payment_status = new_status
            payment.save()
            if new_status == 'Approved':
                booking = payment.booking
                booking.payment_status = 'Paid'
                booking.save()
            messages.success(request, f"Payment {new_status} successfully.")
        else:
            messages.error(request, "Invalid status.")
    return redirect('admin_payments')