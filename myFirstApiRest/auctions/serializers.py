from rest_framework import serializers
from django.utils import timezone
from .models import Category, Auction, Bid, Rating, Commentary, Wallet
from drf_spectacular.utils import extend_schema_field
from datetime import timedelta


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
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Auction
        fields = "__all__"
        read_only_fields = ["auctioneer", "category_name"]

    @extend_schema_field(serializers.BooleanField())
    def get_isOpen(self, obj):
        return obj.closing_date > timezone.now()

    def validate_closing_date(self, value):
        now = timezone.now()

        # Verifica que la fecha de cierre sea en el futuro
        if value <= now:
            raise serializers.ValidationError("Closing date must be greater than now.")

        # Verifica que la diferencia entre la fecha de creación y la fecha de cierre sea de al menos 15 días
        min_closing_date = now + timedelta(days=15)
        if value < min_closing_date:
            raise serializers.ValidationError(
                "Closing date must be at least 15 days after creation."
            )

        return value


class AuctionDetailSerializer(serializers.ModelSerializer):

    creation_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%SZ", read_only=True
    )
    closing_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    isOpen = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Auction
        fields = "__all__"
        read_only_fields = ["auctioneer", "created_at", "status"]

    @extend_schema_field(serializers.BooleanField())
    def get_isOpen(self, obj):
        return obj.closing_date > timezone.now()

    def get_bids(self, obj):
        bids = obj.bids.all().order_by("-price")  # orden descendente
        return BidSerializer(bids, many=True).data

    def validate_closing_date(self, value):
        now = timezone.now()

        # Verifica que la fecha de cierre sea en el futuro
        if value <= now:
            raise serializers.ValidationError("Closing date must be greater than now.")

        # En la edición, ya existe la fecha de creación en la base de datos
        auction = self.instance  # Obtenemos la instancia actual del modelo

        # Si la subasta ya existe, tomamos su fecha de creación real
        creation_date = auction.creation_date if auction else now

        min_closing_date = creation_date + timedelta(days=15)

        if value < min_closing_date:
            raise serializers.ValidationError(
                "Closing date must be at least 15 days after creation."
            )

        # Para calcular algo haces rating = serializer.SerializerMethodFIeld(red_only=True)
        # def get_rating(self, obj): return np.mean(obj.ratings)

        return value


class BidSerializer(serializers.ModelSerializer):
    bidder = serializers.CharField(source="bidder.username", read_only=True)

    class Meta:
        model = Bid
        fields = ["id", "auction", "price", "creation_date", "bidder"]
        read_only_fields = ["id", "creation_date", "auction", "bidder"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be a positive number.")
        return value


class UserBidSerializer(serializers.ModelSerializer):
    auction_title = serializers.CharField(source="auction.title", read_only=True)

    class Meta:
        model = Bid
        fields = ["id", "auction", "auction_title", "price", "creation_date", "bidder"]


class UserRatingSerializer(serializers.ModelSerializer):
    auction_title = serializers.CharField(source="auction.title", read_only=True)
    auction_price = serializers.CharField(source="auction.price", read_only=True)
    auction_category = serializers.CharField(source="auction.category", read_only=True)
    auction_isOpen = serializers.CharField(source="auction.is_open", read_only=True)

    class Meta:
        model = Rating
        fields = [
            "id",
            "auction_price",
            "auction_title",
            "auction_category",
            "auction_isOpen",
            "rating",
        ]


class RatingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Rating
        fields = "__all__"
        read_only_fields = ["auction", "user", "id"]  # Estos no se envian en el POST

    def validate_rating(self, value):
        if value < 0 or value > 5:
            raise serializers.ValidationError("Rating must be a number between 1-5.")
        return value


class UserCommentarySerializer(serializers.ModelSerializer):
    auction_title = serializers.CharField(source="auction.title", read_only=True)
    auction_price = serializers.CharField(source="auction.price", read_only=True)
    auction_category = serializers.CharField(source="auction.category", read_only=True)
    auction_isOpen = serializers.CharField(source="auction.is_open", read_only=True)

    class Meta:
        model = Commentary
        fields = [
            "id",
            "auction_price",
            "auction_title",
            "auction_category",
            "auction_isOpen",
            "description",
        ]


class CommentarySerializer(serializers.ModelSerializer):

    class Meta:
        model = Commentary
        fields = "__all__"
        read_only_fields = ["id", "user", "auction", "creation_date", "last_edit_date"]


class WalletSerializer(serializers.ModelSerializer):

    class Meta:
        model = Wallet
        fields = "__all__"
        read_only_fields = ["user"]

    def validate_credit_card(self, value):
        # Como ahora es CharField, no necesitamos convertir a string
        if len(value) < 13 or len(value) > 19:
            raise serializers.ValidationError(
                "Credit card length must be between 13 and 19 digits"
            )

        # Validar que solo contenga dígitos
        if not value.isdigit():
            raise serializers.ValidationError("Credit card must contain only digits")

        return value

    def validate_money(self, value):
        if abs(value) < 10:
            raise serializers.ValidationError("Minimum of 10$")
        return value
