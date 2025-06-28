# # api/views.py
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .serializers import AudioUploadSerializer
# import whisper
# import os
# import uuid

# model = whisper.load_model("tiny")  # or "tiny", "small", etc.

# class TranscribeAudio(APIView):
#     def post(self, request, *args, **kwargs):
#         serializer = AudioUploadSerializer(data=request.data)
#         if serializer.is_valid():
#             file = serializer.validated_data['file']

#             ext = os.path.splitext(file.name)[1]  # Keep original extension (.mp3, .m4a)
#             filename = f"{uuid.uuid4().hex}{ext}"
#             save_path = os.path.join("temp", filename)
#             os.makedirs("temp", exist_ok=True)

#             with open(save_path, 'wb+') as destination:
#                 for chunk in file.chunks():
#                     destination.write(chunk)

#             try:
#                 result = model.transcribe(save_path)
#                 os.remove(save_path)
#                 return Response({"text": result["text"]}, status=status.HTTP_200_OK)
#             except Exception as e:
#                 return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)












# import speech_recognition as sr
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.parsers import MultiPartParser
# import os

# class TranscribeAudio(APIView):
#     parser_classes = [MultiPartParser]

#     def post(self, request):
#         audio_file = request.FILES.get("audio")
#         if not audio_file:
#             return Response({"error": "No audio file provided."}, status=400)

#         file_path = f"temp_{audio_file.name}"
#         with open(file_path, 'wb+') as f:
#             for chunk in audio_file.chunks():
#                 f.write(chunk)

#         recognizer = sr.Recognizer()
#         try:
#             with sr.AudioFile(file_path) as source:
#                 audio_data = recognizer.record(source)
#                 text = recognizer.recognize_google(audio_data)
#                 os.remove(file_path)
#                 return Response({"text": text})

#         except sr.UnknownValueError:
#             os.remove(file_path)
#             return Response({"error": "Could not understand audio."}, status=400)
#         except sr.RequestError as e:
#             os.remove(file_path)
#             return Response({"error": f"Google API error: {e}"}, status=500)




import os
import uuid
import wave
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.conf import settings
from vosk import Model, KaldiRecognizer

# Use absolute path to the vosk model folder

class TranscribeAudio(APIView):
    def post(self, request, *args, **kwargs):
        VOSK_MODEL_PATH = ''
        lang = request.data.get("lang")  

        if lang == "us en":
            VOSK_MODEL_PATH = os.path.join(settings.BASE_DIR, "model-small-en-us")
        elif lang == "in en":
            VOSK_MODEL_PATH = os.path.join(settings.BASE_DIR, "model-small-en-in")
        else:
            return Response({"error": "Unsupported language."}, status=400)

        try:
            vosk_model = Model(VOSK_MODEL_PATH)
        except Exception as e:
            return Response({"error": f"Model load failed: {e}"}, status=500)

        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided"}, status=400)

        ext = os.path.splitext(file.name)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        save_path = os.path.join("temp", filename)
        os.makedirs("temp", exist_ok=True)

        with open(save_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        # Convert to WAV
        wav_path = save_path.replace(ext, ".wav")
        os.system(f"ffmpeg -y -i \"{save_path}\" -ac 1 -ar 16000 \"{wav_path}\"")

        try:
            wf = wave.open(wav_path, "rb")
            rec = KaldiRecognizer(vosk_model, wf.getframerate())

            result = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    result += res.get("text", "") + " "
            wf.close()

            return Response({"text": result.strip()})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
        finally:
            if os.path.exists(save_path):
                os.remove(save_path)
            if os.path.exists(wav_path):
                os.remove(wav_path)
