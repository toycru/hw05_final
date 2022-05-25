from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from .models import Post, Group, Comment
from .forms import PostForm, CommentForm
from .paginator import make_paginator
User = get_user_model()


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
    user = get_object_or_404(User, username=username)
    user_posts = user.posts.all()
    count_posts = user_posts.count()
    page_obj = make_paginator(request, user_posts)
    context = {
        'username': user,
        'page_obj': page_obj,
        'count_posts': count_posts,
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
