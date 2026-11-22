const note = document.querySelector('#note');
const status = document.querySelector('#status');
const key = 'html_tooldesk_sample_note_v1';
note.value = localStorage.getItem(key) || '';
document.querySelector('#save').addEventListener('click', () => {
  localStorage.setItem(key, note.value);
  status.textContent = 'یادداشت ذخیره شد؛ برنامه را ببندید و دوباره باز کنید.';
});
