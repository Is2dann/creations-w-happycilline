from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django_countries.fields import CountryField


phone_validator = RegexValidator(
    regex=r'^\+?[0-9\s\-()]{7,20}$',
    message=(
        "Please enter a valid phone number using digits, spaces, "
        "brackets and an optional leading + sign."
    ),
)

uk_postcode_validator = RegexValidator(
    # Simple but realistic UK postcode pattern, e.g. SW1A 1AA
    regex=r'^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$',
    message="Please enter a valid UK postcode, e.g. SW1A 1AA.",
    code='invalid_postcode',
)


class UserProfile(models.Model):
    full_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(max_length=250, null=True, blank=True)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='userprofile'
    )
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[phone_validator],
    )
    address1 = models.CharField(max_length=80, null=True, blank=True)
    address2 = models.CharField(max_length=80, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    county = models.CharField(max_length=80, null=True, blank=True)
    postcode = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[uk_postcode_validator],
    )
    country = CountryField(blank_label='Select Country', null=True, blank=True)

    def __str__(self):
        return f'Profile for {self.user.username}'
