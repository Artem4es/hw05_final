from django.test import Client, TestCase
from django.urls import reverse


class AboutPagesViewsTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_pages_use_correct_templates(self):
        """Страницы author и tech используют корректные шаблоны"""
        pages = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for url, template in pages.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
