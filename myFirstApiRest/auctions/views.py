from django.db.models import Q, Max
from rest_framework import generics
from .models import Category, Auction, Bid
from .serializers import (
    CategoryListCreateSerializer,
    CategoryDetailSerializer,
    AuctionListCreateSerializer,
    AuctionDetailSerializer,
    BidDetailSerializer,
    BidListCreateSerializer,
)


# -----------------------------------------------------------------------------
# Vistas para Category
# -----------------------------------------------------------------------------
class CategoryListCreate(generics.ListCreateAPIView):
    # Lista todas las categorías o permite crear una nueva
    queryset = Category.objects.all()
    serializer_class = CategoryListCreateSerializer


class CategoryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    # Permite obtener, actualizar o borrar una categoría específica
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer


# -----------------------------------------------------------------------------
# Vistas para Auction
# -----------------------------------------------------------------------------
class AuctionListCreate(generics.ListCreateAPIView):
    # Muestra todas las subastas o permite crear una nueva subasta
    serializer_class = AuctionListCreateSerializer

    def get_queryset(self):
        # Empezamos con todas las subastas disponibles
        queryset = Auction.objects.all()

        # Filtramos por texto si se pasa en los query params (buscando en título o descripción)
        texto = self.request.query_params.get("texto")
        if texto:
            queryset = queryset.filter(
                Q(title__icontains=texto) | Q(description__icontains=texto)
            )

        # Filtramos por categoría si se pasa el query param 'categoria'
        categoria = self.request.query_params.get("categoria")
        if categoria:
            queryset = queryset.filter(category_id=categoria)

        # Filtramos por precio mínimo y máximo si se pasan en los query params
        precio_min = self.request.query_params.get("precioMin")
        precio_max = self.request.query_params.get("precioMax")
        if precio_min:
            queryset = queryset.filter(price__gte=precio_min)
        if precio_max:
            queryset = queryset.filter(price__lte=precio_max)

        return queryset


class AuctionRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    # Permite obtener, actualizar o borrar una subasta específica
    queryset = Auction.objects.all()
    serializer_class = AuctionDetailSerializer


# -----------------------------------------------------------------------------
# Vistas para Bid
# -----------------------------------------------------------------------------
class BidListCreate(generics.ListCreateAPIView):
    # Muestra todas las pujas para una subasta o permite crear una nueva puja

    def get_queryset(self):
        # Filtra las pujas para la subasta cuyo ID se pasa en la URL
        return Bid.objects.filter(auction_id=self.kwargs["auction_id"])

    def get_serializer_class(self):
        # Usa BidDetailSerializer para POST (crear) y BidListCreateSerializer para GET (listar)
        if self.request.method == "POST":
            return BidDetailSerializer
        return BidListCreateSerializer

    def get_serializer_context(self):
        # Agrega el auction_id al contexto para que el serializer pueda acceder a él
        context = super().get_serializer_context()
        context["auction_id"] = self.kwargs["auction_id"]
        return context

    def perform_create(self, serializer):
        # La validación se traslada al serializer.
        # Se asocia la puja creada con el auction_id obtenido de la URL.
        serializer.save(auction_id=self.kwargs["auction_id"])


class BidRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    # Permite obtener, actualizar o borrar una puja específica para una subasta

    def get_queryset(self):
        # Filtra las pujas que pertenecen a la subasta cuyo ID se pasa en la URL
        return Bid.objects.filter(auction_id=self.kwargs["auction_id"])

    def get_serializer_class(self):
        # Siempre se usa BidDetailSerializer para ver, editar o borrar una puja específica
        return BidDetailSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["auction_id"] = self.kwargs["auction_id"]
        return context

    def perform_update(self, serializer):
        # La validación en actualización se realiza en el serializer
        serializer.save()

    def perform_destroy(self, instance):
        # Se elimina la puja. La validación para borrar (por ejemplo, que la subasta esté abierta) se encuentra en el serializer

        instance.delete()
