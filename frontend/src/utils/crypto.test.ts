/**
 * Test file for crypto utilities
 * This file can be used to verify encryption/decryption functionality
 * Run this in browser console or during development to verify functionality
 */

import { encrypt, decrypt, setEncryptedToken, getEncryptedToken, removeEncryptedToken } from './crypto';

// Test data
const testToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';

// Run tests
export function runCryptoTests() {
  console.log('🔐 Testing Crypto Utilities...');

  // Test 1: Basic encrypt/decrypt
  const encrypted = encrypt(testToken);
  const decrypted = decrypt(encrypted);

  console.log('Original:', testToken);
  console.log('Encrypted:', encrypted);
  console.log('Decrypted:', decrypted);
  console.log('Test 1 - Basic encryption:', decrypted === testToken ? '✅ PASS' : '❌ FAIL');

  // Test 2: Token storage
  setEncryptedToken('test_token', testToken);
  const retrieved = getEncryptedToken('test_token');
  console.log('Test 2 - Storage retrieval:', retrieved === testToken ? '✅ PASS' : '❌ FAIL');

  // Test 3: Token removal
  removeEncryptedToken('test_token');
  const afterRemoval = getEncryptedToken('test_token');
  console.log('Test 3 - Token removal:', afterRemoval === null ? '✅ PASS' : '❌ FAIL');

  // Test 4: Empty token handling
  const emptyEncrypted = encrypt('');
  const emptyDecrypted = decrypt(emptyEncrypted);
  console.log('Test 4 - Empty token:', emptyDecrypted === '' ? '✅ PASS' : '❌ FAIL');

  console.log('🎉 All crypto tests completed!');
}

// Uncomment to run tests immediately
// runCryptoTests();