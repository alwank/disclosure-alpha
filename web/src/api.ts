import type { Review, ReviewQuery } from "./types";

export type DesktopSettingsStatus = {
  configured: boolean;
  display_name: string | null;
};

export type DesktopSettingsInput = {
  displayName: string;
  email: string;
};

async function responseError(response: Response): Promise<Error> {
  let detail = `Request failed (${response.status})`;
  try {
    const body = (await response.json()) as { detail?: string };
    if (body.detail) detail = body.detail;
  } catch {
    /* Keep status message for non-JSON failures. */
  }
  return new Error(detail);
}

export async function fetchReview(
  query: ReviewQuery,
  signal?: AbortSignal,
): Promise<Review> {
  const params = new URLSearchParams({
    fiscal_year: query.fiscalYear,
    form_type: query.formType,
    compare: "prior",
    scoring_model_version: "deterministic_scoring_v2",
  });
  if (query.formType === "10-Q") params.set("quarter", query.quarter);
  const response = await fetch(
    `/v1/company/${encodeURIComponent(query.ticker.trim().toUpperCase())}/filing-review?${params}`,
    { signal },
  );
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json() as Promise<Review>;
}

/**
 * `null` means this is a normal self-hosted API rather than the desktop app.
 * A 404 is deliberate: desktop settings routes are never mounted there.
 */
export async function fetchDesktopSettings(
  signal?: AbortSignal,
): Promise<DesktopSettingsStatus | null> {
  const response = await fetch("/v1/desktop/settings", { signal });
  if (response.status === 404) return null;
  if (!response.ok) throw await responseError(response);
  const body = (await response.json()) as Partial<DesktopSettingsStatus>;
  return typeof body.configured === "boolean"
    ? {
        configured: body.configured,
        display_name:
          typeof body.display_name === "string" ? body.display_name : null,
      }
    : null;
}

export async function saveDesktopSettings(
  input: DesktopSettingsInput,
): Promise<DesktopSettingsStatus> {
  const response = await fetch("/v1/desktop/settings", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      display_name: input.displayName,
      email: input.email,
    }),
  });
  if (!response.ok) throw await responseError(response);
  return response.json() as Promise<DesktopSettingsStatus>;
}

export async function sendDesktopHeartbeat(): Promise<void> {
  try {
    await fetch("/v1/desktop/heartbeat", { method: "POST" });
  } catch {
    // A self-hosted API intentionally has no heartbeat route. It needs no UI hint.
  }
}
