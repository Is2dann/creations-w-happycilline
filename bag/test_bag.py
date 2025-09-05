from django.test import TestCase
from django.urls import reverse
from products.models import Product


class BagViewTests(TestCase):
    """ This testcase is from Django documentation,
        just tweaked to my purpose """
    
    """ Gets Test Item with a price of £10 """
    def setUp(self):
        self.p = Product.objects.create(name='Test Item', price=10)

    """ Adds 2 items to the bag and checks if the
        bag contains 2 item worth of £20 """
    def test_add_then_view(self):
        r = self.client.post(reverse(
            'bag:add_to_bag', args=[self.p.id]), {
                'quantity': 2, 'redirect_url': '/'})
        self.assertEqual(r.status_code, 302)
        r = self.client.get(reverse('bag:view_bag'))
        self.assertContains(r, 'Test Item')
        self.assertContains(r, '£20')

    """ Adds another item to the
        bag and checks quantity and price is now £30 """
    def test_adjust(self):
        self.client.post(reverse(
            'bag:add_to_bag', args=[self.p.id]), {
                'quantity': 1, 'redirect_url': '/'})
        r = self.client.post(reverse(
            'bag:adjust_bag', args=[self.p.id]), {'quantity': 3})
        self.assertEqual(r.status_code, 302)
        r = self.client.get(reverse('bag:view_bag'))
        self.assertContains(r, '£30')

    """ Removes the item completely from bag
        and checks if the bag now NotContain Test Item """
    def test_remove(self):
        self.client.post(reverse(
            'bag:add_to_bag', args=[self.p.id]), {
                'quantity': 1, 'redirect_url': '/'})
        r = self.client.post(reverse('bag:remove_from_bag', args=[self.p.id]))
        self.assertEqual(r.status_code, 302)
        r = self.client.get(reverse('bag:view_bag'))
        self.assertNotContains(r, 'Test Item')
