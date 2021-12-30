from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.relations import SlugRelatedField

from reviews.models import Category, Comment, Review, Genre, Title

User = get_user_model()


class SignUpSerializer(serializers.Serializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        required=True
    )
    username = serializers.CharField(
        max_length=154,
        validators=[UniqueValidator(queryset=User.objects.all())],
        required=True
    )

    def validate_username(self, username):
        if username == 'me':
            raise serializers.ValidationError(
                'Имя me запрещено'
            )

        return username


class TokenSerializer(serializers.Serializer):
    confirmation_code = serializers.CharField(max_length=64, required=True)
    username = serializers.CharField(max_length=154, required=True)


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    class Meta:
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'bio', 'role',
        )
        model = User

    def validate_username(self, username):
        if username == 'me':
            raise serializers.ValidationError(
                'Имя me запрещено'
            )

        return username


class ReviewSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        fields = ('id', 'text', 'author', 'score', 'pub_date')
        model = Review

    def validate(self, data):
        super().validate(data)

        if self.context['request'].method != 'POST':
            return data

        user = self.context['request'].user
        title_id = (
            self.context['request'].parser_context['kwargs']['title_id']
        )
        if Review.objects.filter(author=user, title__id=title_id).exists():
            raise serializers.ValidationError(
                'Вы уже оставили отзыв на данное произведение!')
        return data


class CommentSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        fields = ('id', 'text', 'author', 'pub_date')
        model = Comment


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Genre


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('name', 'slug')
        model = Category


class TitleReadSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(many=True)
    category = CategorySerializer(read_only=True)
    rating = serializers.IntegerField(
        source='reviews__score__avg', read_only=True)

    class Meta:
        fields = '__all__'
        model = Title


class TitleWriteSerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        slug_field='slug', many=True, queryset=Genre.objects.all())
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all())

    class Meta:
        fields = '__all__'
        model = Title
