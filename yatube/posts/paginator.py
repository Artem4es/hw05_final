from django.core.paginator import Paginator


def paginate_page(request, post_list, post_qty):
    """Creates definite page number with 10 posts by default"""
    page_number = request.GET.get('page')
    return Paginator(post_list, post_qty).get_page(page_number)
