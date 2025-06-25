from django.core.management.base import BaseCommand

from complaints.models import Complaint


class Command(BaseCommand):
    help = "Fix can_be_withdrawn field for all complaints"

    def handle(self, *args, **options):
        self.stdout.write("=== Şikayet can_be_withdrawn Alanını Düzeltme ===\n")

        # Tüm şikayetleri güncelle
        complaints = Complaint.objects.all()
        updated_count = 0

        for complaint in complaints:
            if not complaint.can_be_withdrawn:
                complaint.can_be_withdrawn = True
                complaint.save(update_fields=["can_be_withdrawn"])
                updated_count += 1
                self.stdout.write(
                    f"Güncellendi: ID {complaint.pk} - {complaint.title[:30]}"
                )

        self.stdout.write(f"\nToplam {updated_count} şikayet güncellendi.")

        # Kontrol et
        self.stdout.write("\n=== Kontrol ===")
        for c in complaints[:5]:
            self.stdout.write(
                f"ID: {c.pk} | can_withdraw: {c.can_withdraw} | status: {c.status}"
            )

        self.stdout.write(self.style.SUCCESS("İşlem tamamlandı!"))
