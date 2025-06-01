from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Room, Participant
from .serializers import RoomSerializer
from django.conf import settings
import uuid

class CreateRoomView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        room_id = str(uuid.uuid4())[:8]
        room = Room.objects.create(room_id=room_id, host=request.user)
        return Response(RoomSerializer(room).data)


class WebRTCConfigView(APIView):
    def get(self, request):
        return Response(settings.WEBRTC_CONFIG)

