from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group
from django import forms
User = get_user_model()


class PostPagesTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст тестовой записи',
            group=cls.group
        )

    def setUp(self):
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "reverse(name): имя_html_шаблона"
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            (
                reverse('posts:group_list', kwargs={'slug': 'test-group-slug'})
            ): 'posts/group_list.html',
            (
                reverse('posts:profile', kwargs={'username': 'testuser'})
            ): 'posts/profile.html',
            (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id})
            ): 'posts/post_detail.html',
            (
                reverse('posts:post_edit', kwargs={'post_id': self.post.id})
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def get_response_post(self, namespase, kwargs=None):
        """Получает из контекста объект для страницы"""
        response = self.authorized_client.get(reverse(namespase, kwargs))
        return response.context['page_obj']

    def test_home_page_context(self):
        """Поля словаря контекстов главной страницы posts:index"""
        response = self.authorized_client.get(reverse('posts:index'))
        response_post = response.context['page_obj'][0]
        self.assertEqual(response_post.text, 'Текст тестовой записи')
        self.assertEqual(response_post.author.username, 'testuser')

    def test_group_list_context(self):
        """Поля словаря контекстов списка постов по группе posts:group_list"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug'})
        )
        response_group = response.context['group']
        response_post = response.context['page_obj'][0]
        self.assertEqual(response_group.title, 'Тестовый заголовок группы')
        self.assertEqual(response_post.text, 'Текст тестовой записи')
        self.assertEqual(response_post.author.username, 'testuser')

    def test_profile_context(self):
        """Поля словаря контекстов списка постов по пользователю
        posts:profile"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'testuser'})
        )
        response_username = response.context['username']
        response_count_posts = response.context['count_posts']
        response_post = response.context['page_obj'][0]
        self.assertEqual(response_username.username, 'testuser')
        self.assertEqual(response_count_posts, 1)
        self.assertEqual(response_post.text, 'Текст тестовой записи')
        self.assertEqual(response_post.author.username, 'testuser')

    def test_post_detail_context(self):
        """Поля словаря контекстов поста по id posts:post_detail"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        response_count_posts = response.context['count_posts']
        response_post = response.context['post']
        self.assertEqual(response_count_posts, 1)
        self.assertEqual(response_post.text, 'Текст тестовой записи')
        self.assertEqual(response_post.author.username, 'testuser')

    def test_post_create_show_correct_context_type(self):
        """Типы данных в форме шаблона post_create соответствуют контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        # Проверяем, что типы полей формы в словаре context
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context_type(self):
        """Типы данных в форме шаблона post_edit соответствуют контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        # Проверяем, что типы полей формы в словаре context
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Форма в шаблоне post_edit сформирована с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1})
        )
        response_post = response.context['post']
        self.assertEqual(response.context['is_edit'], True)
        self.assertEqual(response_post.text, 'Текст тестовой записи')
        self.assertEqual(response_post.author.username, 'testuser')


class CreatePostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            description='Тестовый текст',
            slug='test-group-slug',
        )
        cls.other_group = Group.objects.create(
            title='Тестовый заголовок другой группы',
            description='Тестовый текст',
            slug='test-other-group-slug',
        )

    def setUp(self):
        # Создание авторизованного клиента
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # данные для передачи в форму
        form_data = {
            'text': 'Тестовый текст для главной страницы',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

    def test_post_in_home_page(self):
        """Пост при создании попал на главную страницу"""
        response_home_page = self.authorized_client.get(reverse('posts:index'))
        response_home_page_post = response_home_page.context['page_obj'][0]
        self.assertEqual(
            response_home_page_post.text,
            'Тестовый текст для главной страницы'
        )

    def test_post_in_group_list(self):
        """Пост при создании попал на страницу группы"""
        response_group_list = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-group-slug'})
        )
        response_group_list_post = response_group_list.context['page_obj'][0]

        self.assertEqual(
            response_group_list_post.text,
            'Тестовый текст для главной страницы'
        )

    def test_post_in_other_group_list(self):
        """Пост не попал в группу, для которой не был предназначен"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-other-group-slug'}
            )
        )
        response_post = response.context['page_obj']
        self.assertEqual(len(response_post), 0)

    def test_post_in_profile(self):
        """Пост при создании попал в профайл пользователя"""
        response_group_list = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'testuser'})
        )
        response_group_list_post = response_group_list.context['page_obj'][0]

        self.assertEqual(
            response_group_list_post.text,
            'Тестовый текст для главной страницы'
        )
