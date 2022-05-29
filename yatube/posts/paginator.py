from django.core.paginator import Paginator

NUMBER_OF_POSTS_PER_PAGE = 10


def make_paginator(request, posts):
    """Функция делит список записей для отображения на странице"""
    paginator = Paginator(posts, NUMBER_OF_POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
