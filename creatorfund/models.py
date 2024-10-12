from django.db import models
from django.core.validators import validate_email
from django.utils import timezone

class CreatorFund(models.Model):
    available_money = models.PositiveIntegerField()
    next_payout = models.DateTimeField(default=timezone.datetime(2024,10,27))

class CreatorGroup(models.Model):
    percentage_share = models.PositiveIntegerField()
    name = models.CharField(max_length=50)
    members = models.ManyToManyField("Creator", blank=True)
    id = models.SlugField(primary_key=True)

class Creator(models.Model):
    profile = models.ForeignKey("profiles.Profile", on_delete=models.CASCADE)
    paypal_email = models.EmailField(validators=[validate_email], unique=True)
    percentage_share = models.PositiveIntegerField(default=0)
    creator_fund = models.ForeignKey(CreatorFund, on_delete=models.CASCADE)
    id = models.SlugField(primary_key=True)