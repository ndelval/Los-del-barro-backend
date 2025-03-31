from django.shortcuts import render
from django.db.models import Q

# Create your views here.
#! Aquí defines la lógica que responde a las peticiones del usuario (GET, POST, PUT, DELETE...).
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


class CategoryListCreate(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryListCreateSerializer


class CategoryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer


class AuctionListCreate(generics.ListCreateAPIView):
    # Usamos un serializador que muestra o crea subastas
    serializer_class = AuctionListCreateSerializer
    # Si se hace un POST se llama automaticamente al metodo create que no hace falta que lo programamos viene con el generics.

    def get_queryset(self):
        # Empezamos con TODAS las subastas disponibles
        queryset = Auction.objects.all()

        # Ej: /subastas?texto=iphone
        texto = self.request.query_params.get("texto")
        if texto:
            # Buscamos si la palabra aparece en el título o en la descripción
            queryset = queryset.filter(
                Q(title__icontains=texto)
                | Q(
                    description__icontains=texto
                )  # Lo de Q ees para poder hacer consultas con or y and
            )
            # y lyego para mirar si contiene o si es mayor y tal se pone el atributo__query

        # Ej: /subastas?categoria=3
        categoria = self.request.query_params.get(
            "categoria"
        )  # esto es lo que se tendra que poner en la url
        if categoria:
            queryset = queryset.filter(category_id=categoria)

        # Ej: /subastas?precioMin=200&precioMax=800
        precio_min = self.request.query_params.get("precioMin")
        precio_max = self.request.query_params.get("precioMax")

        if precio_min:
            queryset = queryset.filter(price__gte=precio_min)  # mayor o igual
        if precio_max:
            queryset = queryset.filter(price__lte=precio_max)  # menor o igual

        # Devolvemos el queryset final con todos los filtros aplicados
        return queryset


class AuctionRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Auction.objects.all()
    serializer_class = AuctionDetailSerializer


class BidListCreate(generics.ListCreateAPIView):
    # Este método se ejecuta cuando se hace una petición GET o POST

    # Definimos cómo filtrar las pujas que queremos mostrar o manipular.
    def get_queryset(self):
        # Filtra las pujas asociadas a la subasta especificada por 'auction_id' en la URL.
        # 'self.kwargs' contiene los parámetros dinámicos de la URL (en este caso, 'auction_id').
        # Esto significa que, si vamos a '/auctions/1/bid/', solo obtendremos las pujas
        # de la subasta con 'auction_id=1'.
        return Bid.objects.filter(auction_id=self.kwargs["auction_id"])

    # Definimos qué serializer usar para esta vista.
    def get_serializer_class(self):
        # Si la solicitud es un POST (creación de una nueva puja), usamos el serializador
        # BidDetailSerializer, que incluirá más detalles (como 'auction_id') y
        # permitirá crear una nueva puja.
        if self.request.method == "POST":
            return BidDetailSerializer
        # Si la solicitud es un GET (listar pujas), usamos BidListCreateSerializer.
        # Este serializador puede ser más básico, mostrando solo los campos esenciales.
        return BidListCreateSerializer

    # Este método se ejecuta cuando una nueva puja es creada (cuando el usuario hace un POST).
    def perform_create(self, serializer):
        # Asocia la puja creada con el 'auction_id' correspondiente, que se pasa en la URL.
        # 'self.kwargs["auction_id"]' obtiene el valor de 'auction_id' de la URL
        # y lo guarda en la nueva puja. Es necesario porque al crear una puja, debemos
        # asignarla a una subasta específica.
        serializer.save(auction_id=self.kwargs["auction_id"])


class BidRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    # Esta vista permite:
    # - GET a /auctions/5/bid/12/ → para ver la puja con id=12 de la subasta con id=5
    # - PUT o PATCH a esa misma ruta → para modificar esa puja
    # - DELETE a esa misma ruta → para eliminarla

    def get_queryset(self):
        # Igual que antes, usamos self.kwargs["auction_id"] para filtrar las pujas
        # que están asociadas a la subasta concreta indicada en la URL.
        # Esto asegura que:
        # - Si pides /auctions/5/bid/12/, solo se buscará la puja 12 *dentro* de las de la subasta 5.
        # - Así evitamos que alguien pueda acceder por error (o malicia) a una puja que no pertenece a esa subasta.
        return Bid.objects.filter(auction_id=self.kwargs["auction_id"])

    def get_serializer_class(self):
        # Siempre usamos BidDetailSerializer porque vamos a trabajar con una única puja
        # y queremos mostrar/editar todos sus detalles.
        return BidDetailSerializer
