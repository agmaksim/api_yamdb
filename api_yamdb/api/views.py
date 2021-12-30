from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db.models import Avg
from django.db.utils import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly
)
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import TitleFilter

from .serializers import (
    CategorySerializer,
    CommentSerializer,
    GenreSerializer,
    ReviewSerializer,
    TitleReadSerializer,
    TitleWriteSerializer,
    UserSerializer,
    SignUpSerializer,
    TokenSerializer,
)
from reviews.models import Category, Genre, Review, Title
from .permissions import (
    OnlyForAdmin,
    IsAuthorOrReadOnly,
    ReadOnly,
    NoRoleChange
)
from .pagination import YamdbPagination
from api_yamdb.settings import SITE_EMAIL

User = get_user_model()


class CreateDestroyListViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    pass


def sending_mail(email, confrimation_code):
    try:
        send_mail(
            'Аутентификация',
            confrimation_code,
            SITE_EMAIL,
            [email],
            fail_silently=False,
        )

    except Exception:
        return 'Ошибка при отправке сообщения'


@api_view(['POST', ])
@permission_classes([AllowAny])
def auth_signup(request):
    serializer = SignUpSerializer(data=request.data)
    code_generator = PasswordResetTokenGenerator()

    serializer.is_valid(raise_exception=True)
    username = serializer.validated_data.get('username')
    email = serializer.validated_data.get('email')
    try:
        user, created = User.objects.get_or_create(
            email=email,
            username=username
        )

    except IntegrityError:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    if not (user or created):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    confirmation_code = code_generator.make_token(
        user=user
    )
    error = sending_mail(email, confirmation_code)

    if error:
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST', ])
@permission_classes([AllowAny])
def auth_get_token(request):
    serializer = TokenSerializer(data=request.data)
    code_generator = PasswordResetTokenGenerator()
    username = serializer.initial_data.get('username')
    code = serializer.initial_data.get('confirmation_code')

    serializer.is_valid(raise_exception=True)

    user = get_object_or_404(
        User,
        username=username
    )

    if code_generator.check_token(user=user, token=code):
        refresh = RefreshToken.for_user(user)

        token = {
            'token': str(refresh.access_token),
        }
        return Response(token, status=status.HTTP_200_OK)

    return Response('Неверный код', status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (OnlyForAdmin,)
    queryset = User.objects.all().order_by('date_joined')
    serializer_class = UserSerializer
    lookup_field = 'username'
    pagination_class = YamdbPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('username',)

    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated, NoRoleChange)
    )
    def users_profile(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        serializer.save(role=user.role, partial=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    pagination_class = YamdbPagination
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('=name',)

    def perform_create(self, serializer):
        title = get_object_or_404(Title, pk=self.kwargs.get('title_id'))
        serializer.save(author=self.request.user, title=title)

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get('title_id'))
        queryset = title.reviews.all()
        return queryset


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        Avg('reviews__score')).order_by('year')
    pagination_class = YamdbPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = TitleFilter
    permission_classes = (ReadOnly,)

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return TitleReadSerializer
        return TitleWriteSerializer


class GenreViewSet(CreateDestroyListViewSet):
    queryset = Genre.objects.get_queryset().order_by('id')
    lookup_field = 'slug'
    serializer_class = GenreSerializer
    pagination_class = YamdbPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('=name',)
    permission_classes = (ReadOnly,)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = YamdbPagination
    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly)

    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id, title__id=title_id)
        serializer.save(author=self.request.user, review=review)

    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        review_id = self.kwargs.get('review_id')
        review = get_object_or_404(Review, pk=review_id, title__id=title_id)
        queryset = review.comments.all()
        return queryset


class CategoryViewSet(CreateDestroyListViewSet):
    queryset = Category.objects.get_queryset().order_by('id')
    lookup_field = 'slug'
    serializer_class = CategorySerializer
    pagination_class = YamdbPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('=name',)
    permission_classes = (ReadOnly,)
