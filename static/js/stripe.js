(function(){
  const form = document.getElementById('checkoutForm');
  if (!form) return;

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');

  const payBtn = document.getElementById('payButton');
  const clientSecret = payBtn?.dataset.clientSecret;
  const stripe = Stripe(window.STRIPE_PUBLIC_KEY || document.querySelector('meta[name="stripe-pk"]')?.content || '');

  // Initialize Elements
  const elements = stripe.elements({ clientSecret });
  const paymentElement = elements.create('payment');
  paymentElement.mount('#payment-element');

  function setLoading(isLoading){
    payBtn.disabled = isLoading;
    payBtn.textContent = isLoading ? 'Processing…' : payBtn.textContent.replace('Processing…','Pay');
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    setLoading(true);
    document.getElementById('cardErrors').style.display = 'none';

    // Build form data for caching
    const data = new FormData(form);

    // Cache checkout data on server (session)
    await fetch('/checkout/cache/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      body: data
    });

    // Confirm Payment with Stripe and redirect back to /checkout/paid/
    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/checkout/paid/`,
      },
    });

    if (error) {
      const el = document.getElementById('cardErrors');
      el.textContent = error.message || 'Payment failed. Please check your details and try again.';
      el.style.display = 'block';
      setLoading(false);
    }
  });
})();