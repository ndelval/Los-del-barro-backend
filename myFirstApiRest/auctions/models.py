from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.models import User
from users.models import CustomUser

#! En este fichero defines las tablas de la base de datos


class Category(models.Model):
    name = models.CharField(
        max_length=50, blank=False, unique=True
    )  # Esto crea una tabla llamada Category con una columna name

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.name


class Auction(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    stock = models.IntegerField()
    brand = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, related_name="auctions", on_delete=models.CASCADE
    )
    thumbnail = models.URLField()
    creation_date = models.DateTimeField(auto_now_add=True)
    closing_date = models.DateTimeField()
    auctioneer = models.ForeignKey(
        CustomUser, related_name="auctions", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("id",)  # Las instancias se ordenarán por el id por defecto

    def __str__(self):
        return self.title  # Representación textual del objeto Auction

    @property
    def is_open(self):
        return self.closing_date > timezone.now()


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bids")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    creation_date = models.DateTimeField(auto_now_add=True)
    bidder = models.ForeignKey(
        CustomUser, related_name="bids", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.bidder} - {self.price}€"


class Rating(models.Model):
    auction = models.ForeignKey(
        Auction, on_delete=models.CASCADE, related_name="ratings"
    )
    rating = models.IntegerField()
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="ratings"
    )


class Commentary(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    creation_date = models.DateTimeField(auto_now_add=True)
    last_edit_date = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(
        CustomUser, related_name="commenter", on_delete=models.CASCADE
    )
    auction = models.ForeignKey(
        Auction, on_delete=models.CASCADE, related_name="comments"
    )


class Wallet(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="wallet"
    )
    credit_card = models.CharField(max_length=19, null=True, blank=True)
    money = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Wallet de {self.user.username}"
