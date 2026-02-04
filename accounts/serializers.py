from .models import *
from rest_framework import serializers

class UserRegistrationSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self,data):
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        username = data.get('username')

        if password!=confirm_password:
            raise serializers.ValidationError("Password and confirm password donot match")

        if username:
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError("Username already taken")

        if email:
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError("Email already registered")
        
        return data

    def create(self,validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self,data):
        email = data.get('email')
        password = data.get('password')

        if not email:
            raise serializers.ValidationError("Email is required")
        if not password:
            raise serializers.ValidationError("Password is required")

        user = User.objects.filter(email=email,password=password).exists()
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active', 'date_joined']
    

