from rest_framework import serializers
from .models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'birth_date', 'municipality', 'locality', 'password')
        extra_kwargs = {'password': {'write_only': True},
        }
    def validate_email(self, value):
        user = self.instance # Solo tiene valor cuando se está actualizando
        if CustomUser.objects.filter(email=value).exclude(pk=user.pk if user else None).exists():
            raise serializers.ValidationError("Email already in used.")
        return value
    
    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

