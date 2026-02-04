from .models import ShareLink
from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from files.models import File

class ShareLinkCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,required=False)
    expires_at = serializers.DateTimeField(required=False)
    files = serializers.PrimaryKeyRelatedField(queryset=File.objects.all(), many=True, required=False)
    share_all = serializers.BooleanField(required=False, write_only=True)

    class Meta:
        model = ShareLink
        fields = ['expires_at','max_downloads','password','files', 'share_all']

    def validate_expires_at(self,data):
        if data <= timezone.now():
            raise serializers.ValidationError("Expiry date cannot be in the past or present")
        return data
    
    def validate_max_downloads(self,data):
        if data<=0:
            raise serializers.ValidationError("Max downloads must be greater than 0")
        return data

    def validate_files(self, value):
        user = self.context.get('user')
        for file in value:
            if file.owner != user:
                raise serializers.ValidationError("You can only share your own files")
            if not file.is_active:
                raise serializers.ValidationError("You can only share active files")
        return value

    def validate(self, data):
        if not data.get('files') and not data.get('share_all'):
            raise serializers.ValidationError("You must select files or choose 'share_all'.")
        return data

    def create(self,validated_data):
        user = self.context.get('user')
        password = validated_data.pop('password',None)
        files = validated_data.pop('files', [])
        share_all = validated_data.pop('share_all',False)
        
        share_link = ShareLink.objects.create(created_by=user,**validated_data)
        if share_all:
            files = File.objects.filter(owner=user,is_active=True)
        share_link.files.set(files)
        
        if password:
            share_link.password = make_password(password)
            share_link.save(update_fields=['password'])
        return share_link

class ShareLinkDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareLink
        fields = ['id','expires_at','download_count','is_active','max_downloads']
        read_only_fields = fields

class ShareLinkFileDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id','file','content_type','uploaded_at','is_active']
        read_only_fields = ['id','file','content_type','uploaded_at','is_active']

class ShareLinkAccessSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def validate(self,data):
        password = data.get('password')
        share_link = self.context.get('share_link')
        if share_link.is_active==False:
            raise serializers.ValidationError("Link inactive")
        if share_link.expires_at < timezone.now():
            raise serializers.ValidationError("Link expired")
        if share_link.download_count >= share_link.max_downloads:
            raise serializers.ValidationError("Download limit reached")
        if share_link.password:
            if not password or not check_password(password,share_link.password):
                raise serializers.ValidationError("Invalid password")
            
        # share_link.download_count += 1
        # share_link.save(update_fields=['download_count'])
        return data