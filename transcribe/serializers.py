from rest_framework import serializers

class AudioUploadSerializer(serializers.Serializer):
    file = serializers.FileField()