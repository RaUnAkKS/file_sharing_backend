from django.shortcuts import render
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated,AllowAny



class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message":"User registered successfully"},status=status.HTTP_201_CREATED)
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"message":"User logged in successfully"},status=status.HTTP_200_OK)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)