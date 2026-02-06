import { StorageService } from './storage';

export class ProfilePage {
  private contentEl: HTMLElement | null = null;

  constructor() {
    this.init();
  }

  private init(): void {
    this.contentEl = document.getElementById('content');
    this.render();
  }

  private render(): void {
    if (!this.contentEl) return;

    const user = StorageService.getUser();

    if (!user) {
      this.renderNotConnected();
      return;
    }

    this.renderProfile(user);
  }

  private renderNotConnected(): void {
    if (!this.contentEl) return;

    this.contentEl.innerHTML = `
      <div class="error">Vous n'êtes pas connecté. Redirection...</div>
    `;

    setTimeout(() => {
      window.location.href = './index.html';
    }, 2000);
  }

  private renderProfile(user: any): void {
    if (!this.contentEl) return;

    this.contentEl.innerHTML = `
      <div class="greeting">Bonjour ${user.first_name}! 👋</div>
      
      <div class="user-info">
        <div class="info-row">
          <div class="label">Prénom</div>
          <div class="value">${user.first_name}</div>
        </div>
        <div class="info-row">
          <div class="label">Nom</div>
          <div class="value">${user.last_name}</div>
        </div>
        <div class="info-row">
          <div class="label">Email</div>
          <div class="value">${user.email}</div>
        </div>
        <div class="info-row">
          <div class="label">Classe</div>
          <div class="value">${user.currentClass}</div>
        </div>
      </div>

      <button class="logout-btn" onclick="goToQuestionnaire()" style="margin-bottom: 1rem; background: linear-gradient(135deg, #e91e63 0%, #f06292 100%);">
        📝 Répondre au questionnaire
      </button>

      <button class="logout-btn" onclick="logout()">Se déconnecter</button>
    `;
  }
}

// Fonction globale pour le logout
(window as any).logout = function() {
  StorageService.clearUser();
  window.location.href = './index.html';
};

// Fonction globale pour aller au questionnaire
(window as any).goToQuestionnaire = function() {
  window.location.href = './questionnaire.html';
};

// Initialise la page quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
  new ProfilePage();
});