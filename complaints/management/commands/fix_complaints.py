from django.core.management.base import BaseCommand

from complaints.models import Complaint


class Command(BaseCommand):
    help = "DRAFT durumundaki şikayetleri SUBMITTED yapar"

    def handle(self, *args, **options):
        # DRAFT durumundaki şikayetleri bul
        draft_complaints = Complaint.objects.filter(status="DRAFT")
        count = draft_complaints.count()

        self.stdout.write(f"DRAFT durumunda {count} şikayet bulundu")

        if count > 0:
            # SUBMITTED yap
            updated = draft_complaints.update(status="SUBMITTED")
            self.stdout.write(
                self.style.SUCCESS(f"{updated} şikayet SUBMITTED durumuna güncellendi")
            )

        # Durumu kontrol et
        self.stdout.write("\n=== Şikayet Durumları ===")
        for complaint in Complaint.objects.all()[:10]:
            self.stdout.write(
                f"ID: {complaint.pk} | {complaint.title[:30]}... | "
                f"Durum: {complaint.status} | Geri çekilebilir: {complaint.can_withdraw}"
            )
