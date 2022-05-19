from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group
User = get_user_model()
NUMBER_OF_POSTS_PER_PAGE = 10
NUMBER_OF_POSTS_PER_SECOND_PAGE = 3
NUMBER_OF_BULK_POSTS = 13


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД для проверки доступности шаблонов
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            description='Тестовый текст',
            slug='test-group-slug',
        )
        test_post_list = [
            Post(
                text='Текст тестовой записи',
                author=cls.user,
                group=cls.group,
            )
            for i in range(NUMBER_OF_BULK_POSTS)
        ]
        cls.posts = Post.objects.bulk_create(test_post_list)

    def setUp(self):
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_first_page_paginator(self):
        """Количество записей при пагинации на 1 странице posts:index"""
        response = self.authorized_client.get(reverse('posts:index'))
        response_post = response.context['page_obj']
        self.assertEqual(len(response_post), NUMBER_OF_POSTS_PER_PAGE)

    def test_home_second_page_paginator(self):
        """Количество записей при пагинации на 2 странице posts:index"""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2'
        )
        response_post = response.context['page_obj']
        self.assertEqual(len(response_post), NUMBER_OF_POSTS_PER_SECOND_PAGE)

    def test_group_list_first_page_paginator(self):
        """Количество записей при пагинации на 1 странице posts:group_list"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug'})
        )
        response_post = response.context['page_obj']
        self.assertEqual(len(response_post), NUMBER_OF_POSTS_PER_PAGE)

    def test_group_list_second_page_paginator(self):
        """Количество записей при пагинации на 2 странице posts:group_list"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-group-slug'}
            ) + '?page=2'
        )
        response_post = response.context['page_obj']
        self.assertEqual(len(response_post), NUMBER_OF_POSTS_PER_SECOND_PAGE)

    def test_profile_first_page_paginator(self):
        """Количество записей при пагинации на 1 странице posts:profile"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'testuser'})
        )
        response_post = response.context['page_obj']
        self.assertEqual(len(response_post), NUMBER_OF_POSTS_PER_PAGE)

    def test_profile_second_page_paginator(self):
        """Количество записей при пагинации на 2 странице posts:profile"""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'testuser'}
            ) + '?page=2'
        )
        response_post = response.context['page_obj']
        self.assertEqual(len(response_post), NUMBER_OF_POSTS_PER_SECOND_PAGE)
