from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User


class AboutPagesUrlsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')

    def setUp(self):
        self.user = AboutPagesUrlsTest.user
        self.guest_client = Client()

    def test_urls_exists_at_desired_addresses_for_unauthorized_user(self):
        """
        Проверка доступности страниц author, tech для
        НЕавторизованного пользователя
        """
        pages = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }
        for url, status in pages.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)
