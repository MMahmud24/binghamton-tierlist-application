document.addEventListener('DOMContentLoaded', () => {
  const dropzones = document.querySelectorAll('.dropzone');
  const pool = document.getElementById('item_pool');

  // ── Populate board ───────────────────────────────────────────────
  if (window.EDIT_MODE && window.EDIT_TIERS) {
    loadEditData(window.EDIT_TIERS);
  } else if (window.TEMPLATE_MODE && window.TEMPLATE_TIERS) {
    loadEditData(window.TEMPLATE_TIERS);
  }

  // Make any pre-existing static items (create mode) draggable
  document.querySelectorAll('.draggable_item').forEach(makeDraggable);

  // ── Add Custom Item form ─────────────────────────────────────────
  const addItemForm = document.getElementById('add_item');
  let nextItemId = Date.now(); // unique across page loads

  if (addItemForm) {
    addItemForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const nameInput  = document.getElementById('item-name');
      const imageInput = document.getElementById('item-image');
      const name = nameInput.value.trim();
      if (!name) return;

      const file = imageInput.files[0];

      const buildItem = (imageDataUrl) => {
        const el = document.createElement('div');
        el.className   = 'draggable_item';
        el.id          = `custom_${nextItemId++}`;
        el.draggable   = true;
        el.dataset.name = name;

        if (imageDataUrl) {
          el.dataset.image = imageDataUrl;
          const img = document.createElement('img');
          img.src = imageDataUrl;
          img.alt = name;
          el.appendChild(img);
        } else {
          el.textContent = name;
        }

        makeDraggable(el);
        pool.appendChild(el);
        addItemForm.reset();
      };

      if (file) {
        const reader = new FileReader();
        reader.onload = () => buildItem(reader.result);
        reader.readAsDataURL(file);
      } else {
        buildItem(null);
      }
    });
  }

  // ── Drop targets ─────────────────────────────────────────────────
  dropzones.forEach(makeDropTarget);
  if (pool) makeDropTarget(pool);

  // ── Save Modal ───────────────────────────────────────────────────
  const modal            = document.getElementById('saveModal');
  const modalClose       = document.getElementById('modalClose');
  const modalCancel      = document.getElementById('modalCancel');
  const modalSave        = document.getElementById('modalSave');
  const tlTitle          = document.getElementById('tl-title');
  const titleError       = document.getElementById('titleError');
  const coverInput       = document.getElementById('coverImageInput');
  const coverPreview     = document.getElementById('coverPreview');
  const coverPlaceholder = document.getElementById('coverPlaceholder');
  const removeCover      = document.getElementById('removeCover');

  // Track the current cover — starts as the existing one in edit mode
  let coverImageDataUrl = null;
  if (window.EDIT_MODE && window.EDIT_COVER) {
    coverImageDataUrl = window.EDIT_COVER;
  } else if (window.TEMPLATE_MODE && window.TEMPLATE_COVER) {
    coverImageDataUrl = window.TEMPLATE_COVER;
  }

  function openModal() {
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    titleError.style.display = 'none';

    // Pre-fill fields
    const defaultName = window.EDIT_MODE
      ? (window.EDIT_TITLE || '')
      : (window.TEMPLATE_MODE ? (window.TEMPLATE_TITLE || '') : '');
    tlTitle.value = defaultName;

    if (coverImageDataUrl) {
      coverPreview.src = coverImageDataUrl;
      coverPreview.style.display = 'block';
      coverPlaceholder.style.display = 'none';
      removeCover.style.display = 'inline-block';
    } else {
      coverPreview.style.display = 'none';
      coverPlaceholder.style.display = 'flex';
      removeCover.style.display = 'none';
    }

    tlTitle.focus();
  }

  function closeModal() {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
  }

  document.getElementById('saveBtn').addEventListener('click', openModal);
  modalClose.addEventListener('click', closeModal);
  modalCancel.addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

  coverInput.addEventListener('change', () => {
    const file = coverInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      coverImageDataUrl = reader.result;
      coverPreview.src  = coverImageDataUrl;
      coverPreview.style.display    = 'block';
      coverPlaceholder.style.display = 'none';
      removeCover.style.display     = 'inline-block';
    };
    reader.readAsDataURL(file);
  });

  removeCover.addEventListener('click', () => {
    coverImageDataUrl = null;
    coverInput.value  = '';
    coverPreview.style.display    = 'none';
    coverPlaceholder.style.display = 'flex';
    removeCover.style.display     = 'none';
  });

  modalSave.addEventListener('click', () => {
    const name = tlTitle.value.trim();
    if (!name) {
      titleError.style.display = 'block';
      tlTitle.focus();
      return;
    }
    titleError.style.display = 'none';
    closeModal();

    if (window.EDIT_MODE) {
      updateTierList(window.EDIT_ID, name, coverImageDataUrl);
    } else {
      saveTierList(name, coverImageDataUrl);
    }
  });

  tlTitle.addEventListener('input', () => {
    if (tlTitle.value.trim()) titleError.style.display = 'none';
  });
});

