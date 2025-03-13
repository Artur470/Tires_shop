
from django.urls import path
from .views import CategoriesListView,HomepageView,FavoriteProduct, ProductCommentListView, CommentCreateView, ProductListView
urlpatterns = [


    path('categories/',  CategoriesListView.as_view()),
    path('all/', ProductListView.as_view()),
    path('homepage/',HomepageView.as_view()),
    path('favorites/',FavoriteProduct.as_view(), name='favorite-products'),
    path('comment/', CommentCreateView.as_view(), name='create_comment'),
    path('<int:product_id>/comments/', ProductCommentListView.as_view(), name='product_comments'),



]
