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

export interface LoginResponse extends User {}

export interface ApiError {
  status: number;
  message: string;
}