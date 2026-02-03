/**
 * Interface représentant un utilisateur
 */
export interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  currentClass: string;
}

/**
 * Payload pour la requête de login
 */
export interface LoginPayload {
  password: string;
}

/**
 * Réponse de login du serveur
 */
export interface LoginResponse extends User {}

/**
 * Erreur API
 */
export interface ApiError {
  status: number;
  message: string;
}