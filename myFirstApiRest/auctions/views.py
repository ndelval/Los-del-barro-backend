
# Create your views here.
from rest_framework import generics, status
from .models import Category, Auction, Bid
from .serializers import CategoryListCreateSerializer, CategoryDetailSerializer, AuctionListCreateSerializer, AuctionDetailSerializer, BidSerializer, UserBidSerializer
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .permissions import IsOwnerOrAdmin
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
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]  # o deja que sea público el GET

    def get_queryset(self):
        queryset = Auction.objects.all()
        params = self.request.query_params
        search = params.get('search', None)
        category_id = params.get('category', None)
        min_price = params.get('minPrice', None)
        max_price = params.get('maxPrice', None)
        min_date = params.get('minDate', None)

        # Filtro por búsqueda de texto (titulo o descripción)
        if search:
            if search == "" or len(search) < 3:
                raise ValidationError(
                    {"search": "La consulta de búsqueda debe tener al menos 3 caracteres."},
                    code=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))

        # Filtro por categoría
        if category_id:
            try:
                category = Category.objects.get(id=category_id)
                queryset = queryset.filter(category=category)
            except Category.DoesNotExist:
                raise ValidationError(
                    {"category": "Categoría no encontrada."},
                    code=status.HTTP_400_BAD_REQUEST
                )

        # Filtro por rango de precios

        # Parseo y validación
        if min_price is not None:
            try:
                min_price = float(min_price)
                if min_price < 0:
                    raise ValidationError(
                        {"minPrice": "El precio mínimo debe ser 0 o mayor."},
                        code=status.HTTP_400_BAD_REQUEST
                    )
                queryset = queryset.filter(price__gte=min_price)
            except ValueError:
                raise ValidationError(
                    {"minPrice": "El precio mínimo debe ser un número válido."},
                    code=status.HTTP_400_BAD_REQUEST
                )

        if max_price is not None:
            try:
                max_price = float(max_price)
                if max_price <= 0:
                    raise ValidationError(
                        {"maxPrice": "El precio máximo debe ser mayor que 0."},
                        code=status.HTTP_400_BAD_REQUEST
                    )
            except ValueError:
                raise ValidationError(
                    {"maxPrice": "El precio máximo debe ser un número válido."},
                    code=status.HTTP_400_BAD_REQUEST
                )

        # Comparación entre ambos (ya convertidos a float o None)
        if min_price is not None and max_price is not None:
            if max_price <= min_price:
                raise ValidationError(
                    {"maxPrice": "El precio máximo debe ser mayor que el precio mínimo."},
                    code=status.HTTP_400_BAD_REQUEST
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
                        code=status.HTTP_400_BAD_REQUEST
                    )
                queryset = queryset.filter(closing_date__date__gte=min_date_parsed)
            except Exception:
                raise ValidationError(
                    {"minDate": "Formato de fecha no válido."},
                    code=status.HTTP_400_BAD_REQUEST
                )

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
        auction_id = self.kwargs['auction_id']
        return Bid.objects.filter(auction__id=auction_id).order_by('-price')

    def perform_create(self, serializer):
        auction_id = self.kwargs['auction_id']
        auction = get_object_or_404(Auction, id=auction_id)

        highest_bid = auction.bids.order_by('-price').first()
        new_price = serializer.validated_data['price']
        if highest_bid and new_price <= highest_bid.price:
            raise ValidationError(
                {"price": "La puja debe ser mayor a la puja más alta."},
                code=status.HTTP_400_BAD_REQUEST
            )
        if new_price <= 0:
            raise ValidationError("El precio de la puja debe ser positivo.")
        
        serializer.save(auction=auction, bidder=self.request.user)

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class BidRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        auction_id = self.kwargs['auction_id']
        bid_id = self.kwargs['bid_id']
        
        bid = get_object_or_404(Bid, id=bid_id, auction__id=auction_id)

        if bid.bidder.username != self.request.user.username:
            raise ValidationError("Solo puedes modificar tus pujas.")

        if bid.auction.closing_date <= timezone.now():
            raise ValidationError("No puedes modificar pujas en subastas cerradas.")

        return bid


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
        # No necesitas auction_id si solo quieres las pujas del usuario
        user_bids = Bid.objects.filter(bidder=self.request.user)
        return user_bids

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = UserBidSerializer(queryset, many=True)
        return Response(serializer.data)