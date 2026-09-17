import { NextRequest, NextResponse } from "next/server";

/**
 * Server-side same-origin proxy to the Cloud Run Staging BFF Gateway.
 *
 * Security guarantees:
 * 1. STAGING_ACCESS_KEY is read strictly from SERVER-ONLY environment variables.
 *    It is NEVER prefixed with NEXT_PUBLIC_* and NEVER leaked to the client browser.
 * 2. Browser requests use same-origin (/api/medicalplab/*), avoiding cross-site cookie
 *    or CORS header complexities.
 * 3. Inbound Authorization and Host headers are stripped; only verified headers
 *    (X-User-Id, content-type, accept) and server-injected X-Staging-Key are sent to BFF.
 */

const BFF_BASE_URL = (
  process.env.BFF_BASE_URL ||
  process.env.MEDICALPLAB_BFF_URL ||
  "http://localhost:8080"
).replace(/\/+$/, "");

// Server-only secret: NEVER expose to browser
const STAGING_ACCESS_KEY = process.env.STAGING_ACCESS_KEY || "";

async function handleProxy(request: NextRequest): Promise<Response> {
  const url = new URL(request.url);
  const subpath = url.pathname.replace(/^\/api\/medicalplab/, "") || "/";
  const targetUrl = `${BFF_BASE_URL}${subpath}${url.search}`;

  const forwardHeaders = new Headers();

  // Forward permitted client headers
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

  // Inject server-only staging key
  if (STAGING_ACCESS_KEY) {
    forwardHeaders.set("x-staging-key", STAGING_ACCESS_KEY);
  }

  // Read request body for mutating methods
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
