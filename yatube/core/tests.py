from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        """Статус ответа 404 и используется шаблон 404.html"""
        response = self.client.get('/nonexist-page/')
        # Проверьте, что статус ответа сервера - 404
        # Проверьте, что используется шаблон core/404.html
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