// ── Helpers ──────────────────────────────────────────────────────────

function makeDraggable(el) {
  el.draggable = true;
  el.addEventListener('dragstart', (e) => {
    e.dataTransfer.setData('text/plain', el.id);
    el.classList.add('dragging');
  });
  el.addEventListener('dragend', () => el.classList.remove('dragging'));
}

function makeDropTarget(zone) {
  zone.addEventListener('dragover',  (e) => e.preventDefault());
  zone.addEventListener('dragenter', () => zone.classList.add('over'));
  zone.addEventListener('dragleave', () => zone.classList.remove('over'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('over');
    const id = e.dataTransfer.getData('text/plain');
    const el = document.getElementById(id);
    if (el) zone.appendChild(el);
  });
}

function getTierState() {
  const tiers = ['S','A','B','C','D','F'];
  const state = {};
  tiers.forEach(t => {
    const zone = document.getElementById(`dropzone_${t}`);
    state[t] = Array.from(zone.children).map(el => el.id);
  });
  const pool = document.getElementById('item_pool');
  state.POOL = Array.from(pool.children).map(el => el.id);
  return state;
}

function getItemName(el) {
  if (!el) return '';
  if (el.dataset && el.dataset.name) return el.dataset.name;
  if (el.title) return el.title;
  const text = (el.textContent || '').trim();
  return text || el.id || '';
}

function getItemImage(el) {
  if (!el) return null;
  if (el.dataset && el.dataset.image) return el.dataset.image;
  const img = el.querySelector('img');
  return img ? img.src : null;
}

function convertStateIdsToNames(stateWithIds) {
  const tiers = {};
  Object.entries(stateWithIds).forEach(([tier, ids]) => {
    tiers[tier] = ids.map(id => {
      const el = document.getElementById(id);
      return {
        name:  getItemName(el) || id,
        image: getItemImage(el)
      };
    });
  });
  return tiers;
}

function saveTierList(name, coverImage) {
  const stateNames = convertStateIdsToNames(getTierState());
  fetch('/save', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: name, tiers: stateNames, cover_image: coverImage || null })
  })
  .then(r => r.json())
  .then(data => { window.location.href = `/view/${data.id}`; })
  .catch(err => { console.error(err); alert('Failed to save tier list'); });
}

function updateTierList(id, name, coverImage) {
  const stateNames = convertStateIdsToNames(getTierState());
  fetch(`/update/${id}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: name, tiers: stateNames, cover_image: coverImage !== undefined ? coverImage : null })
  })
  .then(r => r.json())
  .then(data => { window.location.href = `/view/${data.id}`; })
  .catch(err => { console.error(err); alert('Failed to update tier list'); });
}

function loadEditData(tiersData) {
  const tierKeys = ['S','A','B','C','D','F','POOL'];
  let counter = Date.now();

  tierKeys.forEach(tier => {
    const items = tiersData[tier] || [];
    const zone  = tier === 'POOL'
      ? document.getElementById('item_pool')
      : document.getElementById(`dropzone_${tier}`);
    if (!zone) return;

    items.forEach(item => {
      if (!item || (!item.name && !item.image)) return;

      const el = document.createElement('div');
      el.className    = 'draggable_item';
      el.id           = `edit_${counter++}`;
      el.dataset.name = item.name || '';

      if (item.image) {
        el.dataset.image = item.image;
        const img = document.createElement('img');
        img.src = item.image;
        img.alt = item.name || '';
        el.appendChild(img);
      } else {
        el.textContent = item.name || '';
      }

      makeDraggable(el);
      zone.appendChild(el);
    });
  });
}
