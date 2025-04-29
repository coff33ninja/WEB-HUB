// Encryption helpers for credentials management using AES-256-GCM
import { randomBytes, createCipheriv, createDecipheriv } from 'crypto';
import { existsSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

const KEY_FILE = join(process.cwd(), 'credentials.key');
const ALGO = 'aes-256-gcm';
const IV_LENGTH = 12; // Recommended for GCM
const KEY_LENGTH = 32; // 256 bits

function loadKey(): Buffer {
  if (existsSync(KEY_FILE)) {
    return readFileSync(KEY_FILE);
  } else {
    const key = randomBytes(KEY_LENGTH);
    writeFileSync(KEY_FILE, key);
    return key;
  }
}

const key = loadKey();

export function encryptField(value: string): string {
  if (!value) return '';
  const iv = randomBytes(IV_LENGTH);
  const cipher = createCipheriv(ALGO, key, iv);
  const encrypted = Buffer.concat([cipher.update(value, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  // Store as base64: iv:tag:encrypted
  return [iv.toString('base64'), tag.toString('base64'), encrypted.toString('base64')].join(':');
}

export function decryptField(data: string): string {
  if (!data) return '';
  try {
    const [ivB64, tagB64, encB64] = data.split(':');
    const iv = Buffer.from(ivB64, 'base64');
    const tag = Buffer.from(tagB64, 'base64');
    const encrypted = Buffer.from(encB64, 'base64');
    const decipher = createDecipheriv(ALGO, key, iv);
    decipher.setAuthTag(tag);
    const decrypted = Buffer.concat([decipher.update(encrypted), decipher.final()]);
    return decrypted.toString('utf8');
  } catch {
    return '';
  }
}
