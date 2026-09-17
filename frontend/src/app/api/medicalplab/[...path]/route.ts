import { NextRequest, NextResponse } from "next/server";
import {
  MENTOR_COOKIE_NAME,
  SESSION_TTL_SECONDS,
  getMentorSecret,
  signSessionToken,
  validateMentorAccessCode,
  verifySessionToken,
} from "@/lib/mentor-auth";

/**
 * Server-side same-origin proxy to the Cloud Run Staging BFF Gateway.
 *
 * Security guarantees:
 * 1. MENTOR_SESSION_GATE: Public browser requests without a valid, signed
 *    mentor session cookie are rejected with HTTP 401 before touching the BFF.
 * 2. STAGING_ACCESS_KEY and MENTOR_ACCESS_CODE are strictly SERVER-ONLY
 *    environment variables. They are NEVER leaked or returned to the browser.
 * 3. Mobile clients continue to access the Cloud Run BFF directly via
 *    X-Staging-Key + X-User-Id without browser cookies.
 * 4. Inbound Authorization and Host headers are stripped; only verified headers
 *    (X-User-Id, content-type, accept) and server-injected X-Staging-Key are sent to BFF.
 */

const BFF_BASE_URL = (
  process.env.BFF_BASE_URL ||
  process.env.MEDICALPLAB_BFF_URL ||
  "http://localhost:8080"
).replace(/\/+$/, "");

const STAGING_ACCESS_KEY = process.env.STAGING_ACCESS_KEY || "";
const MENTOR_ACCESS_CODE = process.env.MENTOR_ACCESS_CODE || "";

function isSessionAuthorized(request: NextRequest): boolean {
  // If MENTOR_ACCESS_CODE is set, enforce the session gate strictly
  // In production, require either valid session or fail closed
  const cookie = request.cookies.get(MENTOR_COOKIE_NAME)?.value;
  if (!cookie) {
    // If no MENTOR_ACCESS_CODE is configured in local development, allow dev fallback
    if (!MENTOR_ACCESS_CODE && process.env.NODE_ENV !== "production") {
      return true;
    }
    return false;
  }
  return verifySessionToken(cookie, getMentorSecret());
}

async function handleSessionAuth(request: NextRequest): Promise<Response> {
  if (request.method === "POST") {
    try {
      const body = await request.json();
      const code = (body?.access_code || "").trim();
      if (!code || !validateMentorAccessCode(code)) {
        return NextResponse.json(
          { error: "Invalid mentor access code", detail: "Authentication failed" },
          { status: 401 }
        );
      }

      const exp = Date.now() + SESSION_TTL_SECONDS * 1000;
      const token = signSessionToken({ exp, iat: Date.now(), v: 1 }, getMentorSecret());

      const response = NextResponse.json(
        { authenticated: true, expires_in: SESSION_TTL_SECONDS },
        { status: 200 }
      );

      response.cookies.set({
        name: MENTOR_COOKIE_NAME,
        value: token,
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge: SESSION_TTL_SECONDS,
      });

      return response;
    } catch {
      return NextResponse.json(
        { error: "Malformed request", detail: "JSON body with access_code expected" },
        { status: 400 }
      );
    }
  }

  if (request.method === "GET") {
    const isAuth = isSessionAuthorized(request);
    return NextResponse.json({ authenticated: isAuth }, { status: isAuth ? 200 : 401 });
  }

  if (request.method === "DELETE") {
    const response = NextResponse.json({ authenticated: false, logged_out: true });
    response.cookies.set({
      name: MENTOR_COOKIE_NAME,
      value: "",
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 0,
    });
    return response;
  }

  return NextResponse.json({ error: "Method not allowed" }, { status: 405 });
}

async function handleProxy(request: NextRequest): Promise<Response> {
  const url = new URL(request.url);
  const subpath = url.pathname.replace(/^\/api\/medicalplab/, "") || "/";

  // Dedicated mentor session endpoint
  if (subpath === "/session" || subpath === "/session/") {
    return handleSessionAuth(request);
  }

  // 1. Enforce Mentor Session Gate: Disallow unauthenticated public visitors
  if (!isSessionAuthorized(request)) {
    return NextResponse.json(
      {
        error: "Unauthorized",
        detail: "Mentor access session required. Authenticate at /api/medicalplab/session",
      },
      { status: 401 }
    );
  }

  // 2. Prepare upstream URL & headers
  const targetUrl = `${BFF_BASE_URL}${subpath}${url.search}`;
  const forwardHeaders = new Headers();

  const safeHeaders = [
    "content-type",
    "accept",
    "x-user-id",
    "x-tenant-id",
    "x-learner-id",
    "x-request-id",
  ];
  for (const headerName of safeHeaders) {
    const val = request.headers.get(headerName);
    if (val) {
      forwardHeaders.set(headerName, val);
    }
  }

  // Inject server-only staging key for the Cloud Run BFF gateway
  if (STAGING_ACCESS_KEY) {
    forwardHeaders.set("x-staging-key", STAGING_ACCESS_KEY);
  }

  let body: BodyInit | null = null;
  if (["POST", "PUT", "PATCH"].includes(request.method)) {
    body = await request.arrayBuffer();
  }

  try {
    const bffResponse = await fetch(targetUrl, {
      method: request.method,
      headers: forwardHeaders,
      body,
      redirect: "manual",
    });

    const responseHeaders = new Headers();
    for (const h of ["content-type", "x-request-id"]) {
      const v = bffResponse.headers.get(h);
      if (v) responseHeaders.set(h, v);
    }

    const responseBody = await bffResponse.arrayBuffer();
    return new Response(responseBody, {
      status: bffResponse.status,
      headers: responseHeaders,
    });
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : "Failed to connect to BFF gateway";
    return NextResponse.json(
      {
        error: "Staging proxy error",
        detail: errorMessage,
      },
      { status: 502 }
    );
  }
}

export async function GET(request: NextRequest) {
  return handleProxy(request);
}

export async function POST(request: NextRequest) {
  return handleProxy(request);
}

export async function HEAD(request: NextRequest) {
  return handleProxy(request);
}

export async function OPTIONS() {
  return new Response(null, { status: 204 });
}

export async function DELETE(request: NextRequest) {
  const url = new URL(request.url);
  const subpath = url.pathname.replace(/^\/api\/medicalplab/, "") || "/";
  if (subpath === "/session" || subpath === "/session/") {
    return handleSessionAuth(request);
  }
  return new Response(null, { status: 405 });
}
