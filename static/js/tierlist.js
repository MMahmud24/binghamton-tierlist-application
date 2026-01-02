document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll('.draggable_item');
  const dropzones = document.querySelectorAll('.dropzone');
  const pool = document.getElementById('item_pool');

  loadTierList();

  document
    .getElementById("saveBtn")
    .addEventListener("click", saveTierList);

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
function saveTierList() {
  const state = getTierState();
  localStorage.setItem("tierlist", JSON.stringify(state));
  alert("Tier list saved!");
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
