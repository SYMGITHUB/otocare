"""Seed script — run with: python seed_data.py"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otocare.settings')
django.setup()

from django.contrib.auth.models import User
from service.models import Service, Workshop

# Create superuser
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@otocare.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    u = User.objects.get(username='admin')
    u.set_password('admin123')
    u.save()
    print('Superuser password reset to: admin123')

# Services
services = [
    ('🛢️', 'Oil Change', 'Complete engine oil replacement with quality oil and filter change to keep your engine running smoothly.', 799, '45 mins'),
    ('⚙️', 'Engine Check', 'Full engine diagnostic scan to identify issues, performance tuning, and detailed health report.', 1299, '1.5 hours'),
    ('🛞', 'Tyre Replacement', 'Replacement of worn-out tyres with balancing and wheel alignment check for safer drives.', 2499, '1 hour'),
    ('🔧', 'Full Service', 'Comprehensive vehicle service: oil, filters, brakes, fluids, and complete multi-point inspection.', 4999, '4 hours'),
    ('💨', 'AC Service', 'Air conditioning system deep cleaning, refilling refrigerant gas, and performance check.', 1499, '1.5 hours'),
    ('🔋', 'Battery Check & Replace', 'Battery health diagnosis and replacement with a high-performance battery with warranty.', 3499, '30 mins'),
    ('🧹', 'Deep Cleaning', 'Interior and exterior deep cleaning, polishing, and protective wax coating for a showroom finish.', 1999, '3 hours'),
    ('🔩', 'Brake Service', 'Brake pads, discs inspection/replacement, brake fluid flush for maximum stopping power.', 2199, '2 hours'),
]
for icon, name, desc, price, dur in services:
    obj, created = Service.objects.get_or_create(name=name, defaults={
        'icon': icon, 'description': desc, 'price': price,
        'duration': dur, 'is_active': True
    })
    print(f"Service: {name} — {'created' if created else 'already exists'}")

# Workshops
workshops = [
    ('OTO DriveCare - Main Branch', 'Shop No. 12, MG Road, Pune, Maharashtra - 411001', '020-12345678', 'main@otocare.com', 12),
    ('OTO DriveCare - Kothrud Centre', 'Plot 45, Karve Road, Kothrud, Pune - 411038', '020-87654321', 'kothrud@otocare.com', 8),
    ('OTO DriveCare - Hadapsar Hub', 'Sector 7, MIDC, Hadapsar, Pune - 411028', '020-99887766', 'hadapsar@otocare.com', 10),
]
for name, addr, phone, email, slots in workshops:
    obj, created = Workshop.objects.get_or_create(name=name, defaults={
        'address': addr, 'phone': phone, 'email': email,
        'total_slots': slots, 'is_active': True
    })
    print(f"Workshop: {name} — {'created' if created else 'already exists'}")

print('\n=== SEED COMPLETE ===')
print(f'  Services: {Service.objects.count()}')
print(f'  Workshops: {Workshop.objects.count()}')
