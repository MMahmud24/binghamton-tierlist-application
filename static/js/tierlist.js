document.addEventListener('DOMContentLoaded', () => {
  const items = document.querySelectorAll('.draggable_item');
  const dropzones = document.querySelectorAll('.dropzone');
  const pool = document.getElementById('item_pool');

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
