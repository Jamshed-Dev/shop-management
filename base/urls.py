from django.urls import path
from . import views
urlpatterns = [
    path("download/",views.zip_downloader,name="download-media")
]
