from django.urls import path
from .views import (
    CategoryListCreate,
    CategoryRetrieveUpdateDestroy,
    AuctionListCreate,
    AuctionRetrieveUpdateDestroy,
    BidListCreate,
    BidRetrieveUpdateDestroy,
)

app_name = "auctions"

urlpatterns = [
    # Categorías
    path("categorias", CategoryListCreate.as_view(), name="category-list-create"),
    path(
        "categoria/<int:pk>",
        CategoryRetrieveUpdateDestroy.as_view(),
        name="category-detail",
    ),
    # Subastas
    path(
        "", AuctionListCreate.as_view(), name="auction-list-create"
    ),  # GET con filtros y POST
    path(
        "<int:pk>",
        AuctionRetrieveUpdateDestroy.as_view(),
        name="auction-detail",
    ),  # GET, PUT, DELETE
    # Pujas
    path(
        "<int:auction_id>/pujas/",
        BidListCreate.as_view(),
        name="bid-list-create",
    ),  # GET, POST
    path(
        "<int:auction_id>/pujas/<int:pk>",
        BidRetrieveUpdateDestroy.as_view(),
        name="bid-detail",
    ),  # GET, PUT, DELETE
]
