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

)

app_name = "auctions"

urlpatterns = [
    path('categories/', CategoryListCreate.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroy.as_view(), name='category-detail'),
    path('', AuctionListCreate.as_view(), name='auction-list-create'),
    path('<int:pk>/', AuctionRetrieveUpdateDestroy.as_view(), name='auction-detail'),
    path('<int:auction_id>/bids/', BidListCreateView.as_view(), name='bid-list-create'),
    path('<int:auction_id>/bids/<int:bid_id>/', BidRetrieveUpdateDestroyView.as_view(), name='bid-retrieve-update-destroy'),
    path('users/', UserAuctionListView.as_view(), name='action-from-users'),
    path('users/bids/', UserBidListView.as_view(), name='bids-from-users'),
]


