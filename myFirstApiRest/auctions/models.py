from django.db import models


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
    rating = models.DecimalField(max_digits=3, decimal_places=2)
    stock = models.IntegerField()
    brand = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, related_name="auctions", on_delete=models.CASCADE
    )
    thumbnail = models.URLField()
    creation_date = models.DateTimeField(auto_now_add=True)
    closing_date = models.DateTimeField()

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.title


class Bid(models.Model):
    auction = models.ForeignKey(
        "Auction", on_delete=models.CASCADE, related_name="bids"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    creation_date = models.DateTimeField(auto_now_add=True)
    bidder = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.bidder} - {self.price}€"
