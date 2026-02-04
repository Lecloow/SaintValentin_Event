import { LoginPayload, LoginResponse, ApiError } from './types';

const API_BASE_URL = 'https://saint-valentin-backend-tyqw.onrender.com';
/**
 * Service pour les appels API
 */
export class ApiService {
  /**
   * Envoie une requête de login au backend
   */
  static async login(payload: LoginPayload): Promise<LoginResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const text = await response.text();
        throw {
          status: response.status,
          message: text || `Erreur ${response.status}`,
        } as ApiError;
      }

      const data = (await response.json()) as LoginResponse;
      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw {
          status: 0,
          message: error.message,
        } as ApiError;
      }
      throw error;
    }
  }
}