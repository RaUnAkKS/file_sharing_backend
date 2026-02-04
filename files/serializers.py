from .models import *
from rest_framework import serializers

class FileListSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id','owner','file','original_filename','file_size','content_type','is_active','uploaded_at']
        read_only_fields = ['id','owner','original_filename','file_size','uploaded_at']

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['file','content_type',]

    def validate(self,data):
        file = data.get('file')
        if not file:
            raise serializers.ValidationError("File is required")
        file_size = file.size
        if file_size >1024*1024*5:
            raise serializers.ValidationError("File size should be less than 5MB")
        return data

    def create(self,validated_data):
        file = validated_data.get('file')
        validated_data['original_filename'] = file.name
        validated_data['file_size'] = file.size
        return super().create(validated_data)