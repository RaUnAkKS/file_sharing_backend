from accounts.views import *
from files.views import *
from sharing.views import *
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/',RegisterView.as_view(),name='register'),
    path('login/',LoginView.as_view(),name='login'),
    path('profile/',ProfileView.as_view(),name='profile'),
    path('files/upload/',FileUploadView.as_view(),name='file-upload'),
    path('files/list/',UserFileListView.as_view(),name='file-list'),
    path('files/delete/<uuid:file_id>/',FileDeleteView.as_view(),name='file-delete'),
    path('files/delete-all/',FileDeleteAllView.as_view(),name='file-delete-all'),
    path('share/create/',CreateShareLinkView.as_view(),name='create-share-link'),
    path('share/<uuid:id>/',ShareLinkDetailView.as_view(),name='share-link-detail'),
    path('share/access/<uuid:id>/',ShareLinkAccessView.as_view(),name='share-link-access'),
    path('share/download/<uuid:share_link_id>/',ShareDownload.as_view(),name='share-download'),
    path('share/status/<uuid:id>/',ShareLinkStatusView.as_view(),name='share-link-status'),
    path('share/delete/<uuid:share_link_id>/',ShareLinkDeleteView.as_view(),name='share-link-delete'),
    path('share/list/',ShareLinklist.as_view(),name='share-link-list'),
    path('share/<uuid:id>/files/',ShareDetailList.as_view(),name='share-link-files'),
]
