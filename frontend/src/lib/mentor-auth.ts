import crypto from "node:crypto";

/**
 * Lightweight Zero-Cost Mentor Access Session Gate.
 *
 * Provides a free, server-side authenticated session for mentors and pilot reviewers
 * to access the staging proxy without exposing STAGING_ACCESS_KEY or MENTOR_ACCESS_CODE.
 *
 * Invariants:
 * 1. MENTOR_ACCESS_CODE is server-only (never NEXT_PUBLIC_*).
 * 2. Session tokens are signed with HMAC-SHA256 and stored in an HttpOnly cookie.
 * 3. Token TTL is short (4 hours max).
 * 4. Browser requests to /api/medicalplab/* without a valid session receive HTTP 401.
 */

export const MENTOR_COOKIE_NAME = "medicalplab_mentor_session";
export const SESSION_TTL_SECONDS = 4 * 3600; // 4 hours

export function getMentorSecret(): string {
  return (
    process.env.MENTOR_ACCESS_CODE ||
    process.env.STAGING_ACCESS_KEY ||
    "development-mentor-secret-salt"
  );
}

export function signSessionToken(payloadObj: object, secret: string): string {
  const payloadStr = JSON.stringify(payloadObj);
  const payloadB64 = Buffer.from(payloadStr, "utf-8").toString("base64url");
  const hmac = crypto.createHmac("sha256", secret).update(payloadB64).digest("hex");
  return `${payloadB64}.${hmac}`;
}

export function verifySessionToken(token: string, secret: string): boolean {
  if (!token || typeof token !== "string") return false;
  const parts = token.split(".");
  if (parts.length !== 2) return false;
  const [payloadB64, providedHmac] = parts;
  if (!payloadB64 || !providedHmac) return false;

  const expectedHmac = crypto.createHmac("sha256", secret).update(payloadB64).digest("hex");
  try {
    const bufProvided = Buffer.from(providedHmac, "hex");
    const bufExpected = Buffer.from(expectedHmac, "hex");
    if (bufProvided.length !== bufExpected.length) return false;
    if (!crypto.timingSafeEqual(bufProvided, bufExpected)) return false;

    const payloadJson = Buffer.from(payloadB64, "base64url").toString("utf-8");
    const payload = JSON.parse(payloadJson);
    if (!payload.exp || typeof payload.exp !== "number") return false;
    if (Date.now() > payload.exp) return false;
    return true;
  } catch {
    return false;
  }
}

export function validateMentorAccessCode(inputCode: string): boolean {
  const configuredCode = process.env.MENTOR_ACCESS_CODE || "";
  if (!configuredCode || !inputCode) return false;

  const bufInput = Buffer.from(inputCode, "utf-8");
  const bufConfig = Buffer.from(configuredCode, "utf-8");
  if (bufInput.length !== bufConfig.length) return false;
  return crypto.timingSafeEqual(bufInput, bufConfig);
}
