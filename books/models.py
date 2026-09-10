from django.db import models


class Book(models.Model):
    class CoverChoose(models.TextChoices):
        HARD = "hard", "HARD"
        SOFT = "soft", "SOFT"

    title = models.CharField(max_length=64)
    author = models.CharField(max_length=64)
    cover = models.CharField(
        max_length=4,
        choices=CoverChoose,
        default=CoverChoose.HARD
    )
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )
