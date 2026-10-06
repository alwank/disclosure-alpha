import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import {
  fetchDesktopSettings,
  fetchReview,
  sendDesktopHeartbeat,
} from "./api";
import { DesktopSetup } from "./DesktopSetup";
import { buildSegments, searchRanges, type TextSegment } from "./highlights";
import { groupEvidence, readingBlockViews } from "./reading";
import type { Evidence, Provenance, Review, ReviewQuery } from "./types";

const defaultQuery: ReviewQuery = {
  ticker: "AAPL",
  fiscalYear: "2025",
  formType: "10-K",
  quarter: "",
};

function readQuery(): ReviewQuery | null {
  const params = new URLSearchParams(window.location.search);
  const ticker = params.get("ticker");
  const fiscalYear = params.get("fiscal_year");
  const formType = params.get("form_type");
  const quarter = params.get("quarter") ?? "";
  if (!ticker || !fiscalYear || !["10-K", "10-Q"].includes(formType ?? ""))
    return null;
  return {
    ticker,
    fiscalYear,
    formType: formType as ReviewQuery["formType"],
    quarter: ["Q1", "Q2", "Q3"].includes(quarter)
      ? (quarter as ReviewQuery["quarter"])
      : "",
  };
}

function formatScore(value: number | null | undefined): string {
  return value == null ? "—" : value.toFixed(1);
}

function band(value: number | null | undefined): string {
  if (value == null) return "missing";
  if (value <= 25) return "low";
  if (value <= 50) return "moderate";
  if (value <= 75) return "elevated";
  return "high";
}

function humanize(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function provenanceValue(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "number")
    return Number.isInteger(value) ? String(value) : value.toFixed(4);
  if (typeof value === "boolean" || typeof value === "string")
    return String(value);
  if (typeof value === "object" && "value" in value)
    return provenanceValue(value.value);
  return JSON.stringify(value);
}

function provenanceSections(provenance?: Provenance): string[] {
  if (!provenance) return [];
  const sections = new Set<string>();
  for (const value of Object.values(provenance.inputs)) {
    if (
      value &&
      typeof value === "object" &&
      "section" in value &&
      typeof value.section === "string"
    ) {
      sections.add(value.section);
    }
  }
  return [...sections];
}

