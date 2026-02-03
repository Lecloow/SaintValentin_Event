import { User } from './types';

const USER_STORAGE_KEY = 'user';

/**
 * Service pour gérer le stockage de l'utilisateur
 */
export class StorageService {
  /**
   * Sauvegarde l'utilisateur connecté
   */
  static setUser(user: User): void {
    sessionStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  }

  /**
   * Récupère l'utilisateur connecté
   */
  static getUser(): User | null {
    const raw = sessionStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return null;

    try {
      return JSON.parse(raw) as User;
    } catch {
      this.clearUser();
      return null;
    }
  }

  /**
   * Supprime l'utilisateur connecté
   */
  static clearUser(): void {
    sessionStorage.removeItem(USER_STORAGE_KEY);
  }

  /**
   * Vérifie si un utilisateur est connecté
   */
  static isLoggedIn(): boolean {
    return this.getUser() !== null;
  }
}