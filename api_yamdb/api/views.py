from random import randint
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters, status, mixins, serializers
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
from reviews.models import Category, Comment, Genre, Review, Title
from .permissions import OnlyForAdmin, IsAuthorOrReadOnly, ReadOnly
from .pagination import YamdbPagination

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
            'Authentification',
            confrimation_code,
            'api_yambd@example.com',
            [email],
            fail_silently=False,
        )

        return None

    except Exception:
        return 'Ошибка при отправке сообщения'


@api_view(['POST', ])
@permission_classes([AllowAny])
def auth_signup(request):
    serializer = SignUpSerializer(data=request.data)
    code_generator = PasswordResetTokenGenerator()

    try:
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Создается новый user и тут же используется для алгоритмов
        # генерации токена
        username = serializer.validated_data.get('username')
        user = get_object_or_404(
            User, username=username
        )
        confirmation_code = code_generator.make_token(
            user=user
        )
        email = serializer.validated_data.get('email')
        error = sending_mail(email, confirmation_code)
        if error:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    except serializers.ValidationError:
        '''
        Если ошибка в имени user'a, то она может быть связана
        c существованием user'a с таким именем, поэтому необходимо
        проверить код ошибки.
        Иначе валидация провалена по другим причинам, которые вообщем
        нам неинтересны
        '''
        if serializer.errors.get('username'):
            error_code = serializer.errors.get('username')[0].code
        else:
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        '''
        Не прошло валидацию из-за username:
        Если из-за наличия user'a с таким именем - повторное получение кода
        Иначе - некорректные данные
        '''
        if error_code == 'unique':
            username = serializer.initial_data.get('username')
            email = serializer.initial_data.get('email')
            user = get_object_or_404(User, username=username)

            if email == user.email:
                confirmation_code = code_generator.make_token(
                    user=user
                )
                error = sending_mail(email, confirmation_code)
                if error:
                    return Response(error, status=status.HTTP_400_BAD_REQUEST)

                return Response(serializer.data, status=status.HTTP_200_OK)

            return Response(
                'Полученная почта не является почтой данного пользователя',
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

    if code_generator.check_token(user=user, code=code):
        refresh = RefreshToken.for_user(user)

        token = {
            'token': str(refresh.access_token),
        }
        return Response(token, status=status.HTTP_200_OK)

    return Response('Неверный код', status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (OnlyForAdmin,)
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer
    lookup_field = 'username'
    pagination_class = YamdbPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('username',)

    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='me',
        permission_classes=(IsAuthenticated,)
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
        queryset = Review.objects.filter(title__id=self.kwargs.get('title_id'))
        return queryset


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.get_queryset().order_by('id').annotate(
        Avg('reviews__score')
    )
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
        queryset = Comment.objects.filter(
            review__id=self.kwargs.get('review_id'))
        return queryset


class CategoryViewSet(CreateDestroyListViewSet):
    queryset = Category.objects.get_queryset().order_by('id')
    lookup_field = 'slug'
    serializer_class = CategorySerializer
    pagination_class = YamdbPagination
    filter_backends = (filters.SearchFilter,)
    search_fields = ('=name',)
    permission_classes = (ReadOnly,)
