from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .constants import POST_QTY, RUNOUT
from .forms import CommentForm, PostForm
from .models import Group, Post, Follow, User
from .paginator import paginate_page


@cache_page(RUNOUT, key_prefix='index_page')
def index(request):
    title = 'Последние обновления на сайте'

    post_list = Post.objects.select_related(
        'author',
        'group',
    )

    page_obj = paginate_page(request, post_list, POST_QTY)
    context = {
        'page_obj': page_obj,
        'title': title,
        'index': True,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    title = 'Записи сообщества'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author', 'group')
    page_obj = paginate_page(request, post_list, POST_QTY)
    context = {
        'page_obj': page_obj,
        'group': group,
        'title': title,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group', 'author')
    page_obj = paginate_page(request, post_list, POST_QTY)
    fav_authors = (
        Follow.objects.filter(user_id=request.user.id)
        .all()
        .values_list('author_id', flat=True)
    )
    following = True if author.id in fav_authors else False
    context = {
        'author': author,
        'post_list': post_list,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            user_name = request.user.username
            return redirect(reverse('posts:profile', args=[user_name]))
        return render(request, 'posts/create_post.html', {'form': form})

    form = PostForm()
    context = {'form': form}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user.id == post.author.id:
        if request.method == 'POST':
            form = PostForm(
                request.POST or None,
                instance=post,
                files=request.FILES or None,
            )
            if form.is_valid():
                form.save()
                return redirect(reverse('posts:post_detail', args=[post_id]))

        post = get_object_or_404(Post, id=post_id)
        form = PostForm(instance=post)
        is_edit = True
        context = {'form': form, 'is_edit': is_edit}
        return render(request, 'posts/update_post.html', context)
    return redirect(reverse('posts:post_detail', args=[post_id]))


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(id=post_id)

    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    title = 'Избранные авторы'
    follower = request.user
    post_list = Post.objects.filter(author__following__user=follower)
    page_obj = paginate_page(request, post_list, POST_QTY)
    context = {
        'page_obj': page_obj,
        'title': title,
        'follow': True,
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    follower = request.user
    followed = User.objects.get(username=username)
    if follower.id != followed.id:
        Follow.objects.get_or_create(user=follower, author=followed)
    return redirect(reverse('posts:profile', kwargs={'username': username}))


@login_required
def profile_unfollow(request, username):
    follower = request.user
    followed = User.objects.get(username=username)
    follow_qs = Follow.objects.filter(user=follower, author=followed)
    print(type(follow_qs))
    follow_qs.delete()
    return redirect(reverse('posts:profile', kwargs={'username': username}))
