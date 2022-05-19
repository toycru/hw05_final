from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group
from django.urls import reverse
User = get_user_model()


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

    def setUp(self):
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Форма создает запись в БД и вполняет редирект."""
        # количество записей
        posts_count = Post.objects.count()
        # данные для передачи в форму
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
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
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Последний добавленный пост действительно последний созданный в БД,
        latest_post = Post.objects.latest('pub_date')
        self.assertEqual(latest_post.text, form_data['text'])

    def test_edit_post(self):
        """Форма редактирует запись в БД и вполняет редирект."""
        # Подготавливаем данные для передачи в форму
        form_data = {
            'text': 'Отредактированный тестовый текст',
            'group': self.other_group.id,
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
