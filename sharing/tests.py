from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from files.models import File
from .models import ShareLink
from django.urls import reverse

User = get_user_model()

class ShareLinkTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', username='testuser', password='password123')
        self.client.force_authenticate(user=self.user)
        self.file_content = b"file_content"
        self.uploaded_file = SimpleUploadedFile("test_file.txt", self.file_content, content_type="text/plain")
        self.file = File.objects.create(
            owner=self.user,
            file=self.uploaded_file,
            original_filename="test_file.txt",
            file_size=len(self.file_content),
            content_type="document"
        )

    def test_create_share_link(self):
        url = reverse('create-share-link')
        # Payload now expects 'files' list
        data = {'files': [str(self.file.id)], 'max_downloads': 5}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ShareLink.objects.count(), 1)
        # Check ManyToMany relationship
        link = ShareLink.objects.get()
        self.assertEqual(link.max_downloads, 5)
        self.assertIn(self.file, link.files.all())

    def test_create_share_link_with_password(self):
        url = reverse('create-share-link')
        data = {'files': [str(self.file.id)], 'max_downloads': 5, 'password': 'mypassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        link = ShareLink.objects.get()
        self.assertTrue(link.password) 
        self.assertNotEqual(link.password, 'mypassword')

    def test_access_share_link(self):
        link = ShareLink.objects.create(created_by=self.user, max_downloads=5)
        link.files.add(self.file)
        
        url = reverse('share-link-access', args=[link.id])
        data = {'password': ''} # No password needed
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Security: Check if session was updated
        self.assertIn('unlocked_links', self.client.session)
        self.assertIn(str(link.id), self.client.session['unlocked_links'])

    def test_access_password_protected_link(self):
        link = ShareLink.objects.create(created_by=self.user, max_downloads=5)
        link.files.add(self.file)
        from django.contrib.auth.hashers import make_password
        link.password = make_password('secret')
        link.save()

        url = reverse('share-link-access', args=[link.id])
        
        # 1. Wrong password
        response = self.client.post(url, {'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('unlocked_links', self.client.session)

        # 2. Correct password
        response = self.client.post(url, {'password': 'secret'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(str(link.id), self.client.session['unlocked_links'])

    def test_share_download(self):
        link = ShareLink.objects.create(created_by=self.user, max_downloads=5)
        link.files.add(self.file)
        
        # Simulate unlocked session so download checks pass
        # (For non-password links, we permit download if logic allows, 
        # but our view logic might default to allowing it if no password is set. 
        # Let's verify view logic: "if share_link.password: check session". 
        # If no password, no session check needed.)
        
        url = reverse('share-download', args=[link.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/zip')
        
        # Verify download count incremented
        link.refresh_from_db()
        self.assertEqual(link.download_count, 1)

    def test_secure_download_bypass_attempt(self):
        """Test trying to download a password-protected file without unlocking it first"""
        link = ShareLink.objects.create(created_by=self.user, max_downloads=5)
        link.files.add(self.file)
        from django.contrib.auth.hashers import make_password
        link.password = make_password('secret')
        link.save()

        url = reverse('share-download', args=[link.id])
        # Try finding download URL without accessing/entering password
        response = self.client.get(url)
        # Should be Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
