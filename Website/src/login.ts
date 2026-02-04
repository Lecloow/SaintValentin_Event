import { ApiService } from './api';
import { StorageService } from './storage';
import { LoginPayload } from './types';

export class LoginPage {
  private form: HTMLFormElement | null = null;
  private passwordInput: HTMLInputElement | null = null;
  private resultEl: HTMLElement | null = null;
  private submitBtn: HTMLButtonElement | null = null;

  constructor() {
    this.init();
  }

  /**
   * Initialise la page
   */
  private init(): void {
    this.cacheElements();
    this.attachEventListeners();
  }

  /**
   * Met en cache les éléments du DOM
   */
  private cacheElements(): void {
    this.form = document.getElementById('loginForm') as HTMLFormElement | null;
    this.passwordInput = document.getElementById('password') as HTMLInputElement | null;
    this.resultEl = document.getElementById('result') as HTMLElement | null;
    this.submitBtn = document.getElementById('submitBtn') as HTMLButtonElement | null;

    if (!this.form || !this.passwordInput || !this.resultEl) {
      console.error('Elements manquants dans le DOM');
    }
  }

  /**
   * Attache les event listeners
   */
  private attachEventListeners(): void {
    this.form?.addEventListener('submit', (e) => this.handleSubmit(e));
    this.passwordInput?.addEventListener('input', () => this.clearError());
  }

  /**
   * Gère la soumission du formulaire
   */
  private async handleSubmit(event: Event): Promise<void> {
    event.preventDefault();

    const password = this.passwordInput?.value.trim();

    if (!password) {
      this.showError('Veuillez entrer un code.');
      return;
    }

    await this.submitLogin(password);
  }

  /**
   * Soumet la requête de login
   */
  private async submitLogin(password: string): Promise<void> {
    try {
      this.setLoading(true);
      this.clearError();

      const payload: LoginPayload = { password };
      const user = await ApiService.login(payload);

      // Sauvegarde l'utilisateur
      StorageService.setUser(user);

      this.showSuccess('Connexion réussie! Redirection...');

      window.location.href = './website/profile.html';
    } catch (error: any) {
      const message =
        error.message || 'Erreur lors de la connexion';
      this.showError(message);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Affiche un message d'erreur
   */
  private showError(message: string): void {
    if (!this.resultEl) return;
    this.resultEl.textContent = message;
    this.resultEl.className = 'result error';
  }

  /**
   * Affiche un message de succès
   */
  private showSuccess(message: string): void {
    if (!this.resultEl) return;
    this.resultEl.textContent = message;
    this.resultEl.className = 'result success';
  }

  /**
   * Affiche l'état de chargement
   */
  private setLoading(isLoading: boolean): void {
    if (!this.submitBtn || !this.resultEl) return;

    this.submitBtn.disabled = isLoading;

    if (isLoading) {
      this.resultEl.innerHTML = '<span class="spinner"></span>Connexion en cours...';
      this.resultEl.className = 'result loading';
    } else {
      this.resultEl.innerHTML = '';
      this.resultEl.className = 'result';
    }
  }

  /**
   * Efface les messages d'erreur
   */
  private clearError(): void {
    if (!this.resultEl) return;
    this.resultEl.innerHTML = '';
    this.resultEl.className = 'result';
  }
}

// Initialise la page quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
  new LoginPage();
});