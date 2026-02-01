interface Person {
  id?: string
  first_name?: string
  last_name?: string
  email?: string
  currentClass?: string
}

document.addEventListener('DOMContentLoaded', () => {
  const raw = sessionStorage.getItem('user')
  if (!raw) {
    window.location.href = './index.html'
    return
  }

  let user: Person
  try {
    user = JSON.parse(raw) as Person
  } catch {
    sessionStorage.removeItem('user')
    window.location.href = './index.html'
    return
  }

  const setText = (id: string, value?: string) => {
    const el = document.getElementById(id)
    if (el) el.textContent = value ?? ''
  }

  setText('info-id', user.id)
  setText('info-first', user.first_name)
  setText('info-last', user.last_name)
  setText('info-email', user.email)
  setText('info-class', user.currentClass)

  const heading = document.getElementById('heading')
  if (heading) {
    const name = [user.first_name, user.last_name].filter(Boolean).join(' ')
    heading.textContent = name ? `Welcome, ${name}` : 'Your profile'
  }

  const logoutBtn = document.getElementById('logout')
  if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
      sessionStorage.removeItem('user')
      window.location.href = './index.html'
    })
  }
})