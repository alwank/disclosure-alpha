import type { Review, ReviewQuery } from "./types";

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
