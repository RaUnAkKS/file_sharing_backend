from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwner
from django.shortcuts import get_object_or_404

class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        files = request.FILES.getlist("files")
        if not files:
            return Response({"error":"No files provided"},status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_files = []

        for file in files:
            data = {
                'file' : file,
                'content_type' : request.data.get('content_type','other')
            }
            serializer = FileUploadSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            file_instance = serializer.save(owner=request.user)
            uploaded_files.insert(0,FileListSerializer(file_instance).data)
        return Response({"message":"File uploaded successfully","files":uploaded_files},status=status.HTTP_201_CREATED)

class UserFileListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        files = File.objects.filter(owner=request.user,is_active=True)
        serializer = FileListSerializer(files,many=True)
        return Response(serializer.data)

class FileDeleteView(APIView):
    permission_classes = [IsAuthenticated,IsOwner]

    def get_object(self):
        return get_object_or_404(File,id=self.kwargs.get('file_id'))
        
    def delete(self,request, file_id):
        file = self.get_object()
        file.is_active = False
        file.save(update_fields=['is_active'])
        return Response({"message":"File deleted successfully"},status=status.HTTP_200_OK)

class FileDeleteAllView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        files = File.objects.filter(owner=request.user, is_active=True)
        count = files.count()
        files.update(is_active=False)
        return Response({"message": f"{count} files deleted successfully"}, status=status.HTTP_200_OK)