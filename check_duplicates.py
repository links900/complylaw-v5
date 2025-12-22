import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings') # Ensure this matches your project name
django.setup()

from users.models import FirmProfile

def find_conflicts():
    email = 'complylawtestuser1@yopmail.com'
    domain = 'alhambra-solutions.com'
    phone = '+923215151188'

    print("--- Searching for Conflicts ---")
    
    # Check Email
    firms_email = FirmProfile.objects.filter(email=email)
    print(f"Firms with email {email}: {[f.id for f in firms_email]}")

    # Check Domain
    firms_domain = FirmProfile.objects.filter(domain=domain)
    print(f"Firms with domain {domain}: {[f.id for f in firms_domain]}")

    # Check Phone
    firms_phone = FirmProfile.objects.filter(phone=phone)
    print(f"Firms with phone {phone}: {[f.id for f in firms_phone]}")

if __name__ == "__main__":
    find_conflicts()