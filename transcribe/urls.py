# api/urls.py

from django.urls import path
from .views import *

urlpatterns = [
    # path('transcribe/', TranscribeAudio.as_view(), name='transcribe-audio'),
    path('transcribe/', TranscribeAudio.as_view(), name="transcribe-audio"),
]
