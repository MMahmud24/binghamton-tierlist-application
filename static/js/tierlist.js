document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll('.draggable_item');
  const dropzones = document.querySelectorAll('.dropzone');
  const pool = document.getElementById('item_pool');

  
  loadTierList();

  const addItemForm = document.getElementById("add_item");
  let nextItemId = document.querySelectorAll('.draggable_item').length + 1;

  if (addItemForm) {
    addItemForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const nameInput = document.getElementById("item-name");
      const imageInput = document.getElementById("item-image");

      const name = nameInput.value.trim();
      if (!name) return;

      const file = imageInput.files[0];
      const newItemId = `item_${nextItemId}`;

      const createItemElement = (imageDataUrl) => {
        const newItem = document.createElement("div");
        newItem.className = "draggable_item";
        newItem.id = newItemId;
        newItem.draggable = true;
        newItem.title = name;
        newItem.dataset.name = name;
        if (imageDataUrl) {
          newItem.dataset.image = imageDataUrl;
          const img = document.createElement("img");
          img.src = imageDataUrl;
          img.alt = name;
          newItem.appendChild(img);
        } else {
          newItem.textContent = name;
        }

        newItem.addEventListener('dragstart', (e) => {
          e.dataTransfer.setData('text/plain', newItem.id);
          newItem.classList.add('dragging');
        });
        newItem.addEventListener('dragend', () =>
          newItem.classList.remove('dragging'));

        pool.appendChild(newItem);
        nextItemId++;
        addItemForm.reset();
      };

      if (file) {
        const reader = new FileReader();
        reader.onload = () => createItemElement(reader.result);
        reader.readAsDataURL(file);
      } else {
        createItemElement(null);
      }
    });
  }

  document
    .getElementById("saveBtn")
    .addEventListener("click", () => {
      const name = prompt("Enter a name for your tierlist: ");
      if (!name || !name.trim()) return;

      saveTierList(name.trim());
    });
    

  items.forEach(item => {
    item.draggable = true;
    item.addEventListener('dragstart', (e) => {
      e.dataTransfer.setData('text/plain', item.id);
      item.classList.add('dragging');
    });
    item.addEventListener('dragend', () => item.classList.remove('dragging'));
  });

  function makeDropTarget(zone) {
    zone.addEventListener('dragover', e => e.preventDefault()); 
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

  dropzones.forEach(makeDropTarget);
  if (pool) makeDropTarget(pool);
});




function getTierState() {
  const tiers = ["S","A","B","C","D","F"];
  const state = {};

  tiers.forEach(t => {
    const zone = document.getElementById(`dropzone_${t}`);
    state[t] = Array.from(zone.children).map(el => el.id);
  });

  const pool = document.getElementById("item_pool");
  state.POOL = Array.from(pool.children).map(el => el.id);

  return state;
}

function getItemName(el) {
  if (!el) return "";
  // Prefer explicit data-name, then title, then text content, finally fallback to id.
  if (el.dataset && el.dataset.name) return el.dataset.name;
  if (el.title) return el.title;
  const text = (el.textContent || "").trim();
  if (text) return text;
  return el.id || "";
}

function getItemImage(el) {
  if (!el) return null;
  if (el.dataset && el.dataset.image) return el.dataset.image;
  // Fallback: if element contains an <img>, capture its src (may be object URL)
  const img = el.querySelector("img");
  return img ? img.src : null;
}

function convertStateIdsToNames(stateWithIds) {
  const tiers = {};
  Object.entries(stateWithIds).forEach(([tier, ids]) => {
    tiers[tier] = ids.map(id => {
      const el = document.getElementById(id);
      return {
        name: getItemName(el) || id,
        image: getItemImage(el)
      };
    });
  });
  return tiers;
}

function saveTierList(name) {
  const stateIds = getTierState();
  const stateNames = convertStateIdsToNames(stateIds);

  fetch("/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: name,
      tiers: stateNames
    })
  })
  .then(res => res.json())
  .then(data => {
    window.location.href = `/view/${data.id}`;
  })
  .catch(err => {
    console.error(err);
    alert("Failed to save tier list");
  });
}

function loadTierList() {
  const saved = localStorage.getItem("tierlist");
  if (!saved) return;

  const state = JSON.parse(saved);

  Object.entries(state).forEach(([tier, items]) => {
    const zone =
      tier === "POOL"
        ? document.getElementById("item_pool")
        : document.getElementById(`dropzone_${tier}`);

    items.forEach(id => {
      const el = document.getElementById(id);
      if (el) zone.appendChild(el);
    });
  });
}
