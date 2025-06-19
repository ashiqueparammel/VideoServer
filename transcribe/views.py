# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AudioUploadSerializer
import whisper
import os
import uuid

model = whisper.load_model("base")  # or "tiny", "small", etc.

class TranscribeAudio(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AudioUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']

            ext = os.path.splitext(file.name)[1]  # Keep original extension (.mp3, .m4a)
            filename = f"{uuid.uuid4().hex}{ext}"
            save_path = os.path.join("temp", filename)
            os.makedirs("temp", exist_ok=True)

            with open(save_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            try:
                result = model.transcribe(save_path)
                os.remove(save_path)
                return Response({"text": result["text"]}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
