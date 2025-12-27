from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import FirmProfile, UserAccount

class Command(BaseCommand):
    help = 'Resets specific test data to fix unique constraint conflicts'

    def handle(self, *args, **options):
        target_domain = 'abcd.com'
        target_user_id = 6

        try:
            with transaction.atomic():
                # 1. Remove the conflicting domain
                deleted_count, _ = FirmProfile.objects.filter(domain=target_domain).delete()
                
                # 2. Reset the specific test user
                user = UserAccount.objects.filter(id=target_user_id).first()
                if user:
                    user.firm = None
                    user.save()
                    user_status = f"User {target_user_id} unlinked."
                else:
                    user_status = "User not found."

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully deleted {deleted_count} profiles. {user_status}"
                    )
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during reset: {e}"))