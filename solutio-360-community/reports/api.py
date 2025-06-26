import csv

from django.http import HttpResponse

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Report
from .serializers import ReportSerializer


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]

    @action(detail=False, methods=["get"], url_path="export/csv")
    def export_csv(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=raporlar.csv"
        writer = csv.writer(response)
        writer.writerow(["Başlık", "Şablon", "Durum", "Oluşturulma"])
        for r in self.get_queryset():
            writer.writerow(
                [
                    r.title,
                    str(r.template.template_type) if r.template else "",
                    str(r.status),
                    r.created_at.strftime("%d.%m.%Y %H:%M"),
                ]
            )
        return response
