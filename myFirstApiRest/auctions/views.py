# Create your views here.
from rest_framework import generics, status, viewsets

from users.models import CustomUser

# from myFirstApiRest.users.models import CustomUser
from .models import Category, Auction, Bid, Commentary, Rating, Wallet, Favorites
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
    FavoritesSerializer,
)
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
    """
    FLUJO DE CategoryListCreate(generics.ListCreateAPIView):
    -----------------------------------------------------
    1. PARA GET (listar categorías):
    - Usa queryset = Category.objects.all() para obtener todos los objetos
    - Los serializa con el serializer_class (CategoryListCreateSerializer)
    - Devuelve JSON con todas las categorías

    2. PARA POST (crear categoría):
    - Recibe datos JSON en la petición
    - Usa el serializer_class (CategoryListCreateSerializer) para validar
    - Si es válido, crea nueva categoría en la base de datos
    - Devuelve la categoría creada en formato JSON
    """

    permission_classes = [AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategoryListCreateSerializer


class CategoryRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    """
    FLUJO DE CategoryRetrieveUpdateDestroy (RetrieveUpdateDestroyAPIView):
    --------------------------------------------------------------------
    Esta vista maneja operaciones sobre una categoría específica por ID (/categories/1/)

    1. PARA GET (obtener una categoría):
    - Recibe URL con ID: /api/auctions/categories/5/
    - Busca la categoría con ID=5 en queryset = Category.objects.all()
    - La serializa con CategoryDetailSerializer
    - Devuelve JSON con los datos de esa categoría

    2. PARA PUT/PATCH (actualizar categoría):
    - Recibe URL con ID y datos JSON en la petición
    - Busca la categoría con ese ID
    - Valida los datos con CategoryDetailSerializer
    - Actualiza la categoría en la base de datos
    - Devuelve la categoría actualizada en formato JSON

    3. PARA DELETE (eliminar categoría):
    - Recibe URL con ID: /api/auctions/categories/5/
    - Busca y elimina la categoría con ID=5
    - Devuelve respuesta 204 No Content (sin datos)

    """

    permission_classes = [AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer


class AuctionListCreate(generics.ListCreateAPIView):
    """
    FLUJO INTERNO DE ListCreateAPIView:
    ----------------------------------
    - Recibe petición HTTP
    - IDENTIFICA el método (GET o POST)
    - REDIRECCIONA a la función apropiada:
    - GET → list() → usa get_queryset()
    - POST → create() → usa perform_create()

    Cada método solo se ejecuta cuando corresponde.
    """

    serializer_class = AuctionListCreateSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]  # o deja que sea público el GET

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

        # Parseo y validación
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
        if min_rating:
            min_rating = float(min_rating)
            queryset = queryset.filter(rating__gte=min_rating)

        if isOpen:
            is_open_value = isOpen.lower() == "true"

            if is_open_value:
                queryset = queryset.filter(closing_date__gt=timezone.now())
            else:
                queryset = queryset.filter(closing_date__lte=timezone.now())

        return queryset

    # Se va a ejecutar cuadno se haga un POST que llamara al create() y eso llamara a esto
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

        initial_price = auction.price
        new_price = serializer.validated_data["price"]

        if new_price <= initial_price:
            raise ValidationError(
                {"price": "La puja debe ser mayor al precio inicial."},
                code=status.HTTP_400_BAD_REQUEST,
            )
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
    """
    FLUJO DE EDICIÓN DE PUJAS:
    -------------------------
    1. Cliente envía PUT/PATCH a /api/auctions/{auction_id}/bids/{bid_id}/
    - Ejemplo: PUT /api/auctions/5/bids/12/ con {"price": 150}

    2. BidRetrieveUpdateDestroyView recibe la petición y:
    - Extrae auction_id=5 y bid_id=12 de la URL
    - Ejecuta get_object() con estas validaciones:

    a) ¿La puja existe y pertenece a la subasta?
        bid = get_object_or_404(Bid, id=bid_id, auction__id=auction_id)
        ↑ Si no existe: devuelve error 404

    b) ¿El usuario actual es quien hizo la puja?
        if bid.bidder.username != self.request.user.username:
            raise ValidationError("Solo puedes modificar tus pujas.")
        ↑ Si no es tu puja: error 400

    c) ¿La subasta sigue abierta?
        if bid.auction.closing_date <= timezone.now():
            raise ValidationError("No puedes modificar pujas en subastas cerradas.")
        ↑ Si ya cerró: error 400

    3. Si pasa todas las validaciones:
    - Se actualiza la puja con los datos enviados
    - Se devuelve respuesta 200 OK con los datos actualizados
    """

    serializer_class = BidSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        auction_id = self.kwargs["auction_id"]
        bid_id = self.kwargs["bid_id"]
        # Esto solo te va a devolver una puja
        # Como quiero acceder al campo de otra tabla pongo el nombre de la tabla __ campo
        bid = get_object_or_404(Bid, id=bid_id, auction__id=auction_id)

        if bid.bidder.username != self.request.user.username:
            raise ValidationError("Solo puedes modificar tus pujas.")

        if bid.auction.closing_date <= timezone.now():
            raise ValidationError("No puedes modificar pujas en subastas cerradas.")

        return bid

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
        # Aqui tienes que devolver un conjunto de objetoc por eso es necesairo el filter asi
        # No necesitas auction_id si solo quieres las pujas del usuario
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
        # user_ratings = self.request.user.ratings.all() otra forma
        return user_ratings


class RatingListCreateView(generics.ListCreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Esto me devuelve el objeto auction que realmente es lo que esta en la entrada de la tabla
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
        # Esto me devuelve el objeto auction que realmente es lo que esta en la entrada de la tabla
        auction = get_object_or_404(Auction, id=self.kwargs["auction_id"])
        return Commentary.objects.filter(auction=auction)

    def perform_create(self, serializer):
        auction = get_object_or_404(Auction, id=self.kwargs["auction_id"])
        serializer.save(user=self.request.user, auction=auction)


class CommentaryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentarySerializer

    permission_classes = [IsAuthenticated]

    def get_object(self):  # Esto consigue el objeto para luego editarlo
        auction_id = self.kwargs["auction_id"]
        comment_id = self.kwargs["comment_id"]
        # Esto solo te va a devolver una puja
        # Como quiero acceder al campo de otra tabla pongo el nombre de la tabla __ campo
        comment = get_object_or_404(Commentary, id=comment_id, auction__id=auction_id)

        if comment.user.username != self.request.user.username:
            raise ValidationError("Solo puedes modificar tus comentarios.")

        return comment

    def perform_update(self, serializer):
        # Actualiza el comentario y establece la fecha actual como última edición
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
        # otra alternativa seria hacer return get_object_or_404(Wallet, user=self.request.user)
        wallet = Wallet.objects.get(
            user=self.request.user
        )  # Con filter devuelves un queryset a no ser que hagas first()
        return wallet

    def perform_update(self, serializer):
        # Si están añadiendo dinero, lo sumamos al saldo existente
        if "money" in serializer.validated_data:
            try:
                money_to_add = float(serializer.validated_data["money"])
                # Obtenemos la billetera actual
                wallet = self.get_object()
                # Sumamos el dinero al saldo actual
                total_money = float(wallet.money) + money_to_add
                if total_money < 0:
                    raise ValidationError(
                        "No puedes retirar mas cantidad de la que tienes"
                    )
                # Actualizamos el valor en los datos validados antes de guardar
                serializer.validated_data["money"] = total_money
            except ValueError:
                raise ValidationError({"money": "El valor debe ser un número válido."})

        # Guardamos los cambios
        serializer.save()


class FavoritesListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoritesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        auction_id = self.kwargs["auction_id"]
        auction = get_object_or_404(Auction, id=self.kwargs["auction_id"])
        queryset = Favorites.objects.filter(auction=auction, user=self.request.user)
        return queryset

    def perform_create(self, serializer):
        auction_id = self.kwargs["auction_id"]
        auction = Auction.objects.get(id=auction_id)
        serializer.save(auction=auction, user=self.request.user)


class FavoritesRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FavoritesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        auction_id = self.kwargs["auction_id"]
        auction = get_object_or_404(Auction, id=self.kwargs["auction_id"])
        print(auction)
        queryset = Favorites.objects.filter(auction=auction, user=self.request.user)
        print(queryset)
        return queryset

    #! IMPORTANTE si haces un retirve update delete en una url sin pk tienes que modificar a mano el get_object
    def get_object(self):
        queryset = self.get_queryset()
        # Obtener el primer objeto (debería ser único por usuario y subasta)
        favorite = queryset.first()
        if not favorite:
            raise ValidationError("No se encontró el favorito para esta subasta.")
        return favorite


"""

1. Listar (GET colección, p.ej. ListAPIView / ListCreateAPIView)
dispatch()

    get(request…) → list(request…)

    get_queryset()

    filter_queryset(qs)

    paginate_queryset(qs)

    get_serializer(page, many=True)

    Response(serializer.data) (o paginada)

    No hay get_object() ni perform_create / perform_update aquí.

2. Recuperar detalle (GET único, RetrieveAPIView)
dispatch()

    get(request…) → retrieve(request…)

    get_object()

    internamente hace get_queryset() → filter_queryset() → lookup por PK

    get_serializer(obj)

    Response(serializer.data)

3. Crear (POST, CreateAPIView / ListCreateAPIView)
dispatch()

    post(request…) → create(request…)

    get_serializer(data=request.data)

    serializer.is_valid(raise_exception=True)

    perform_create(serializer) (por defecto serializer.save())

    Response(serializer.data, status=201)

    No se invoca get_queryset() ni get_object().

4. Actualizar (PUT/PATCH, UpdateAPIView / RetrieveUpdateAPIView)
dispatch()

    put/patch(request…) → update(request…) / partial_update(request…)

    get_object()

    get_serializer(instance, data=request.data, partial=…)

    serializer.is_valid(raise_exception=True)

    perform_update(serializer) (por defecto serializer.save())

    Response(serializer.data)

5. Borrar (DELETE, DestroyAPIView / RetrieveDestroyAPIView)
dispatch()

    delete(request…) → destroy(request…)

    get_object() -> que llama a get_queryset

    perform_destroy(instance) (por defecto instance.delete())

    Response(status=204)

Resumen de cuándo se llaman

    get_queryset() → siempre que necesites una lista (list) o como base de get_object().

    get_object() → en retrieve, update y destroy; internamente llama a get_queryset().

    get_serializer(data=…) → en create.

    get_serializer(instance,…) → en list, retrieve y update.

    hooks (perform_create, perform_update, perform_destroy) reciben el serializer o la instancia ya obtenida y ejecutan el .save() o .delete().


"""
