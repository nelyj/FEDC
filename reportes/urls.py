from django.urls import path

from .views import (
	ReportesCreateListView,
)


app_name = 'reportes'
urlpatterns = [
    path('reportes/', ReportesCreateListView.as_view(), name='crear'),

]