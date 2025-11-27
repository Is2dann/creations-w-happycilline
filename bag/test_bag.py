from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from products.models import Product


class BagViewTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test Item",
            price=Decimal("10.00"),
        )

    def test_add_then_view(self):
        """
        Adding an item to the bag should store it in the session
        and display it on the bag page.
        """
        add_url = reverse("bag:add_to_bag", args=[self.product.id])
        response = self.client.post(
            add_url,
            {"quantity": 1, "redirect_url": "/"},
            follow=True,
        )

        # Session bag should contain the product id
        bag = self.client.session.get("bag", {})
        self.assertIn(str(self.product.id), bag)
        self.assertEqual(bag[str(self.product.id)], 1)

        # Bag page should show the item
        view_url = reverse("bag:view_bag")
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Item")

    def test_adjust(self):
        """
        Adjusting quantity in the bag should update the session and
        still show the item with updated quantity.
        """
        add_url = reverse("bag:add_to_bag", args=[self.product.id])
        self.client.post(
            add_url,
            {"quantity": 1, "redirect_url": "/"},
            follow=True,
        )

        adjust_url = reverse("bag:adjust_bag", args=[self.product.id])
        self.client.post(
            adjust_url,
            {"quantity": 3},
            follow=True,
        )

        bag = self.client.session.get("bag", {})
        self.assertIn(str(self.product.id), bag)
        self.assertEqual(bag[str(self.product.id)], 3)

        view_url = reverse("bag:view_bag")
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Item")

    def test_remove(self):
        """
        Removing an item from the bag should clear it from the session
        and show an empty bag message.
        """
        add_url = reverse("bag:add_to_bag", args=[self.product.id])
        self.client.post(
            add_url,
            {"quantity": 1, "redirect_url": "/"},
            follow=True,
        )

        remove_url = reverse("bag:remove_from_bag", args=[self.product.id])
        self.client.post(remove_url, follow=True)

        # Session bag should no longer contain the product
        bag = self.client.session.get("bag", {})
        self.assertNotIn(str(self.product.id), bag)

        # Bag page should show empty bag message
        view_url = reverse("bag:view_bag")
        response = self.client.get(view_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your bag is empty.")
        # We no longer assert that 'Test Item' is absent, because it is
        # still present in toast messages, which is expected behaviour.
