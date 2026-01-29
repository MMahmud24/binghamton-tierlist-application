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

      const newItem = document.createElement("div");
      newItem.className = "draggable_item";
      newItem.id = `item_${nextItemId}`;
      newItem.draggable = true;
      newItem.title = name;
      const file = imageInput.files[0];
      if (file) {
        const img = document.createElement("img");
        img.src = URL.createObjectURL(file);
        img.alt = name;
        newItem.appendChild(img);
        }
        else { 
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
function saveTierList(name) {
  const state = getTierState();

  fetch("/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: name,
      tiers: state
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