from django.utils import timezone
from rest_framework import serializers
from .models import Category, Auction, Bid
from drf_spectacular.utils import extend_schema_field
from datetime import timedelta
from django.db.models import Max


#: Los serializers toman objetos complejos de Python, como instancias de modelos de Django, y los convierten en formatos de datos simples y estructurados como JSON
class CategoryListCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ["id", "name"]


class CategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category  # Que modelo vamos a estar usando cuando llamemos a esto
        fields = (
            "__all__"  # Que es los datos que vamos a enviar o a recibir en formato json
        )


class AuctionListCreateSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source="category.name", read_only=True
    )  # Es como que accedemos al nombre de nuestra foregin key
    creation_date = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%SZ", read_only=True
    )
    closing_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    isOpen = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Auction
        fields = "__all__"

    # Tanto validate como stock se van a ejecutar automaticamente validate_<campo> donde campo sera una de tus columnas
    # El validate se ejecuta cuando se hace un POST/PUT/PATCH y el get se hace con todos esos mas el GET
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
    category_name = serializers.CharField(source="category.name", read_only=True)
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
    auction = serializers.PrimaryKeyRelatedField(read_only=True)

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "El precio debe ser un número natural positivo."
            )
        return value

    def validate(self, data):
        """
        Validación global para la puja:
        - Verifica que la subasta esté abierta.
        - Compara el nuevo precio con la puja más alta actual.
        """
        # Obtenemos auction_id del contexto, que debe ser proporcionado por la vista
        auction_id = self.context.get("auction_id")
        if not auction_id:
            raise serializers.ValidationError(
                "El ID de la subasta es obligatorio en el contexto."
            )

        # Recuperamos la subasta
        try:
            auction = Auction.objects.get(id=auction_id)
        except Auction.DoesNotExist:
            raise serializers.ValidationError("La subasta no existe.")

        # Validamos que la subasta esté abierta utilizando la propiedad is_open
        if not auction.is_open:
            raise serializers.ValidationError(
                "La subasta ya está cerrada. No se puede pujar."
            )

        # Obtenemos la puja más alta actual para la subasta
        highest_bid = Bid.objects.filter(auction=auction).aggregate(
            max_price=Max("price")
        )["max_price"]
        if highest_bid is None:
            highest_bid = auction.price

        new_price = data.get("price")
        if new_price <= highest_bid:
            raise serializers.ValidationError(
                "El precio de la nueva puja debe ser mayor que la puja ganadora actual."
            )

        return data

    def create(self, validated_data):
        """
        Asigna la subasta a la puja utilizando auction_id del contexto antes de crear la instancia.
        """
        auction_id = self.context.get("auction_id")
        validated_data["auction_id"] = auction_id
        return super().create(validated_data)

    class Meta:
        model = Bid
        fields = "__all__"
