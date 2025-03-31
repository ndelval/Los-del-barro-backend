from django.utils import timezone
from rest_framework import serializers
from .models import Category, Auction, Bid
from drf_spectacular.utils import extend_schema_field
from datetime import timedelta


#: Los serializers toman objetos complejos de Python, como instancias de modelos de Django, y los convierten en formatos de datos simples y estructurados como JSON
class CategoryListCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name"]


class CategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class AuctionListCreateSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%SZ", read_only=True
    )
    closing_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    isOpen = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Auction
        fields = "__all__"

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El stock debe ser un número natural positivo."
            )
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El precio debe ser un número natural positivo."
            )
        return value

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La valoración debe estar entre 1 y 5.")
        return value

    def validate_closing_date(self, value):
        creation_date = timezone.now()
        min_date = creation_date + timedelta(days=15)
        if value <= creation_date:
            raise serializers.ValidationError(
                "La fecha de cierre debe ser posterior a la de creación."
            )
        if value < min_date:
            raise serializers.ValidationError(
                "La fecha de cierre debe ser al menos 15 días posterior a la creación."
            )
        return value

    @extend_schema_field(serializers.BooleanField())
    def get_isOpen(self, obj):
        return obj.closing_date > timezone.now()


class AuctionDetailSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%SZ", read_only=True
    )
    closing_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    isOpen = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Auction
        fields = "__all__"

    @extend_schema_field(serializers.BooleanField())
    def get_isOpen(self, obj):
        return obj.closing_date > timezone.now()


class BidListCreateSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%SZ", read_only=True
    )

    class Meta:
        model = Bid
        fields = ["id", "price", "bidder", "creation_date"]


class BidDetailSerializer(serializers.ModelSerializer):
    creation_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%SZ", read_only=True
    )

    class Meta:
        model = Bid
        fields = "__all__"
