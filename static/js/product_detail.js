// galleryData comes directly from context as JSON
  const galleryData = {{ gallery_js|safe }};
  
  const modalEl = document.getElementById('imageModal');
  const modalImg = document.getElementById('imageModalFull');
  const counter = document.getElementById('imageCounter');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  let currentIdx = 0;

  function showImage(idx) {
    if (!galleryData.length) return;
    if (idx < 0) idx = galleryData.length - 1;
    if (idx >= galleryData.length) idx = 0;
    currentIdx = idx;
    const item = galleryData[currentIdx];
    if (modalImg) {
      modalImg.src = item.url;
      modalImg.alt = item.alt || "";
    }
    if (counter) {
      counter.textContent = (currentIdx + 1) + " / " + galleryData.length;
    }
  }

  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('[data-bs-target="#imageModal"][data-idx]');
    if (!trigger) return;
    const idx = parseInt(trigger.getAttribute('data-idx'), 10) || 0;
    showImage(idx);
  });

  prevBtn?.addEventListener('click', () => showImage(currentIdx - 1));
  nextBtn?.addEventListener('click', () => showImage(currentIdx + 1));

  modalEl?.addEventListener('shown.bs.modal', () => {
    const onKey = (ev) => {
      if (ev.key === 'ArrowLeft') showImage(currentIdx - 1);
      if (ev.key === 'ArrowRight') showImage(currentIdx + 1);
    };
    document.addEventListener('keydown', onKey);
    modalEl.addEventListener('hidden.bs.modal', () => {
      document.removeEventListener('keydown', onKey);
      if (modalImg) {
        modalImg.removeAttribute('src');
        modalImg.removeAttribute('alt');
      }
    }, { once: true });
  });