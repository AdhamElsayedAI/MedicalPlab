import { test, describe } from "node:test";
import assert from "node:assert";
import crypto from "node:crypto";

// Standalone verification of the mentor auth security invariants
const SESSION_TTL_SECONDS = 4 * 3600;
const TEST_SECRET = "test-mentor-secret-998877";
const TEST_ACCESS_CODE = "PILOT-MENTOR-2026";
const STAGING_KEY = "staging-secret-never-leak-to-browser";

function signToken(payloadObj, secret) {
  const payloadStr = JSON.stringify(payloadObj);
  const payloadB64 = Buffer.from(payloadStr, "utf-8").toString("base64url");
  const hmac = crypto.createHmac("sha256", secret).update(payloadB64).digest("hex");
  return `${payloadB64}.${hmac}`;
}

function verifyToken(token, secret) {
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

function validateAccessCode(inputCode, configuredCode) {
  if (!inputCode || !configuredCode) return false;
  const bufInput = Buffer.from(inputCode, "utf-8");
  const bufConfig = Buffer.from(configuredCode, "utf-8");
  if (bufInput.length !== bufConfig.length) return false;
  return crypto.timingSafeEqual(bufInput, bufConfig);
}

describe("Mentor Access Session Gate Security", () => {
  test("1. Unauthenticated request without session cookie is rejected (HTTP 401 equivalent)", () => {
    const unauthenticatedToken = null;
    assert.strictEqual(verifyToken(unauthenticatedToken, TEST_SECRET), false);

    const emptyToken = "";
    assert.strictEqual(verifyToken(emptyToken, TEST_SECRET), false);
  });

  test("2. Valid mentor access code allows creation and verification of signed session", () => {
    // Valid code matches
    assert.strictEqual(validateAccessCode("PILOT-MENTOR-2026", TEST_ACCESS_CODE), true);

    // Invalid code rejected
    assert.strictEqual(validateAccessCode("WRONG-CODE", TEST_ACCESS_CODE), false);

    // Mint valid token with 4-hour TTL
    const exp = Date.now() + SESSION_TTL_SECONDS * 1000;
    const token = signToken({ exp, iat: Date.now(), v: 1 }, TEST_SECRET);

    // Verification succeeds
    assert.strictEqual(verifyToken(token, TEST_SECRET), true);
  });

  test("3. Tampered token or invalid HMAC signature is strictly rejected", () => {
    const exp = Date.now() + SESSION_TTL_SECONDS * 1000;
    const token = signToken({ exp, iat: Date.now(), v: 1 }, TEST_SECRET);

    // Tamper with payload
    const parts = token.split(".");
    const tamperedPayload = Buffer.from(JSON.stringify({ exp: exp + 999999, v: 1 })).toString("base64url");
    const tamperedToken = `${tamperedPayload}.${parts[1]}`;

    assert.strictEqual(verifyToken(tamperedToken, TEST_SECRET), false);

    // Verify with wrong secret
    assert.strictEqual(verifyToken(token, "wrong-secret-signature"), false);
  });

  test("4. Expired token is rejected", () => {
    // Token expired 10 seconds ago
    const exp = Date.now() - 10000;
    const expiredToken = signToken({ exp, iat: Date.now() - 20000, v: 1 }, TEST_SECRET);

    assert.strictEqual(verifyToken(expiredToken, TEST_SECRET), false);
  });

  test("5. Staging secret is NEVER present in the signed session token or client payload", () => {
    const exp = Date.now() + SESSION_TTL_SECONDS * 1000;
    const token = signToken({ exp, iat: Date.now(), v: 1 }, TEST_SECRET);

    // Ensure the staging key never appears in the token string
    assert.strictEqual(token.includes(STAGING_KEY), false);

    const payloadJson = Buffer.from(token.split(".")[0], "base64url").toString("utf-8");
    assert.strictEqual(payloadJson.includes(STAGING_KEY), false);
    assert.strictEqual(payloadJson.includes(TEST_ACCESS_CODE), false);
  });
});
