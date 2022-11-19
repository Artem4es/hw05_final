import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug1',
            description='Тестовое описание 1',
        )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif', content=cls.small_gif, content_type='image/gif'
        )

        cls.post1 = Post.objects.create(
            text='Тестовый текст1',
            author=cls.user,
            group=cls.group1,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = PostTestCase.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': 'test-slug1'}
            ),
            'posts/index.html': reverse('posts:index'),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': 1}
            ),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': 'author'}
            ),
            'posts/update_post.html': reverse(
                'posts:post_edit', kwargs={'post_id': 1}
            ),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_404_page_uses_custom_template(self):
        """Страница 404 использует кастомный шаблон сore/404.html"""
        response = self.authorized_client.get('/unexisiting_page/')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_home_page_shows_correct_context(self):
        """Шаблон главной страницы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_list = response.context.get('page_obj').object_list
        post_list_expected = list(Post.objects.all())
        title = response.context.get('title')
        self.assertEqual(post_list, post_list_expected)
        self.assertEqual(title, 'Последние обновления на сайте')

    def test_home_page_contains_image_in_context(self):
        """Главная страница содержит искомое изображение в контексте"""
        response = self.authorized_client.get(reverse('posts:index'))
        context_image = response.context.get('page_obj')[0].image
        expected_image = Post.objects.get(id=self.post1.id).image
        self.assertEqual(context_image, expected_image)

    def test_group_page_shows_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug1'})
        )
        post_list = response.context.get('page_obj').object_list
        post_list_expected = list(Post.objects.filter(group=self.group1))
        self.assertEqual(post_list, post_list_expected)

    def test_group_page_contains_post_with_correct_image_in_context(self):
        """Страница group_list содержит искомое изображение в контексте."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug1'})
        )
        context_image = response.context.get('page_obj')[0].image
        expected_image = Post.objects.get(id=self.post1.id).image
        self.assertEqual(context_image, expected_image)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'author'})
        )
        post_list = response.context.get('page_obj').object_list
        post_list_expected = list(Post.objects.filter(author=self.user))
        self.assertEqual(post_list, post_list_expected)

    def test_profile_page_contains_correct_image(self):
        """Страница profile содержит искомое изображение в контексте."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'author'})
        )
        context_image = response.context.get('page_obj')[0].image
        expected_image = Post.objects.get(id=self.post1.id).image
        self.assertEqual(context_image, expected_image)

    def test_post_detail_page_shows_correct_context(self):
        """
        Шаблон post_detail сформирован с правильным контекстом:
        выдаёт один пост
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        post = response.context.get('post')
        post_expected = Post.objects.get(id=1)
        self.assertEqual(post, post_expected)

    def test_post_detail_contains_post_with_correct_image_in_context(self):
        """
        Страница post_detail содержит пост с искомым изображением в контексте
        """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        context_image = response.context.get('post').image
        image_expected = Post.objects.get(id=1).image
        self.assertEqual(context_image, image_expected)

    def test_post_edit_page_shows_correct_context(self):
        """
        Шаблон post_edit имеет форму с правильным контекстом
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest():
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_shows_correct_context(self):
        """
        Шаблон create_post имеет форму с правильным контекстом
        """
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest():
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')

        cls.group1 = Group.objects.create(
            title='Тестовая группа1',
            slug='test-slug1',
            description='Тестовое описание1',
        )

        Post.objects.bulk_create(
            [
                (Post(text='Балк пост1', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост2', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост3', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост4', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост5', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост6', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост7', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост8', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост9', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост10', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост11', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост12', author=cls.user, group=cls.group1)),
                (Post(text='Балк пост13', author=cls.user, group=cls.group1)),
            ]
        )

    def setUp(self):
        self.user = PaginatorViewsTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_index_first_page_contains_ten_records(self):
        """Проверка, что паджинатор выводит 10 записей на страницу"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_two_records(self):
        """Проверка, что на второй странице index 3 поста"""
        response = self.authorized_client.get(
            (reverse('posts:index') + '?page=2')
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_first_page_contains_ten_records(self):
        """Проверка, что паджинатор выводит 10 записей на страницу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug1'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_list_second_page_contains_two_records(self):
        """Проверка, что на второй странице group_list 3 поста"""
        response = self.authorized_client.get(
            (reverse('posts:group_list', kwargs={'slug': 'test-slug1'}))
            + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_first_page_contains_ten_records(self):
        """Проверка, что паджинатор выводит 10 записей на страницу"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'author'})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page_contains_two_records(self):
        """Проверка, что на второй странице profile 3 поста"""
        response = self.authorized_client.get(
            (
                reverse('posts:profile', kwargs={'username': 'author'})
                + '?page=2'
            )
        )
        self.assertEqual(len(response.context['page_obj']), 3)


class PostRelatedGroupTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug1',
            description='Тестовое описание 1',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        cls.post1 = Post.objects.create(
            text='Тестовый текст1',
            author=cls.user,
            group=cls.group1,
        )

    def setUp(self):
        self.user = PostRelatedGroupTest.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_created_post_appears_on_related_pages(self):
        """
        При создании поста с укзанием группы он появляется на связанных
        с ним страницах
        """
        url_list = {
            'posts:index': None,
            'posts:group_list': {'slug': 'test-slug1'},
            'posts:profile': {'username': 'author'},
        }

        for key, value in url_list.items():
            with self.subTest():
                response = self.authorized_client.get(
                    reverse(key, kwargs=value)
                )
                expected_post = Post.objects.get(id=1)
                self.assertContains(response, expected_post)

    def test_no_created_post_on_non_related_pages(self):
        """
        При создании поста с укзанием группы он не появляется на
        не связанных с ним страницах
        """
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug2'})
        )
        wanted_post = Post.objects.get(id=1)

        self.assertNotContains(response, wanted_post)

    def test_index_page_cache(self):
        """Тестируем кэширование главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        a = response.content
        Post.objects.get(id=self.post1.id).delete()
        b = self.authorized_client.get(reverse('posts:index')).content
        self.assertEqual(a, b)
        cache.clear()
        c = self.authorized_client.get(reverse('posts:index')).content
        self.assertNotEqual(b, c)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='user')
        cls.user2 = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            text='Подпишись на меня!', author=cls.user2
        )

    def setUp(self):
        self.user1 = FollowTest.user1
        self.user2 = FollowTest.user2
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        cache.clear()

    def test_follow(self):
        """Проверка подписки и отписки от автора"""
        follower = self.user1
        fav_author = self.user2
        self.authorized_client1.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': fav_author.username},
            )
        )
        follower_subscribed_to = Follow.objects.get(user_id=follower.id).author
        self.assertEqual(follower_subscribed_to, fav_author)
        self.authorized_client1.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': fav_author.username},
            )
        )
        follower_subscribed_to = Follow.objects.all()
        self.assertEqual(len(follower_subscribed_to), 0)

    def test_new_author_post_on_follow_index_page(self):
        """
        Новая запись автора видна только подписанному пользователю
        на странице follow_index
        """
        subscription = Follow.objects.create(
            user=self.user1, author=self.user2
        )
        response = self.authorized_client1.get(reverse('posts:follow_index'))
        new_post = response.context.get('page_obj').object_list[0]
        expected_post = self.post
        self.assertEqual(new_post, expected_post)
        subscription.delete()
        response = self.authorized_client1.get(reverse('posts:follow_index'))
        post_list = response.context.get('page_obj').object_list
        self.assertEqual(len(post_list), 0)
