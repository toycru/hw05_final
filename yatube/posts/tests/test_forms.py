import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_forms_user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            description='Тестовый текст',
            slug='test-group-slug',
        )
        cls.other_group = Group.objects.create(
            title='Тестовый заголовок другой группы',
            description='Тестовый другой текст',
            slug='test-other-group-slug',
        )
        cls.one_post = Post.objects.create(
            author=cls.user,
            text='Текст тестовой записи',
            group=cls.group
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

    def test_create_post(self):
        """Форма создает запись в БД и вполняет редирект."""
        # количество записей
        posts_count = Post.objects.count()
        # Подготавливаем данные для передачи в форму
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # данные для передачи в форму
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'test_forms_user'}
        ))
        # Проверяем, что создалась запись с рисунком
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                image='posts/small.gif',
                group=self.group.id,
            ).exists()
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Последний добавленный пост действительно последний созданный в БД,
        latest_post = Post.objects.latest('pub_date')
        self.assertEqual(latest_post.text, form_data['text'])

    def test_edit_post(self):
        """Форма редактирует запись в БД и вполняет редирект."""
        # Подготавливаем данные для передачи в форму
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small1.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Отредактированный тестовый текст',
            'group': self.other_group.id,
            'image': uploaded,
        }
        last_post = Post.objects.last()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': last_post.id}),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.filter(id=last_post.id).get()
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': last_post.id}
        ))
        # Проверяем, что создалась запись с рисунком
        self.assertTrue(
            Post.objects.filter(
                text='Отредактированный тестовый текст',
                image='posts/small1.gif',
                group=self.other_group.id,
            ).exists()
        )

    def test_add_comment(self):
        """После успешной отправки комментарий появляется на странице поста."""
        # количество комментариев изначально
        comment_count = Comment.objects.count()
        # данные для передачи в форму
        form_data = {
            'text': 'Тестовый комментарий',
            'post': self.one_post,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.one_post.id}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.one_post.id}
        ))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Комментарий добавлен в БД
        self.assertTrue(
            Comment.objects.filter(
                text='Тестовый комментарий',
            ).exists()
        )
        # Проверяем, увеличилось ли число комментариев
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        response_context = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        ).context['comments'][0]
        self.assertEqual(response_context.text, 'Тестовый комментарий')
