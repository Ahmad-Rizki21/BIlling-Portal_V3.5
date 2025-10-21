/**
 * Utility functions for token encryption/decryption
 * This enhances security by storing tokens in encrypted format in localStorage
 */

// Simple XOR-based encryption for client-side (not for highly sensitive data)
// For production, consider using Web Crypto API for stronger encryption
const ENCRYPTION_KEY = 'ArtacomFTTH_2025_Secure_Key_Hashing';

/**
 * Encrypts a string using XOR cipher
 * @param text - Plain text to encrypt
 * @returns Encrypted string (base64 encoded)
 */
export function encrypt(text: string): string {
  if (!text) return '';

  try {
    let encrypted = '';
    for (let i = 0; i < text.length; i++) {
      encrypted += String.fromCharCode(
        text.charCodeAt(i) ^ ENCRYPTION_KEY.charCodeAt(i % ENCRYPTION_KEY.length)
      );
    }
    return btoa(encrypted); // base64 encode
  } catch (error) {
    console.error('Encryption failed:', error);
    return text; // fallback to plain text
  }
}

/**
 * Decrypts a string using XOR cipher
 * @param encryptedText - Encrypted string (base64 encoded)
 * @returns Decrypted plain text
 */
export function decrypt(encryptedText: string): string {
  if (!encryptedText) return '';

  try {
    // Check if this is a JWT token (starts with eyJ) - return as-is
    if (encryptedText.startsWith('eyJ')) {
      return encryptedText;
    }

    // Check if this might be a Fernet encrypted token (starts with gAAAAA)
    if (encryptedText.startsWith('gAAAAA')) {
      console.warn('Fernet encryption detected in frontend - this should be handled by backend');
      return encryptedText; // Cannot decrypt Fernet in frontend
    }

    // Try to detect if the string is valid base64 before decoding
    if (!isValidBase64(encryptedText)) {
      // Not base64, might be plain text or already decrypted
      return encryptedText;
    }

    const decoded = atob(encryptedText); // base64 decode
    let decrypted = '';
    for (let i = 0; i < decoded.length; i++) {
      decrypted += String.fromCharCode(
        decoded.charCodeAt(i) ^ ENCRYPTION_KEY.charCodeAt(i % ENCRYPTION_KEY.length)
      );
    }
    return decrypted;
  } catch (error) {
    console.error('Decryption failed:', error);
    return encryptedText; // fallback to original text (might be plain)
  }
}

/**
 * Validates if a string is valid base64
 * @param str - String to validate
 * @returns True if valid base64
 */
function isValidBase64(str: string): boolean {
  try {
    // Basic base64 validation - check if it contains only valid base64 characters
    // and length is divisible by 4 (with proper padding)
    const base64Regex = /^[A-Za-z0-9+/]*={0,2}$/;
    if (!base64Regex.test(str) || str.length % 4 !== 0) {
      return false;
    }

    // Try to decode to see if it's actually valid base64
    atob(str);
    return true;
  } catch (error) {
    return false;
  }
}

/**
 * Encrypts and stores a token in localStorage
 * @param key - Storage key
 * @param token - Token to encrypt and store
 */
export function setEncryptedToken(key: string, token: string): void {
  if (!token) {
    localStorage.removeItem(key);
    return;
  }

  try {
    const encrypted = encrypt(token);
    localStorage.setItem(key, encrypted);
  } catch (error) {
    console.error('Failed to encrypt and store token:', error);
    // Fallback to plain storage if encryption fails
    localStorage.setItem(key, token);
  }
}

/**
 * Retrieves and decrypts a token from localStorage
 * @param key - Storage key
 * @returns Decrypted token or null
 */
export function getEncryptedToken(key: string): string | null {
  try {
    const encrypted = localStorage.getItem(key);
    if (!encrypted) return null;

    // Check if it's already a valid JWT token
    if (encrypted.startsWith('eyJ')) {
      return encrypted;
    }

    // Check if it's a Fernet encrypted token (should not happen in frontend)
    if (encrypted.startsWith('gAAAAA')) {
      console.warn('Fernet encrypted token found in localStorage - this should not happen');
      return null; // Cannot handle Fernet in frontend
    }

    // Try to decrypt if it looks like XOR encrypted data
    if (isValidBase64(encrypted)) {
      try {
        const decrypted = decrypt(encrypted);

        // Validate if it's a valid JWT (starts with eyJ)
        if (decrypted.startsWith('eyJ')) {
          return decrypted;
        }

        // If decryption didn't result in valid JWT, return original
        return encrypted;
      } catch (decryptError) {
        console.warn('Failed to decrypt token, treating as plain:', decryptError);
        return encrypted;
      }
    }

    // If not base64 and not JWT, treat as plain token
    return encrypted;
  } catch (error) {
    console.error('Failed to retrieve and decrypt token:', error);
    return localStorage.getItem(key); // fallback
  }
}

/**
 * Removes encrypted token from localStorage
 * @param key - Storage key
 */
export function removeEncryptedToken(key: string): void {
  localStorage.removeItem(key);
}