export function App() {
  const initialQuery = useMemo(readQuery, []);
  const [query, setQuery] = useState<ReviewQuery>(initialQuery ?? defaultQuery);
  const [submitted, setSubmitted] = useState<ReviewQuery | null>(initialQuery);
  const [review, setReview] = useState<Review | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState("");
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(
    null,
  );
  const [selectedComponent, setSelectedComponent] = useState<string | null>(
    null,
  );
  const [search, setSearch] = useState("");
  const [mobileTab, setMobileTab] = useState<"score" | "reader" | "evidence">(
    "reader",
  );
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [desktopSetupRequired, setDesktopSetupRequired] = useState(false);
  const evidencePanelRef = useRef<HTMLElement>(null);
  const evidenceCloseRef = useRef<HTMLButtonElement>(null);
  const evidenceToggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    void fetchDesktopSettings(controller.signal)
      .then((status) => {
        if (status && !status.configured) setDesktopSetupRequired(true);
      })
      .catch(() => {
        // If this is an ordinary self-hosted deployment, preserve its UI.
      });
    void sendDesktopHeartbeat();
    const heartbeatTimer = window.setInterval(() => {
      void sendDesktopHeartbeat();
    }, 20_000);
    return () => {
      controller.abort();
      window.clearInterval(heartbeatTimer);
    };
  }, []);

  useEffect(() => {
    if (!submitted) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setReview(null);
    fetchReview(submitted, controller.signal)
      .then((result) => {
        setReview(result);
        setActiveSection(result.sections[0]?.section_name ?? "");
        setSelectedEvidenceId(null);
        setSelectedComponent(null);
        setSearch("");
        setEvidenceOpen(false);
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          cause instanceof Error
            ? cause.message
            : "Unable to load this filing.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [submitted]);

  useEffect(() => {
    if (!selectedEvidenceId) return;
    const frame = window.requestAnimationFrame(() => {
      const mark = document.querySelector<HTMLElement>(
        '[data-selected-hit="true"]',
      );
      mark?.scrollIntoView({ block: "center", behavior: "smooth" });
      mark?.focus({ preventScroll: true });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [activeSection, selectedEvidenceId]);

  useEffect(() => {
    if (!evidenceOpen) return;
    const drawerViewport = window.matchMedia("(min-width: 800px) and (max-width: 1279px)");
    const closeOutsideDrawerViewport = () => {
      if (!drawerViewport.matches) setEvidenceOpen(false);
    };
    drawerViewport.addEventListener("change", closeOutsideDrawerViewport);
    evidenceCloseRef.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setEvidenceOpen(false);
        evidenceToggleRef.current?.focus();
      } else if (event.key === "Tab") {
        const controls = evidencePanelRef.current?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), [tabindex="0"]',
        );
        if (!controls?.length) return;
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      window.removeEventListener("keydown", closeOnEscape);
      drawerViewport.removeEventListener("change", closeOutsideDrawerViewport);
    };
  }, [evidenceOpen]);

  const section = review?.sections.find(
    (item) => item.section_name === activeSection,
  );
  const sectionEvidence = useMemo(
    () =>
      review?.evidence.filter((item) => item.section === activeSection) ?? [],
    [review, activeSection],
  );
  const segments = useMemo(
    () =>
      section
        ? buildSegments(section.cleaned_text, sectionEvidence, search)
        : [],
    [section, sectionEvidence, search],
  );
  const readingBlocks = useMemo(
    () => (section ? readingBlockViews(section, segments) : []),
    [section, segments],
  );
  const evidenceGroups = useMemo(
    () => groupEvidence(review?.evidence ?? []),
    [review],
  );
  const searchCount = section
    ? searchRanges(section.cleaned_text, search).length
    : 0;
  const provenance = review?.scores.provenance.find(
    (item) => item.score_name === selectedComponent,
  );

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (query.formType === "10-Q" && !query.quarter) {
      setError("Choose Q1, Q2, or Q3 for a 10-Q filing.");
      return;
    }
    const normalized = { ...query, ticker: query.ticker.trim().toUpperCase() };
    const params = new URLSearchParams({
      ticker: normalized.ticker,
      fiscal_year: normalized.fiscalYear,
      form_type: normalized.formType,
    });
    if (normalized.formType === "10-Q")
      params.set("quarter", normalized.quarter);
    window.history.replaceState(
      {},
      "",
      `${window.location.pathname}?${params}`,
    );
    setSubmitted(normalized);
  }

  function selectEvidence(item: Evidence) {
    setActiveSection(item.section);
    setSelectedEvidenceId(item.id);
    setMobileTab("reader");
    setEvidenceOpen(false);
  }

  function moveEvidence(direction: -1 | 1) {
    if (!review?.evidence.length) return;
    const index = review.evidence.findIndex(
      (item) => item.id === selectedEvidenceId,
    );
    const next =
      index < 0
        ? direction === 1
          ? 0
          : review.evidence.length - 1
        : Math.max(0, Math.min(review.evidence.length - 1, index + direction));
    selectEvidence(review.evidence[next]);
  }

  function sectionLabel(name: string): string {
    return review?.display.section_labels[name] ?? humanize(name);
  }

  function renderSegment(segment: TextSegment) {
    const selected = segment.evidenceIds.includes(selectedEvidenceId ?? "");
    return segment.evidenceIds.length || segment.search ? (
      <mark
        key={segment.start}
        data-selected-hit={selected ? "true" : undefined}
        className={[
          segment.evidenceIds.length ? "flag-highlight" : "",
          segment.search ? "search-highlight" : "",
          selected ? "selected-highlight" : "",
        ].join(" ")}
        tabIndex={selected ? -1 : undefined}
      >
        {segment.text}
      </mark>
    ) : (
      <span key={segment.start}>{segment.text}</span>
    );
  }

  if (desktopSetupRequired) {
    return <DesktopSetup onComplete={() => setDesktopSetupRequired(false)} />;
  }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <strong>Disclosure Alpha</strong>
        </div>
        <span className="topbar-product">Filing review</span>
      </header>

      <div className="workspace-header">
        <div className="filing-identity">
          <p className="eyebrow">SEC filing review</p>
          <h1>
            {review
              ? `${review.filing.ticker} · FY${review.filing.fiscal_year} ${review.filing.quarter ? `${review.filing.quarter} ` : ""}${review.filing.form_type}`
              : "Select a company filing"}
          </h1>
          {review ? (
            <div className="filing-meta">
              <span>Filed {review.filing.filing_date ?? "—"}</span>
              <span>Accession {review.filing.accession_number}</span>
              {review.filing.source_url && (
                <a href={review.filing.source_url} target="_blank" rel="noopener noreferrer">
                  Original SEC filing ↗
                </a>
              )}
            </div>
          ) : (
            <p className="intro">Scores, marked language, and source text in one view.</p>
          )}
        </div>
        <form className="lookup" onSubmit={submit} aria-label="Select a filing">
          <label>
            Ticker
            <input
              aria-label="Ticker"
              value={query.ticker}
              onChange={(event) =>
                setQuery({ ...query, ticker: event.target.value })
              }
              required
              maxLength={12}
            />
          </label>
          <label>
            Fiscal year
            <input
              aria-label="Fiscal year"
              type="number"
              min="1994"
              max="2100"
              value={query.fiscalYear}
              onChange={(event) =>
                setQuery({ ...query, fiscalYear: event.target.value })
              }
              required
            />
          </label>
          <label>
            Form
            <select
              aria-label="Form"
              value={query.formType}
              onChange={(event) =>
                setQuery({
                  ...query,
                  formType: event.target.value as ReviewQuery["formType"],
                  quarter: "",
                })
              }
            >
              <option>10-K</option>
              <option>10-Q</option>
            </select>
          </label>
          {query.formType === "10-Q" && (
            <label>
              Quarter
              <select
                aria-label="Quarter"
                value={query.quarter}
                onChange={(event) =>
                  setQuery({
                    ...query,
                    quarter: event.target.value as ReviewQuery["quarter"],
                  })
                }
              >
                <option value="">Select</option>
                <option>Q1</option>
                <option>Q2</option>
                <option>Q3</option>
              </select>
            </label>
          )}
          <button className="run-button" type="submit" disabled={loading}>
            {loading ? "Loading…" : "Open filing"}
          </button>
        </form>
      </div>

      {error && (
        <div className="error-banner" role="alert">
          <strong>Could not load filing.</strong> {error}{" "}
          <button type="button" onClick={() => setSubmitted({ ...query })}>
            Retry
          </button>
        </div>
      )}
      {loading && (
        <div className="loading-banner" role="status">
          <span className="spinner" /> Fetching and analyzing filing…
        </div>
      )}

      {!review && !loading && !error && (
        <div className="empty-state">
          <p>
            Enter a ticker and fiscal period above. Try AAPL FY2025 10-K to
            explore the review.
          </p>
        </div>
      )}

      {review && (
        <>
          <nav className="mobile-tabs" aria-label="Review panels">
            {(["score", "reader", "evidence"] as const).map((tab) => (
              <button
                type="button"
                key={tab}
                className={mobileTab === tab ? "active" : ""}
                aria-pressed={mobileTab === tab}
                onClick={() => setMobileTab(tab)}
              >
                {tab === "reader" ? "Filing" : humanize(tab)}
              </button>
            ))}
          </nav>
          <main className="review-grid">
            <aside
              className={`panel score-panel mobile-${mobileTab}`}
              aria-label="Score dashboard"
            >
              <div className="panel-heading">
                <span>Scorecard</span>
                <span>01</span>
              </div>
              <div className="overall-card">
                <div className="overall-meta">
                  Disclosure language score{" "}
                  <span
                    className={`band-dot ${band(review.scores.overall_disclosure_risk_score)}`}
                  />
                </div>
                <div
                  className={`overall-value ${band(review.scores.overall_disclosure_risk_score)}`}
                >
                  {formatScore(review.scores.overall_disclosure_risk_score)}
                  <small>/ 100</small>
                </div>
                <div className="overall-label">
                  {review.scores.overall_disclosure_risk_score == null
                    ? "Score unavailable"
                    : `${humanize(band(review.scores.overall_disclosure_risk_score))} score band`}
                </div>
              </div>
              <div className="quality-row">
                <div>
                  <span>Coverage</span>
                  <strong>
                    {Math.round(review.scores.score_coverage_ratio * 100)}%
                  </strong>
                </div>
                <div>
                  <span>Confidence</span>
                  <strong>
                    {Math.round(review.scores.confidence_score * 100)}%
                  </strong>
                </div>
              </div>
              {review.scores.missing_components.length > 0 && (
                <p className="missing-note">
                  Missing:{" "}
                  {review.scores.missing_components.map(humanize).join(", ")}.
                  Missing scores are not zero.
                </p>
              )}
              <div className="subheading">
                Component scores <span>Weight</span>
              </div>
              <div className="component-list">
                {review.display.headline_rows.map((row) => (
                  <button
                    type="button"
                    key={row.key}
                    className={`component-row ${selectedComponent === row.key ? "chosen" : ""}`}
                    onClick={() =>
                      setSelectedComponent(
                        selectedComponent === row.key ? null : row.key,
                      )
                    }
                    aria-expanded={selectedComponent === row.key}
                  >
                    <span className="component-name">{row.label}</span>
                    <span className="component-weight">{row.weight_pct}%</span>
                    <strong className={band(row.score)}>
                      {formatScore(row.score)}
                    </strong>
                  </button>
                ))}
              </div>
              {selectedComponent && (
                <div className="component-detail">
                  <div className="detail-title">
                    Score inputs{" "}
                    <button
                      type="button"
                      aria-label="Close score inputs"
                      onClick={() => setSelectedComponent(null)}
                    >
                      ×
                    </button>
                  </div>
                  {!provenance ||
                  Object.keys(provenance.inputs).length === 0 ? (
                    <p>No input breakdown is available for this component.</p>
                  ) : (
                    <>
                      <dl>
                        {Object.entries(provenance.inputs).map(
                          ([key, value]) => (
                            <div key={key}>
                              <dt>{humanize(key)}</dt>
                              <dd>{provenanceValue(value)}</dd>
                            </div>
                          ),
                        )}
                      </dl>
                      {provenanceSections(provenance).length > 0 && (
                        <div className="related-sections">
                          <span>RELATED SECTIONS</span>
                          {provenanceSections(provenance).map((name) => (
                            <button
                              type="button"
                              key={name}
                              onClick={() => {
                                setActiveSection(name);
                                setSelectedEvidenceId(null);
                                setMobileTab("reader");
                              }}
                            >
                              {sectionLabel(name)} ↗
                            </button>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
              <div className="subheading flags-heading">
                Matched phrase categories <span>{review.display.flag_summary.length}</span>
              </div>
              <p className="microcopy">
                Phrase matches in extracted text; these are not confirmed events.
              </p>
              {review.display.flag_summary.length === 0 ? (
                <p className="muted">No active flags in extracted sections.</p>
              ) : (
                <div className="flag-chips">
                  {review.display.flag_summary.map((flag) => (
                    <button
                      className={`flag-chip tier-${flag.tier}`}
                      key={flag.flag}
                      type="button"
                      onClick={() => {
                        const hit = review.evidence.find(
                          (item) => item.flag === flag.flag,
                        );
                        if (hit) selectEvidence(hit);
                      }}
                    >
                      {flag.label}
                      <small>
                        {flag.section_count}{" "}
                        {flag.section_count === 1 ? "section" : "sections"}
                      </small>
                    </button>
                  ))}
                </div>
              )}
              <div className="subheading changes-heading">Section changes</div>
              {review.display.change_rows.length === 0 ? (
                <p className="muted">No prior comparison available.</p>
              ) : (
                <div className="change-list">
                  {review.display.change_rows.map((change) => (
                    <button
                      type="button"
                      key={change.section}
                      onClick={() => {
                        setActiveSection(change.section);
                        setSelectedEvidenceId(null);
                        setMobileTab("reader");
                      }}
                    >
                      <span>{change.section_label}</span>
                      <strong>{formatScore(change.change_score)}</strong>
                    </button>
                  ))}
                </div>
              )}
            </aside>

            <section
              className={`panel reader-panel mobile-${mobileTab}`}
              aria-label="Filing reader"
            >
              <div className="panel-heading">
                <span>Filing reader</span>
                <span>{review.sections.length} sections</span>
              </div>
              <div className="reader-toolbar">
                <div className="section-select-wrap">
                  <label htmlFor="section-select">Section</label>
                  <select
                    id="section-select"
                    value={activeSection}
                    onChange={(event) => {
                      setActiveSection(event.target.value);
                      setSelectedEvidenceId(null);
                    }}
                  >
                    {review.sections.map((item) => (
                      <option key={item.section_name} value={item.section_name}>
                        {sectionLabel(item.section_name)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="search-wrap">
                  <label htmlFor="filing-search">Search text</label>
                  <div>
                    <input
                      id="filing-search"
                      type="search"
                      placeholder="Find text…"
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                    />
                    {search && (
                      <span className="search-count">{searchCount}</span>
                    )}
                  </div>
                </div>
                <button
                  ref={evidenceToggleRef}
                  className="evidence-toggle"
                  type="button"
                  aria-controls="evidence-panel"
                  aria-expanded={evidenceOpen}
                  onClick={() => setEvidenceOpen(true)}
                >
                  Evidence <span>{review.evidence.length}</span>
                </button>
              </div>
              {selectedEvidenceId && (
                <div className="selected-evidence-context">
                  Matched phrase: <strong>{review.evidence.find((item) => item.id === selectedEvidenceId)?.matched_text}</strong>
                </div>
              )}
              {section ? (
                <>
                  <div className="section-head">
                    <div>
                      <p className="eyebrow">Extracted filing text</p>
                      <h2>{sectionLabel(section.section_name)}</h2>
                      <p>
                        {section.word_count.toLocaleString()} words ·{" "}
                        {sectionEvidence.length} marked{" "}
                        {sectionEvidence.length === 1 ? "phrase" : "phrases"} ·
                        Extraction confidence{" "}
                        {Math.round(section.extraction_confidence * 100)}%
                      </p>
                    </div>
                  </div>
                  {section.warnings.length > 0 && (
                    <details className="section-warning">
                      <summary>Text extraction notes</summary>
                      <p>{section.warnings.map(humanize).join(", ")}</p>
                    </details>
                  )}
                  <article
                    className="filing-text"
                    aria-label={`${sectionLabel(section.section_name)} filing text`}
                  >
                    {readingBlocks.map((block, index) =>
                      block.kind === "heading" ? (
                        <h3 key={index}>{block.segments.map(renderSegment)}</h3>
                      ) : (
                        <p key={index}>{block.segments.map(renderSegment)}</p>
                      ),
                    )}
                  </article>
                </>
              ) : (
                <div className="reader-empty">
                  No sections were extracted from this filing. Check the
                  original SEC filing.
                </div>
              )}
            </section>

            {evidenceOpen && (
              <button
                className="drawer-backdrop"
                type="button"
                aria-hidden="true"
                tabIndex={-1}
                onClick={() => {
                  setEvidenceOpen(false);
                  evidenceToggleRef.current?.focus();
                }}
              />
            )}
            <aside
              ref={evidencePanelRef}
              id="evidence-panel"
              className={`panel evidence-panel mobile-${mobileTab} ${evidenceOpen ? "drawer-open" : ""}`}
              aria-label="Flag evidence"
              role={evidenceOpen ? "dialog" : undefined}
              aria-modal={evidenceOpen ? true : undefined}
            >
              <div className="panel-heading">
                <span>Evidence</span>
                <span>{review.evidence.length} phrase matches</span>
                <button
                  ref={evidenceCloseRef}
                  className="drawer-close"
                  type="button"
                  aria-label="Close evidence"
                  onClick={() => {
                    setEvidenceOpen(false);
                    evidenceToggleRef.current?.focus();
                  }}
                >
                  ×
                </button>
              </div>
              <div className="evidence-intro">
                <h2>Marked language</h2>
                <p>Phrase matches, not confirmed events. Choose one to read it in context.</p>
              </div>
              <div className="evidence-controls">
                <button
                  type="button"
                  onClick={() => moveEvidence(-1)}
                  disabled={
                    !review.evidence.length ||
                    selectedEvidenceId === review.evidence[0]?.id
                  }
                >
                  ← Previous
                </button>
                <span>
                  {selectedEvidenceId
                    ? `${review.evidence.findIndex((item) => item.id === selectedEvidenceId) + 1} / ${review.evidence.length}`
                    : `${review.evidence.length} total`}
                </span>
                <button
                  type="button"
                  onClick={() => moveEvidence(1)}
                  disabled={
                    !review.evidence.length ||
                    selectedEvidenceId === review.evidence.at(-1)?.id
                  }
                >
                  Next →
                </button>
              </div>
              {review.evidence.length === 0 ? (
                <p className="no-evidence">
                  No unsuppressed flag phrases were detected in the extracted
                  sections.
                </p>
              ) : (
                <div className="evidence-groups">
                  {review.sections.map((item) => {
                    const groups = evidenceGroups.filter(
                      (group) => group.section === item.section_name,
                    );
                    if (!groups.length) return null;
                    return (
                      <div className="evidence-group" key={item.section_name}>
                        <div className="group-heading">
                          <span>{sectionLabel(item.section_name)}</span>
                          <span>{groups.reduce((count, group) => count + group.hits.length, 0)}</span>
                        </div>
                        {groups.map((group) => (
                          <div
                            key={group.key}
                            className={`evidence-hit ${group.hits.some((hit) => hit.id === selectedEvidenceId) ? "selected" : ""}`}
                          >
                            <p className="hit-context">{group.sentence}</p>
                            <div className="hit-phrases">
                              {group.hits.map((hit) => (
                                <button
                                  key={hit.id}
                                  type="button"
                                  onClick={() => selectEvidence(hit)}
                                  aria-current={selectedEvidenceId === hit.id ? "true" : undefined}
                                  aria-label={`${hit.label}: ${hit.matched_text}`}
                                >
                                  <span>{hit.label}</span>
                                  <strong>“{hit.matched_text}”</strong>
                                </button>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    );
                  })}
                </div>
              )}
            </aside>
          </main>
          <footer className="footer">
            <span>Scores describe filing language, not an investment recommendation.</span>
            <details>
              <summary>Method details</summary>
              <span>{review.versions.scoring_model_version} · {review.versions.parser_version}</span>
            </details>
          </footer>
        </>
      )}
    </div>
  );
}
