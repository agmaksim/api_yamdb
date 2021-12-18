from django.urls import path, include
from rest_framework.routers import DefaultRouter
# from rest_framework.authtoken import views

from .views import (
    CategoryViewSet,
    GenreViewSet,
    ReviewViewSet,
    TitleViewSet,
    CommentViewSet,
    UserViewSet,
    auth_signup,
    auth_get_token,
)


router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='categories')
router.register(r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
                CommentViewSet, basename='comments')
router.register(r'titles/(?P<title_id>\d+)/reviews',
                ReviewViewSet, basename='reviews')
router.register('titles', TitleViewSet, basename='titles')
router.register('genres', GenreViewSet, basename='genres')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('v1/', include(router.urls)),
    path('auth/signup/', auth_signup, name='signup'),
    path('auth/token/', auth_get_token, name='token'),
]
