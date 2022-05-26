import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from posts.models import Post, Group, Follow
from django import forms

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст тестовой записи',
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

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

    def test_home_page_context(self):
        """Поля словаря контекстов главной страницы posts:index"""
        response = self.authorized_client.get(reverse('posts:index'))
        response_post = response.context['page_obj'][0]
        self.assertEqual(response_post.text, 'Текст тестовой записи')
        self.assertEqual(response_post.author.username, 'testuser')
        self.assertEqual(response_post.image, self.post.image)

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
        self.assertEqual(response_post.image, self.post.image)

    def test_profile_context(self):
        """Поля словаря контекстов списка постов по пользователю
        posts:profile"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'testuser'})
        )
        response_username = response.context['author']
        response_count_posts = response.context['count_posts']
        response_post = response.context['page_obj'][0]
        self.assertEqual(response_username.username, 'testuser')
        self.assertEqual(response_count_posts, 1)
        self.assertEqual(response_post.text, 'Текст тестовой записи')
        self.assertEqual(response_post.author.username, 'testuser')
        self.assertEqual(response_post.image, self.post.image)

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
        self.assertEqual(response_post.image, self.post.image)

    def test_post_create_show_correct_context_type(self):
        """Типы данных в форме шаблона post_create соответствуют контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
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
            'image': forms.fields.ImageField
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

    def test_post_cashing_index_page(self):
        """Главная страница кешируется"""
        post = self.post
        response = self.authorized_client.get(reverse('posts:index'))
        count_before_delete_post = len(response.context.get('page_obj'))
        post.delete()
        count_after_delete_post = len(response.context.get('page_obj'))
        self.assertEqual(count_before_delete_post, count_after_delete_post)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        count_after_clear_cash = len(response.context.get('page_obj'))
        self.assertEqual(count_before_delete_post, count_after_clear_cash + 1)


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
        cache.clear()

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


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.another_user = User.objects.create_user(username='anotheruser')
        cls.author = User.objects.create_user(username='testauthor')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            description='Тестовый текст',
            slug='test-group-slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст тестовой записи автора',
            group=cls.group,
        )
        cls.post_of_user = Post.objects.create(
            author=cls.user,
            text='Текст тестовой записи пользователя',
            group=cls.group,
        )

    def setUp(self):
        # Создание авторизованного клиента
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_auth_user_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок, редиректы верные"""
        count_follow_before_follow = Follow.objects.count()
        response = self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                args={'testauthor'}
            )
        )
        count_follow_after_follow = Follow.objects.count()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'testauthor'}
        ))
        self.assertEqual(
            count_follow_before_follow + 1,
            count_follow_after_follow
        )
        response = self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                args={'testauthor'}
            )
        )
        count_follow_after_unfollow = Follow.objects.count()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'testauthor'}
        ))
        self.assertEqual(
            count_follow_after_follow - 1,
            count_follow_after_unfollow
        )

    def test_subscribe_to_yourself(self):
        """Нельзя подписаться на себя"""
        count_follow_before_follow = Follow.objects.count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                args={'testuser'}
            )
        )
        count_follow_after_follow = Follow.objects.count()
        self.assertEqual(count_follow_before_follow, count_follow_after_follow)

    def test_post_in_follow(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count_before_follow = len(response.context.get('page_obj'))
        Follow.objects.get_or_create(user=self.user, author=self.author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count_after_follow = len(response.context.get('page_obj'))
        self.assertEqual(count_before_follow + 1, count_after_follow)
        cache.clear()
        self.authorized_client.force_login(self.another_user)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count_posts_in_unfollow_user = len(response.context.get('page_obj'))
        self.assertEqual(count_posts_in_unfollow_user, 0)
        cache.clear()
