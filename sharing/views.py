from django.shortcuts import render
from django.utils import timezone
from .serializers import *
from .models import ShareLink
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .permissions import IsLinkOwner
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from files.models import File
import io
import zipfile
from django.http import HttpResponse
from django.shortcuts import get_list_or_404
from sharing.services.validation import check_validation
from .pagination import ShareLinkCursorPagination
from files.serializers import FileListSerializer
from files.pagination import FileCursorPagination


class CreateShareLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        serializer = ShareLinkCreateSerializer(data=request.data,context={'user':request.user})
        serializer.is_valid(raise_exception=True)
        share_link = serializer.save()
        return Response(ShareLinkDetailSerializer(share_link).data,status=status.HTTP_201_CREATED)

class ShareLinkDetailView(APIView):
    permission_classes = [IsAuthenticated,IsLinkOwner]

    def get(self,request,id):
        share_link = get_object_or_404(ShareLink,id=id)
        self.check_object_permissions(request,share_link)
        serializer = ShareLinkDetailSerializer(share_link)
        return Response(serializer.data)

class ShareLinkAccessView(APIView):
    permission_classes = []
    def post(self,request,id):
        share_link = get_object_or_404(ShareLink,id=id)
        serializer = ShareLinkAccessSerializer(data=request.data,context={'share_link':share_link})
        serializer.is_valid(raise_exception=True)
        
        if 'unlocked_links' not in request.session:
            request.session['unlocked_links'] = []
        request.session['unlocked_links'].append(str(id))
        request.session.modified = True
            
        return Response({"message":"Access granted"},status=status.HTTP_200_OK)

class ShareDownload(APIView):
    permission_classes = []
    def get(self,request,share_link_id):
        share_link = get_object_or_404(ShareLink,id=share_link_id)
        if(check_validation(share_link)==False):
            return Response({"message":"Link is expired or invalid"},status=status.HTTP_400_BAD_REQUEST)
        
        if share_link.password:
            unlocked_links = request.session.get('unlocked_links', [])
            if str(share_link_id) not in unlocked_links:
                 return Response({"message":"Password verification required"},status=status.HTTP_403_FORBIDDEN)
        
        files = share_link.files.all()
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer,'w',zipfile.ZIP_DEFLATED) as zip_file:
            for file_obj in files:
                try:
                    with file_obj.file.open('rb') as f:
                        zip_file.writestr(file_obj.original_filename, f.read())
                except Exception as e:
                    print(f"Error zipping file {file_obj.id}: {e}")
                    continue

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(),content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="shared_files.zip"'
        return response

class ShareLinkDeleteView(APIView):
    permission_classes = [IsAuthenticated,IsLinkOwner]
    def delete(self,request,share_link_id):
        share_link = get_object_or_404(ShareLink,id=share_link_id)
        self.check_object_permissions(request,share_link)
        share_link.is_active = False
        share_link.save(update_fields=['is_active'])
        return Response({"message":"Link deleted successfully"},status=status.HTTP_200_OK)

class ShareLinkStatusView(APIView):
    permission_classes = []
    def get(self, request, id):
        share_link = get_object_or_404(ShareLink, id=id)
        
        status_code = "valid"
        if not share_link.is_active:
            status_code = "inactive"
        elif share_link.expires_at and share_link.expires_at < timezone.now():
            status_code = "expired"
        elif share_link.download_count >= share_link.max_downloads:
            status_code = "limit_reached"
        unlocked_links = request.session.get('unlocked_links', [])
        is_unlocked = str(id) in unlocked_links

        return Response({
            "has_password": bool(share_link.password),
            "is_active": share_link.is_active,
            "status": status_code,
            "is_unlocked": is_unlocked
        })

class ShareLinklist(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        search_term = request.query_params.get('search',None)
        if search_term == "all" or search_term is None:
             share_links = ShareLink.objects.filter(created_by=request.user).order_by('-created_at')
        elif search_term == "active":
            share_links = ShareLink.objects.filter(created_by=request.user,is_active=True).order_by('-created_at')
        elif search_term == "inactive":
            share_links = ShareLink.objects.filter(created_by=request.user,is_active=False).order_by('-created_at')
        else:
            return Response({"message":"Invalid search term"},status=status.HTTP_400_BAD_REQUEST)
        
        total = share_links.count()
        paginator = ShareLinkCursorPagination()
        paginated_links = paginator.paginate_queryset(share_links, request, view=self)
        serializer = ShareLinkDetailSerializer(paginated_links,many=True)
        return paginator.get_paginated_response({"count":total,"results":serializer.data})

class ShareDetailList(APIView):
    permission_classes = [IsAuthenticated,IsLinkOwner]
    def get(self,request,id):
        share_link = get_object_or_404(ShareLink,id=id)
        self.check_object_permissions(request,share_link)
        
        files = share_link.files.all().order_by('-uploaded_at') 
        total = files.count()
        paginator = FileCursorPagination()
        paginated_files = paginator.paginate_queryset(files,request,view=self)
        
        serializer = FileListSerializer(paginated_files, many=True, context={'request': request})
        return paginator.get_paginated_response({"count":total,"results":serializer.data})
