document.addEventListener('DOMContentLoaded', function () {
  const form = document.getElementById('loginForm');
  const resultEl = document.getElementById('result');

  if (!form || !resultEl) return;

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const input = document.getElementById('password');
    if (!input) return;

    const password = input.value.trim();
    if (!password) {
      resultEl.textContent = 'Please enter a code.';
      return;
    }

    try {
      const res = await fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });

      if (!res.ok) {
        const text = await res.text();
        resultEl.textContent = `Error: ${res.status} ${text}`;
        return;
      }

      const data = await res.json();
      sessionStorage.setItem('user', JSON.stringify(data));
      window.location.href = './profile.html';
    } catch (err) {
      resultEl.textContent = 'Network error: ' + (err && err.message ? err.message : err);
    }
  });
});