from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import cache_page
from .models import Post, Group, Comment, Follow
from .forms import PostForm, CommentForm
from .paginator import make_paginator
User = get_user_model()


@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    page_obj = make_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """View-функция для отображения всех записей группы"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj_group = make_paginator(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj_group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """View-функция для отображения всех записей пользователя"""
    author = get_object_or_404(User, username=username)
    user_posts = author.posts.all()
    count_posts = user_posts.count()
    page_obj = make_paginator(request, user_posts)
    # подписки
    if Follow.objects.filter(user=request.user, author=author).exists():
        following = True
    else:
        following = False
    if author == request.user:
        its_not_me = False
    else:
        its_not_me = True
    context = {
        'author': author,
        'page_obj': page_obj,
        'count_posts': count_posts,
        'following': following,
        'its_not_me': its_not_me
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """View-функция для отображения одной записи"""
    post = get_object_or_404(Post, pk=post_id)
    count_posts = post.author.posts.count()
    comments = Comment.objects.filter(post=post)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'count_posts': count_posts,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """View-функция для создания записи"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if request.method == 'POST':
        if form.is_valid():
            form = form.save(commit=False)
            form.author = request.user
            form.save()
            return redirect('posts:profile', username=form.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """View-функция для редактирования записи"""
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if post.author == request.user:
        if request.method == 'POST':
            if form.is_valid():
                form.save()
                return redirect('posts:post_detail', post_id=post_id)
        context = {
            'is_edit': True,
            'form': form,
            'post': post,
        }
        return render(request, 'posts/create_post.html', context)
    else:
        return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    user = request.user
    authors = user.follower.values_list('id', flat=True)
    post_list = Post.objects.filter(author_id__in=authors)
    page_obj = make_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на автора username"""
    author = get_object_or_404(User, username=username)
    user_fol = Follow.objects.filter(user=request.user, author=author)
    # на себя подписываться нельзя
    if request.user != author and not user_fol.exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора username"""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', author)
