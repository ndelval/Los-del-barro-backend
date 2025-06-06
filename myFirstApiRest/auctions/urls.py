from django.urls import path
from .views import (
    CategoryListCreate,
    CategoryRetrieveUpdateDestroy,
    AuctionListCreate,
    AuctionRetrieveUpdateDestroy,
    BidListCreateView,
    BidRetrieveUpdateDestroyView,
    UserAuctionListView,
    UserBidListView,
    RatingListCreateView,
    CommentaryListCreateView,
    CommentaryRetrieveUpdateDestroyView,
    UserRatingListView,
    WalletListCreateView,
    WalletRetrieveUpdateDestroyView,
    UserCommentaryListView,
    FavoritesListCreateView,
    FavoritesRetrieveUpdateDestroyView,
)

app_name = "auctions"

urlpatterns = [
    path("categories/", CategoryListCreate.as_view(), name="category-list-create"),
    path(
        "categories/<int:pk>/",
        CategoryRetrieveUpdateDestroy.as_view(),
        name="category-detail",
    ),
    path("", AuctionListCreate.as_view(), name="auction-list-create"),
    path("<int:pk>/", AuctionRetrieveUpdateDestroy.as_view(), name="auction-detail"),
    path("<int:auction_id>/bids/", BidListCreateView.as_view(), name="bid-list-create"),
    path(
        "<int:auction_id>/bids/<int:pk>/",
        BidRetrieveUpdateDestroyView.as_view(),
        name="bid-retrieve-update-destroy",
    ),
    path("users/", UserAuctionListView.as_view(), name="action-from-users"),
    path("users/bids/", UserBidListView.as_view(), name="bids-from-users"),
    path("users/ratings/", UserRatingListView.as_view(), name="ratings-from-users"),
    path(
        "users/comments/", UserCommentaryListView.as_view(), name="comments-from-users"
    ),
    path("users/wallet/", WalletListCreateView.as_view(), name="wallet-create"),
    path(
        "users/wallet/update/",
        WalletRetrieveUpdateDestroyView.as_view(),
        name="wallet-update",
    ),
    path(
        "<int:auction_id>/ratings/",
        RatingListCreateView.as_view(),
        name="rating-create",
    ),
    path(
        "<int:auction_id>/comments/",
        CommentaryListCreateView.as_view(),
        name="comment-list-create",
    ),
    path(
        "<int:auction_id>/comments/<int:pk>/",
        CommentaryRetrieveUpdateDestroyView.as_view(),
        name="comment-retrieve-update-destroy",
    ),
    path(
        "<int:auction_id>/favorites/add/",
        FavoritesListCreateView.as_view(),
        name="favorites-add",
    ),
    path(
        "<int:auction_id>/favorites/change/",
        FavoritesRetrieveUpdateDestroyView.as_view(),
        name="favorites-change",
    ),
]
