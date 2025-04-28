
from django.urls import path
from .views import (
    HomepageView,
    FavoriteProduct,
    ProductCommentListView,
    CommentCreateView,
    ProductListView,
    ProductFilterView,
    ProductDetailView,
    ProductAutocompleteView,
    NewsListView,
    NewsDetailView,
    NewsCreateView, ProductCreateView,
    ProductUpdateDeleteView, FilterDetailView, ProductSortView
)
urlpatterns = [
    path('all/', ProductListView.as_view()),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('homepage/',HomepageView.as_view()),
    path('favorites/',FavoriteProduct.as_view(), name='favorite-products'),
    path('comment/', CommentCreateView.as_view(), name='create_comment'),
    path('<int:product_id>/comments/', ProductCommentListView.as_view(), name='product_comments'),
    path('filter/', ProductFilterView.as_view(), name='product-filter'),
    path('autocomplete/', ProductAutocompleteView.as_view(), name='product-autocomplete'),
    path('news_list/', NewsListView.as_view(), name='news-list'),
    path('news_create/', NewsCreateView.as_view(), name='news-list'),
    path('news/<int:pk>/', NewsDetailView.as_view(), name='news-detail'),
    path('create/', ProductCreateView.as_view(), name='product-admin'),
    path('filter-detail/', FilterDetailView.as_view(), name='filter-detail'),
    path('<int:pk>/edit/', ProductUpdateDeleteView.as_view(), name='product-edit-delete'),

    path('filter_dop/', ProductSortView.as_view(), name='product-filter-sort' ),
]


