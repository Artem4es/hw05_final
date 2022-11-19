from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        Post.objects.create(
            text='Постик',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = PostFormCreateTests.user
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        form_data = {
            'text': 'Тестовый пост',
            'group': 1,
        }
        post_count = Post.objects.count()

        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={'username': 'author'})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)

    def test_create_post_with_image(self):
        """Переданное в форму изображение сохранятся в БД."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'Картинка',
            'group': 1,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        post_image = response.context.get('page_obj')[0].image
        expected_image = Post.objects.get(id=2).image
        self.assertEqual(post_image, expected_image)

    def test_edit_post(self):
        """
        Валидная форма редактирует существующую запись в Post,
        не создавая новую запись
        """
        post_count = Post.objects.count()
        old_text = Post.objects.get(id=1).text
        old_author = Post.objects.get(id=1).author
        old_group = Post.objects.get(id=1).group
        form_data = {
            'text': 'Обновлённый текст',
            'group': 1,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True,
        )
        new_text = Post.objects.get(id=1).text
        new_author = Post.objects.get(id=1).author
        new_group = Post.objects.get(id=1).group
        self.assertNotEqual(old_text, new_text)
        self.assertEqual(old_author, new_author)
        self.assertEqual(old_group, new_group)
        self.assertEqual(post_count, Post.objects.count())

    def test_create_post_unauthorized(self):
        """
        Неавторизованный пользователь не может создать новый пост
        и его редиректит на страницу входа
        """
        post_count = Post.objects.count()
        form_data = {
            'text': 'Пост неавторизованного юзера',
            'group': 1,
        }
        response = self.unauthorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            f'{reverse("users:login")}?next={reverse("posts:post_create")}',
        ),

        self.assertEqual(Post.objects.count(), post_count)

    def test_edit_post_unauthorized(self):
        """
        Неавторизованный пользователь не может редактировать пост в БД
        и его редиректит на страницу входа
        """
        post_count = Post.objects.count()
        old_text = Post.objects.get(id=1).text
        old_author = Post.objects.get(id=1).author
        old_group = Post.objects.get(id=1).group
        form_data = {
            'text': 'Пост неавторизованного юзера',
            'group': 1,
        }
        response = self.unauthorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            (
                f'{reverse("users:login")}?next='
                f'{reverse("posts:post_edit", kwargs = {"post_id":1})}'
            ),
        )

        self.assertEqual(Post.objects.count(), post_count)
        new_text = Post.objects.get(id=1).text
        new_author = Post.objects.get(id=1).author
        new_group = Post.objects.get(id=1).group
        self.assertEqual(old_text, new_text)
        self.assertEqual(old_author, new_author)
        self.assertEqual(old_group, new_group)

    def test_comment_create_authorized_user(self):
        """
        Комментарий создаётся авторизованным пользователем и его
        редиректит на страницу post_detail
        """
        form_data = {
            'text': 'Тестовый коммент',
        }
        comment_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 1}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_comment_create_unauthorized_user(self):
        """
        Комментарий НЕ создаётся НЕавторизованным пользователем.
        """
        form_data = {
            'text': 'Неавторизованный коммент',
        }
        comment_count_initial = Comment.objects.count()
        response = self.unauthorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": 1}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comment_count_initial)
