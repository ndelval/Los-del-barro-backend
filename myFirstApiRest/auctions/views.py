# Create your views here.
from rest_framework import generics, status

from users.models import CustomUser


from .models import Category, Auction, Bid, Commentary, Rating, Wallet
from .serializers import (
    CategoryListCreateSerializer,
    CategoryDetailSerializer,
    AuctionListCreateSerializer,
    AuctionDetailSerializer,
    BidSerializer,
    UserBidSerializer,
    RatingSerializer,
    CommentarySerializer,
    UserRatingSerializer,
    WalletSerializer,
    UserCommentarySerializer,
)
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .permissions import IsOwnerOrAdmin, IsBidOwnerOrAdmin, IsCommentOwnerOrAdmin
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django.utils.dateparse import parse_datetime, parse_date
from django.utils import timezone
from django.shortcuts import get_object_or_404


class CategoryListCreate(generics.ListCreateAPIView):
    permission_classes = [AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategoryListCreateSerializer


class CategoryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer


class AuctionListCreate(generics.ListCreateAPIView):

    serializer_class = AuctionListCreateSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    # Se va a ejecutar cuando se haga un GET que llamara al list y eso llamara a esto
    def get_queryset(self):
        queryset = Auction.objects.all()
        params = self.request.query_params
        search = params.get("search", None)
        category_id = params.get("category", None)
        min_price = params.get("minPrice", None)
        max_price = params.get("maxPrice", None)
        min_date = params.get("minDate", None)
        min_rating = params.get("minRating", None)
        isOpen = params.get("isOpen", None)
        print(f"min_date recibido: {min_date}, tipo: {type(min_date)}")
        # Filtro por búsqueda de texto (titulo o descripción)
        if search:
            if search == "" or len(search) < 3:
                raise ValidationError(
                    {
                        "search": "La consulta de búsqueda debe tener al menos 3 caracteres."
                    },
                    code=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Filtro por categoría
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                queryset = queryset.filter(category=category)
            except Category.DoesNotExist:
                raise ValidationError(
                    {"category": "Categoría no encontrada."},
                    code=status.HTTP_400_BAD_REQUEST,
                )

        # Filtro por rango de precios

        if min_price is not None:
            try:
                min_price = float(min_price)
                if min_price < 0:
                    raise ValidationError(
                        {"minPrice": "El precio mínimo debe ser 0 o mayor."},
                        code=status.HTTP_400_BAD_REQUEST,
                    )
                queryset = queryset.filter(price__gte=min_price)
            except ValueError:
                raise ValidationError(
                    {"minPrice": "El precio mínimo debe ser un número válido."},
                    code=status.HTTP_400_BAD_REQUEST,
                )

        if max_price is not None:
            try:
                max_price = float(max_price)
                if max_price <= 0:
                    raise ValidationError(
                        {"maxPrice": "El precio máximo debe ser mayor que 0."},
                        code=status.HTTP_400_BAD_REQUEST,
                    )
            except ValueError:
                raise ValidationError(
                    {"maxPrice": "El precio máximo debe ser un número válido."},
                    code=status.HTTP_400_BAD_REQUEST,
                )

        # Comparación entre ambos (ya convertidos a float o None)
        if min_price is not None and max_price is not None:
            if max_price <= min_price:
                raise ValidationError(
                    {
                        "maxPrice": "El precio máximo debe ser mayor que el precio mínimo."
                    },
                    code=status.HTTP_400_BAD_REQUEST,
                )

        # Aplicación del filtro de max_price
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        if min_date:
            try:
                min_date_parsed = parse_date(min_date)
                if not min_date_parsed:
                    raise ValidationError(
                        {"minDate": "Formato de fecha no válido. Usa YYYY-MM-DD."},
                        code=status.HTTP_400_BAD_REQUEST,
                    )
                queryset = queryset.filter(closing_date__lte=min_date_parsed)
            except Exception:
                raise ValidationError(
                    {"minDate": "Formato de fecha no válido."},
                    code=status.HTTP_400_BAD_REQUEST,
                )
        # Filtro por rating
        if min_rating:
            min_rating = float(min_rating)
            queryset = queryset.filter(rating__gte=min_rating)
        # Filtro por si una subasta esta abierta o no
        if isOpen:
            is_open_value = isOpen.lower() == "true"

            if is_open_value:
                queryset = queryset.filter(closing_date__gt=timezone.now())
            else:
                queryset = queryset.filter(closing_date__lte=timezone.now())

        return queryset

    def perform_create(self, serializer):
        serializer.save(auctioneer=self.request.user)


class AuctionRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):

    permission_classes = [IsOwnerOrAdmin]
    queryset = Auction.objects.all()
    serializer_class = AuctionDetailSerializer


class BidListCreateView(generics.ListCreateAPIView):

    serializer_class = BidSerializer

    def get_queryset(self):
        auction_id = self.kwargs["auction_id"]
        return Bid.objects.filter(auction__id=auction_id).order_by("-price")

    def perform_create(self, serializer):
        auction_id = self.kwargs["auction_id"]
        auction = get_object_or_404(Auction, id=auction_id)

        highest_bid = auction.bids.order_by("-price").first()
        new_price = serializer.validated_data["price"]

        # Validación para puja más alta
        if highest_bid and new_price <= highest_bid.price:
            raise ValidationError(
                {"price": "La puja debe ser mayor a la puja más alta."},
                code=status.HTTP_400_BAD_REQUEST,
            )

        # Validación para puja positiva
        if new_price <= 0:
            raise ValidationError({"price": "El precio de la puja debe ser positivo."})

        # Validación de saldo suficiente en la billetera
        try:
            wallet = Wallet.objects.get(user=self.request.user)
            if wallet.money < new_price:
                raise ValidationError(
                    {
                        "price": "No tienes suficiente saldo en tu billetera para realizar esta puja."
                    },
                    code=status.HTTP_400_BAD_REQUEST,
                )
        except Wallet.DoesNotExist:
            raise ValidationError(
                {
                    "wallet": "No tienes una billetera creada. Crea una billetera antes de pujar."
                },
                code=status.HTTP_400_BAD_REQUEST,
            )

        serializer.save(auction=auction, bidder=self.request.user)

    def get_permissions(self):
        if self.request.method == "GET":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class BidRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated, IsBidOwnerOrAdmin]

    def get_queryset(self):
        auction_id = self.kwargs["auction_id"]
        return Bid.objects.filter(auction__id=auction_id)


    def perform_update(self, serializer):
        new_price = serializer.validated_data["price"]
        try:
            wallet = Wallet.objects.get(user=self.request.user)
            if float(wallet.money) < float(new_price):
                raise ValidationError(
                    {
                        "price": "No tienes suficiente saldo en tu billetera para realizar esta puja."
                    },
                    code=status.HTTP_400_BAD_REQUEST,
                )
        except Wallet.DoesNotExist:
            raise ValidationError(
                {
                    "wallet": "No tienes una billetera creada. Crea una billetera antes de pujar."
                },
                code=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()


class UserAuctionListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Obtener las subastas del usuario autenticado
        user_auctions = Auction.objects.filter(auctioneer=request.user)
        serializer = AuctionListCreateSerializer(user_auctions, many=True)
        return Response(serializer.data)


class UserBidListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user_bids = Bid.objects.filter(bidder=self.request.user)
        return user_bids

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = UserBidSerializer(queryset, many=True)
        return Response(serializer.data)


class UserRatingListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserRatingSerializer

    def get_queryset(self):
        user_ratings = Rating.objects.filter(user=self.request.user)

        return user_ratings


class RatingListCreateView(generics.ListCreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        auction = get_object_or_404(Auction, id=self.kwargs["auction_id"])
        return Rating.objects.filter(user=self.request.user, auction=auction)

    def perform_create(self, serializer):
        auction = get_object_or_404(Auction, id=self.kwargs["auction_id"])
        # Esto es un poco una manera de hacer el update sin tener una view para ello y a que me complicaba mucho el front
        Rating.objects.filter(user=self.request.user, auction=auction).delete()
        new_rating = serializer.validated_data.get("rating")
        if new_rating != 0:
            rating = serializer.save(user=self.request.user, auction=auction)

        # Actualiza el rating promedio en la subasta
        all_ratings = auction.ratings.all()
        if all_ratings.exists():
            total = sum(r.rating for r in all_ratings)
            auction.rating = round(total / all_ratings.count(), 2)
        else:
            auction.rating = 1
        auction.save(update_fields=["rating"])



class UserCommentaryListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserCommentarySerializer

    def get_queryset(self):
        return Commentary.objects.filter(user=self.request.user)


class CommentaryListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentarySerializer

    def get_queryset(self):

        auction = get_object_or_404(Auction, id=self.kwargs["auction_id"])
        return Commentary.objects.filter(auction=auction)

    def perform_create(self, serializer):
        auction = get_object_or_404(Auction, id=self.kwargs["auction_id"])
        serializer.save(user=self.request.user, auction=auction)




class CommentaryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentarySerializer
    permission_classes = [IsAuthenticated, IsCommentOwnerOrAdmin]

    def get_queryset(self):
        auction_id = self.kwargs['auction_id']
        auction = Auction.objects.get(id=auction_id)
        return Commentary.objects.filter(auction=auction)
    
    def perform_update(self, serializer):
        serializer.save(last_edit_date=timezone.now())





class WalletListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WalletSerializer

    def get_queryset(self):

        return Wallet.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WalletRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WalletSerializer

    def get_object(self):

        wallet = Wallet.objects.get(user=self.request.user)
        return wallet

    def perform_update(self, serializer):
        # Si están añadiendo dinero, lo sumamos al saldo existente
        if "money" in serializer.validated_data:
            try:
                money_to_add = float(serializer.validated_data["money"])

                wallet = self.get_object()
                # Sumamos el dinero recibido por el PUT al saldo actual
                total_money = float(wallet.money) + money_to_add
                if total_money < 0:
                    raise ValidationError(
                        "No puedes retirar mas cantidad de la que tienes"
                    )
                # Actualizamos el valor en los datos validados antes de guardar
                serializer.validated_data["money"] = total_money
            except ValueError:
                raise ValidationError({"money": "El valor debe ser un número válido."})

        serializer.save()
