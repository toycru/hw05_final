from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            description='Тестовый текст',
            slug='test-group-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            pub_date='дата',
            group=cls.group
        )

    def setUp(self):
        # Создаём экземпляр клиента. Он неавторизован.
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        # авторизация тестового пользователя
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_homepage_availability(self):
        """Доступность главной страницы"""
        response = self.guest_client.get('/')
        # Утверждаем, что для прохождения теста код должен быть равен 200
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_unavailability(self):
        """Переход на стр.404 при переход на несуществующую страницу"""
        response = self.guest_client.get('/unexisting_page')
        # Утверждаем, что для прохождения теста код должен быть равен 404
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-group-slug/': 'posts/group_list.html',
            '/profile/testuser/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_add_comment_unavailability(self):
        """Недоступность добавления комментариев неавторизованному"""
        response = self.guest_client.get(
            f'/posts/{self.post.id}/comment/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
