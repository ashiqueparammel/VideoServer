from django.urls import path
from .views import *

urlpatterns = [
    path('create-room/', CreateRoomView.as_view()),
    path('config/', WebRTCConfigView.as_view()),
]
