import { LoginResponse, ApiError } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export class ApiService {
  static async login(password: string): Promise<LoginResponse> {
    try {
      const formData = new FormData();
      formData.append('password', password);

      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        body: formData,  // Pas de Content-Type, FormData le gère automatiquement
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