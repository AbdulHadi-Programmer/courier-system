"""
Management command: seed fake data for local testing/demo.

Usage:
    python manage.py seed_data
    python manage.py seed_data --flush   (wipes old seeded data first)

Creates:
    - ~28 customers, 5 staff (password for ALL seeded users: pass1234)
    - 1-3 saved addresses per customer (mix of from/to)
    - 2-6 shipments per customer, each with a realistic status + a full
      StatusUpdate history matching that status (so the tracking timeline
      looks real, not just a single row).
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from addresses.models import Address
from shipments.models import Shipment, StatusUpdate
from shipments.services import (
    calculate_price, STATUS_FLOW, STATUS_LOCATIONS, STATUS_NOTES,
)

PASSWORD = 'pass1234'

FIRST_NAMES = [
    'Ahmed', 'Ali', 'Bilal', 'Danish', 'Fahad', 'Hamza', 'Imran', 'Junaid',
    'Kamran', 'Mudassar', 'Naveed', 'Omar', 'Qasim', 'Rashid', 'Saad',
    'Tariq', 'Usman', 'Waqas', 'Yasir', 'Zeeshan',
    'Ayesha', 'Bushra', 'Fatima', 'Hina', 'Iqra', 'Komal', 'Mahnoor',
    'Nida', 'Rabia', 'Sana', 'Tania', 'Zara', 'Areeba', 'Maham',
]
LAST_NAMES = [
    'Khan', 'Siddiqui', 'Sheikh', 'Qureshi', 'Malik', 'Baig', 'Raza',
    'Hussain', 'Abbasi', 'Farooqi', 'Memon', 'Soomro', 'Chaudhry', 'Iqbal',
]

# Completely separate name pool for RECEIVERS, so a receiver can never end up
# with the exact same first+last name as the sender/customer.
RECEIVER_FIRST_NAMES = [
    'Asad', 'Babar', 'Farhan', 'Ghulam', 'Haris', 'Ibrahim', 'Jawad',
    'Kashif', 'Luqman', 'Mansoor', 'Noman', 'Owais', 'Rehan', 'Shahzad',
    'Talha', 'Umar', 'Wahab', 'Yusuf', 'Zafar', 'Aamir',
    'Amna', 'Beenish', 'Farah', 'Ghazala', 'Huma', 'Javeria', 'Kiran',
    'Laiba', 'Mehwish', 'Noreen', 'Saba', 'Tahira', 'Uzma',
]
RECEIVER_LAST_NAMES = [
    'Aslam', 'Bukhari', 'Cheema', 'Dar', 'Effendi', 'Gondal', 'Hashmi',
    'Jafri', 'Lodhi', 'Mughal', 'Niazi', 'Pirzada', 'Rizvi', 'Syed',
]
CITIES = [
    'Karachi', 'Lahore', 'Islamabad', 'Faisalabad', 'Multan', 'Hyderabad',
    'Peshawar', 'Quetta', 'Sialkot', 'Rawalpindi', 'Gujranwala',
]
AREA_LABELS = ['Home', 'Office', 'Warehouse', 'Shop', 'Branch Office']
STREETS = [
    'Block 4, Gulshan-e-Iqbal', 'DHA Phase 5', 'North Nazimabad Block C',
    'Clifton Block 2', 'Johar Town Phase 1', 'F-10 Markaz',
    'Saddar Cantt', 'Model Town', 'Bahadurabad', 'PECHS Block 6',
]
PACKAGE_TYPES = ['document', 'parcel', 'fragile', 'bulk']
SERVICE_TYPES = ['express', 'standard', 'economy']
DESCRIPTIONS = [
    'Mobile accessories', 'Documents', 'Clothing', 'Books', 'Electronics',
    'Gift item', 'Spare parts', 'Cosmetics', 'Kitchenware', '',
]


def rand_phone():
    return f"03{random.randint(0, 9)}{random.randint(1000000, 9999999)}"


class Command(BaseCommand):
    help = 'Seed the database with realistic fake customers, staff, addresses, and shipments.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Delete previously seeded data (matched by username prefix) before creating new data.',
        )
        parser.add_argument(
            '--customers', type=int, default=28, help='Number of customers to create (default 28).',
        )
        parser.add_argument(
            '--staff', type=int, default=5, help='Number of staff to create (default 5).',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['flush']:
            self._flush()

        n_customers = options['customers']
        n_staff = options['staff']

        customers = self._create_users(n_customers, role='customer', prefix='cust')
        staff = self._create_users(n_staff, role='staff', prefix='staff')

        self.stdout.write(self.style.SUCCESS(
            f'Created/found {len(customers)} customers and {len(staff)} staff. Password for all: {PASSWORD}'
        ))

        total_addresses = 0
        total_shipments = 0
        for customer in customers:
            total_addresses += self._create_addresses(customer)
            total_shipments += self._create_shipments(customer)

        self.stdout.write(self.style.SUCCESS(
            f'Created {total_addresses} addresses and {total_shipments} shipments.'
        ))
        self.stdout.write(self.style.SUCCESS('Seeding complete.'))
        self.stdout.write(
            f'Sample login -> username: cust01..cust{n_customers:02d} or staff01..staff{n_staff:02d}  |  password: {PASSWORD}'
        )

    def _flush(self):
        deleted_users = User.objects.filter(username__startswith='cust').count() + \
            User.objects.filter(username__startswith='staff').count()
        User.objects.filter(username__startswith='cust').delete()
        User.objects.filter(username__startswith='staff').delete()
        self.stdout.write(self.style.WARNING(
            f'Flushed {deleted_users} previously seeded users (their addresses/shipments cascade-deleted too).'
        ))

    def _create_users(self, count, role, prefix):
        created = []
        for i in range(1, count + 1):
            username = f'{prefix}{i:02d}'
            existing = User.objects.filter(username=username).first()
            if existing:
                created.append(existing)
                continue
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            city = random.choice(CITIES)
            user = User(
                username=username,
                first_name=first,
                last_name=last,
                email=f'{username}@example.com',
                role=role,
                phone=rand_phone(),
                city=city,
                address=f'{random.choice(STREETS)}, {city}',
                is_active=True,
            )
            user.set_password(PASSWORD)
            user.save()
            created.append(user)
        return created

    def _create_addresses(self, user):
        # Skip if this user already has addresses (e.g. command run twice)
        if Address.objects.filter(user=user).exists():
            return 0
        count = 0
        for addr_type in ('from', 'to'):
            n = random.randint(1, 2)
            for _ in range(n):
                city = random.choice(CITIES)
                Address.objects.create(
                    user=user,
                    address_type=addr_type,
                    full_name=(f'{user.first_name} {user.last_name}' if addr_type == 'from'
                               else f'{random.choice(RECEIVER_FIRST_NAMES)} {random.choice(RECEIVER_LAST_NAMES)}'),
                    phone=rand_phone(),
                    city=city,
                    address=f'{random.choice(STREETS)}, {city}',
                    label=random.choice(AREA_LABELS),
                )
                count += 1
        return count

    def _create_shipments(self, customer):
        # Skip if this user already has shipments (e.g. command run twice)
        if Shipment.objects.filter(sender=customer).exists():
            return 0

        count = 0
        n_shipments = random.randint(2, 6)
        from_addrs = list(Address.objects.filter(user=customer, address_type='from'))
        to_addrs = list(Address.objects.filter(user=customer, address_type='to'))
        if not from_addrs or not to_addrs:
            return 0

        for _ in range(n_shipments):
            from_addr = random.choice(from_addrs)
            to_addr = random.choice(to_addrs)

            weight = Decimal(str(round(random.uniform(0.5, 25), 2)))
            quantity = random.randint(1, 5)
            package_type = random.choice(PACKAGE_TYPES)
            service_type = random.choice(SERVICE_TYPES)

            final_status = random.choices(
                ['pending', 'picked_up', 'in_transit', 'out_for_delivery',
                 'delivered', 'cancelled', 'returned'],
                weights=[15, 10, 15, 10, 40, 7, 3],
                k=1,
            )[0]

            tracking_number = self._unique_tracking_number()
            price = calculate_price(weight, quantity, package_type, service_type)

            days_ago = random.randint(0, 25)
            created_at = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            eta = (created_at + timedelta(days=random.randint(1, 7))).date()

            shipment = Shipment.objects.create(
                tracking_number=tracking_number,
                sender=customer,
                sender_name=from_addr.full_name,
                sender_phone=from_addr.phone,
                sender_address=from_addr.address,
                sender_city=from_addr.city,
                receiver_name=to_addr.full_name,
                receiver_phone=to_addr.phone,
                receiver_address=to_addr.address,
                receiver_city=to_addr.city,
                weight=weight,
                quantity=quantity,
                package_type=package_type,
                service_type=service_type,
                description=random.choice(DESCRIPTIONS),
                price=price,
                estimated_delivery=eta,
                status=final_status,
            )
            Shipment.objects.filter(pk=shipment.pk).update(created_at=created_at, updated_at=created_at)

            self._build_status_history(shipment, final_status, created_at)
            count += 1
        return count

    def _build_status_history(self, shipment, final_status, created_at):
        """Builds a believable StatusUpdate trail leading up to final_status,
        with increasing timestamps so the tracking timeline reads correctly."""
        ts = created_at
        pending = StatusUpdate.objects.create(
            shipment=shipment, status='pending',
            location=shipment.sender_city,
            notes='Shipment created and is awaiting pickup.',
        )
        StatusUpdate.objects.filter(pk=pending.pk).update(timestamp=ts)

        if final_status == 'cancelled':
            ts += timedelta(hours=random.randint(1, 12))
            cancelled = StatusUpdate.objects.create(
                shipment=shipment, status='cancelled', location='-',
                notes=STATUS_NOTES['cancelled'],
            )
            StatusUpdate.objects.filter(pk=cancelled.pk).update(timestamp=ts)
            return

        target = 'delivered' if final_status == 'returned' else final_status
        if target in STATUS_FLOW:
            idx = STATUS_FLOW.index(target)
            for step in STATUS_FLOW[1:idx + 1]:
                ts += timedelta(hours=random.randint(6, 30))
                u = StatusUpdate.objects.create(
                    shipment=shipment, status=step,
                    location=STATUS_LOCATIONS.get(step, ''),
                    notes=STATUS_NOTES.get(step, ''),
                )
                StatusUpdate.objects.filter(pk=u.pk).update(timestamp=ts)

        if final_status == 'returned':
            ts += timedelta(hours=random.randint(6, 24))
            ret = StatusUpdate.objects.create(
                shipment=shipment, status='returned',
                location=STATUS_LOCATIONS['returned'],
                notes=STATUS_NOTES['returned'],
            )
            StatusUpdate.objects.filter(pk=ret.pk).update(timestamp=ts)

    def _unique_tracking_number(self):
        while True:
            tn = 'TRK' + ''.join(random.choices('0123456789', k=12))
            if not Shipment.objects.filter(tracking_number=tn).exists():
                return tn