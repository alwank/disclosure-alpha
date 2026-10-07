import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { fetchReview } from "./api";
import { buildSegments, searchRanges, type TextSegment } from "./highlights";
import { groupEvidence, readingBlockViews } from "./reading";
import type {
  Evidence,
  Provenance,
  Review,
  ReviewQuery,
  SectionChangeDrivers,
} from "./types";

const defaultQuery: ReviewQuery = {
  ticker: "AAPL",
  fiscalYear: "2025",
  formType: "10-K",
  quarter: "",
};

const deltaLabels: Record<string, string> = {
  negative_language_delta: "Negative language",
  uncertainty_language_delta: "Uncertainty language",
  legal_language_delta: "Legal language",
  constraining_language_delta: "Constraining language",
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

function scoreWidth(value: number | null | undefined): string {
  return `${Math.max(0, Math.min(100, value ?? 0))}%`;
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

function formatDelta(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)} pp`;
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

function TopicGroup({ label, topics }: { label: string; topics: string[] }) {
  return (
    <div className="topic-group">
      <span>{label}</span>
      {topics.length ? (
        <div className="topic-list">
          {topics.map((topic) => (
            <span key={topic}>{humanize(topic)}</span>
          ))}
        </div>
      ) : (
        <em>None detected</em>
      )}
    </div>
  );
}

function ChangeDrivers({ drivers }: { drivers: SectionChangeDrivers }) {
  return (
    <div className="change-drivers">
      <p className="context-note">
        Detected comparison signals. The change score measures magnitude, not
        whether the disclosure improved or worsened.
      </p>
      <div className="driver-counts">
        <div>
          <strong>{drivers.added_sentence_count}</strong>
          <span>sentences added</span>
        </div>
        <div>
          <strong>{drivers.removed_sentence_count}</strong>
          <span>sentences removed</span>
        </div>
        <div>
          <strong>{drivers.changed_numeric_count}</strong>
          <span>numeric token changes</span>
        </div>
      </div>
      <TopicGroup label="New topics" topics={drivers.new_topics} />
      <TopicGroup
        label="Intensified topics"
        topics={drivers.intensified_topics}
      />
      <TopicGroup label="Removed topics" topics={drivers.removed_topics} />
      <div className="driver-heading">
        Language shifts <span>percentage points</span>
      </div>
      <dl className="delta-list">
        {Object.entries(drivers.language_deltas).map(([name, value]) => (
          <div key={name}>
            <dt>
              {deltaLabels[name] ?? humanize(name.replace(/_delta$/, ""))}
            </dt>
            <dd
              className={
                value > 0 ? "positive-delta" : value < 0 ? "negative-delta" : ""
              }
            >
              {formatDelta(value)}
            </dd>
          </div>
        ))}
      </dl>
      <p className="driver-confidence">
        Comparison confidence {Math.round(drivers.confidence_score * 100)}%
      </p>
    </div>
  );
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
  const [selectedChangeSection, setSelectedChangeSection] = useState<
    string | null
  >(null);
  const [search, setSearch] = useState("");
  const [activeSearchIndex, setActiveSearchIndex] = useState(-1);
  const [sectionFilter, setSectionFilter] = useState("");
  const [flagFilter, setFlagFilter] = useState("");
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const workspaceRef = useRef<HTMLElement>(null);
  const evidencePanelRef = useRef<HTMLElement>(null);
  const evidenceCloseRef = useRef<HTMLButtonElement>(null);
  const evidenceToggleRef = useRef<HTMLButtonElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

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
        setSelectedChangeSection(null);
        setSearch("");
        setActiveSearchIndex(-1);
        setSectionFilter("");
        setFlagFilter("");
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
    const drawerViewport = window.matchMedia?.("(max-width: 1279px)");
    const closeOutsideDrawerViewport = () => {
      if (drawerViewport && !drawerViewport.matches) setEvidenceOpen(false);
    };
    drawerViewport?.addEventListener("change", closeOutsideDrawerViewport);
    evidenceCloseRef.current?.focus();
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setEvidenceOpen(false);
        evidenceToggleRef.current?.focus();
      } else if (event.key === "Tab") {
        const controls =
          evidencePanelRef.current?.querySelectorAll<HTMLElement>(
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
      drawerViewport?.removeEventListener("change", closeOutsideDrawerViewport);
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
  const visibleEvidence =
    selectedChangeSection === activeSection ? [] : sectionEvidence;
  const searchMatches = useMemo(
    () => (section ? searchRanges(section.cleaned_text, search) : []),
    [section, search],
  );
  const activeSearchRange = searchMatches[activeSearchIndex];
  const segments = useMemo(
    () =>
      section
        ? buildSegments(section.cleaned_text, visibleEvidence, search)
        : [],
    [section, visibleEvidence, search],
  );
  const readingBlocks = useMemo(
    () => (section ? readingBlockViews(section, segments) : []),
    [section, segments],
  );
  const filteredEvidence = useMemo(
    () => {
      const sectionOrder = new Map(
        (review?.sections ?? []).map((item, index) => [item.section_name, index]),
      );
      return (review?.evidence ?? [])
        .filter(
          (item) =>
            (!sectionFilter || item.section === sectionFilter) &&
            (!flagFilter || item.flag === flagFilter),
        )
        .sort(
          (a, b) =>
            (sectionOrder.get(a.section) ?? Infinity) -
              (sectionOrder.get(b.section) ?? Infinity) ||
            a.start - b.start ||
            a.end - b.end ||
            a.id.localeCompare(b.id),
        );
    },
    [review, sectionFilter, flagFilter],
  );
  const evidenceGroups = useMemo(
    () => groupEvidence(filteredEvidence),
    [filteredEvidence],
  );
  const sectionCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of review?.evidence ?? [])
      counts.set(item.section, (counts.get(item.section) ?? 0) + 1);
    return counts;
  }, [review]);
  const flagOptions = useMemo(() => {
    const labels = new Map(
      (review?.evidence ?? []).map((item) => [item.flag, item.label]),
    );
    const options = (review?.display.flag_summary ?? [])
      .filter((item) => labels.has(item.flag))
      .map((item) => ({ flag: item.flag, label: item.label }));
    for (const [flag, label] of labels) {
      if (!options.some((item) => item.flag === flag))
        options.push({ flag, label });
    }
    return options;
  }, [review]);

  const provenance = review?.scores.provenance.find(
    (item) => item.score_name === selectedComponent,
  );
  const selectedEvidence = review?.evidence.find(
    (item) => item.id === selectedEvidenceId,
  );
  const selectedChange = review?.display.change_rows.find(
    (item) => item.section === selectedChangeSection,
  );
  const selectedDrivers = selectedChangeSection
    ? review?.changes.section_drivers?.[selectedChangeSection]
    : undefined;
  const changeRows = [...(review?.display.change_rows ?? [])].sort(
    (a, b) => (b.change_score ?? -1) - (a.change_score ?? -1),
  );

  function sectionLabel(name: string): string {
    return review?.display.section_labels[name] ?? humanize(name);
  }

  function scrollToWorkspace() {
    window.requestAnimationFrame(() =>
      workspaceRef.current?.scrollIntoView({
        block: "start",
        behavior: "smooth",
      }),
    );
  }

  function openContextOnNarrow() {
    if (window.matchMedia?.("(max-width: 1279px)").matches)
      setEvidenceOpen(true);
  }

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

  function selectChange(sectionName: string) {
    setActiveSection(sectionName);
    setActiveSearchIndex(-1);
    setSelectedChangeSection(sectionName);
    setSelectedComponent(null);
    setSelectedEvidenceId(null);
    scrollToWorkspace();
    openContextOnNarrow();
  }

  function selectComponent(key: string) {
    const next = selectedComponent === key ? null : key;
    setSelectedComponent(next);
    setSelectedChangeSection(null);
    setSelectedEvidenceId(null);
    if (next) openContextOnNarrow();
  }

  function selectEvidence(item: Evidence) {
    setActiveSection(item.section);
    setActiveSearchIndex(-1);
    if (sectionFilter && sectionFilter !== item.section) setSectionFilter("");
    if (flagFilter && flagFilter !== item.flag) setFlagFilter("");
    setSelectedEvidenceId(item.id);
    setSelectedComponent(null);
    setSelectedChangeSection(null);
    setEvidenceOpen(false);
    scrollToWorkspace();
  }

  function moveEvidence(direction: -1 | 1) {
    if (!filteredEvidence.length) return;
    const index = filteredEvidence.findIndex(
      (item) => item.id === selectedEvidenceId,
    );
    const next =
      index < 0
        ? direction === 1
          ? 0
          : filteredEvidence.length - 1
        : Math.max(0, Math.min(filteredEvidence.length - 1, index + direction));
    selectEvidence(filteredEvidence[next]);
  }

  function setEvidenceFilters(nextSection: string, nextFlag: string) {
    setSectionFilter(nextSection);
    setFlagFilter(nextFlag);
    if (
      selectedEvidence &&
      ((nextSection && selectedEvidence.section !== nextSection) ||
        (nextFlag && selectedEvidence.flag !== nextFlag))
    )
      setSelectedEvidenceId(null);
  }

  function selectReaderSection(sectionName: string) {
    setActiveSection(sectionName);
    setActiveSearchIndex(-1);
    setSelectedEvidenceId(null);
    setSelectedChangeSection(null);
  }

  function moveSearch(direction: -1 | 1) {
    if (!searchMatches.length) return;
    setActiveSearchIndex((current) =>
      current < 0
        ? direction === 1
          ? 0
          : searchMatches.length - 1
        : (current + direction + searchMatches.length) % searchMatches.length,
    );
    window.requestAnimationFrame(() => {
      document
        .querySelector<HTMLElement>('[data-active-search-hit="true"]')
        ?.scrollIntoView({ block: "center", behavior: "smooth" });
    });
  }

  function renderSegment(segment: TextSegment) {
    const selected = segment.evidenceIds.includes(selectedEvidenceId ?? "");
    const activeSearch =
      segment.search &&
      activeSearchRange != null &&
      segment.start < activeSearchRange[1] &&
      segment.end > activeSearchRange[0];
    return segment.evidenceIds.length || segment.search ? (
      <mark
        key={segment.start}
        data-selected-hit={selected ? "true" : undefined}
        data-active-search-hit={
          activeSearch && segment.start === activeSearchRange[0]
            ? "true"
            : undefined
        }
        className={[
          segment.evidenceIds.length ? "flag-highlight" : "",
          segment.search ? "search-highlight" : "",
          activeSearch ? "active-search-highlight" : "",
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
                <a
                  href={review.filing.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Original SEC filing ↗
                </a>
              )}
            </div>
          ) : (
            <p className="intro">
              Scores, change signals, and marked source text in one view.
            </p>
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
          <section className="overview" aria-label="Review overview">
            <div className="overview-title">
              <div>
                <p className="eyebrow">Analysis overview</p>
                <h2>Start with what changed</h2>
              </div>
              <p>
                Review the signals, then inspect the extracted filing text
                below.
              </p>
            </div>
            <div className="overview-top">
              <div className="overview-card overall-card">
                <div className="card-title">
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
                <p>
                  {review.scores.overall_disclosure_risk_score == null
                    ? "Score unavailable"
                    : `${humanize(band(review.scores.overall_disclosure_risk_score))} concern band`}
                </p>
                <div className="score-track" aria-hidden="true">
                  <span
                    className={`risk-fill ${band(review.scores.overall_disclosure_risk_score)}`}
                    style={{
                      width: scoreWidth(
                        review.scores.overall_disclosure_risk_score,
                      ),
                    }}
                  />
                </div>
              </div>
              <div className="overview-card quality-card">
                <div className="quality-metrics">
                  <div>
                    <span>Score coverage</span>
                    <strong>
                      {Math.round(review.scores.score_coverage_ratio * 100)}%
                    </strong>
                    <small>
                      {
                        review.display.headline_rows.filter(
                          (row) => row.score != null,
                        ).length
                      }{" "}
                      of {review.display.headline_rows.length} components
                    </small>
                  </div>
                  <div>
                    <span>Confidence</span>
                    <strong>
                      {Math.round(review.scores.confidence_score * 100)}%
                    </strong>
                    <small>Pipeline confidence</small>
                  </div>
                </div>
                <div className="comparison-meta">
                  {review.filing.prior_accession_number ? (
                    <>
                      Compared with prior filing{" "}
                      <strong>{review.filing.prior_accession_number}</strong>
                    </>
                  ) : (
                    "No prior comparison available"
                  )}
                </div>
              </div>
            </div>

            <div className="overview-cards">
              <section
                className="overview-card changes-card"
                aria-labelledby="changes-title"
              >
                <div className="card-heading">
                  <div>
                    <p className="eyebrow">01 · Comparison</p>
                    <h3 id="changes-title">Disclosure change by section</h3>
                  </div>
                  <span>0–100</span>
                </div>
                <p className="card-description">
                  Change magnitude versus the prior comparable filing. A larger
                  bar means more change, not necessarily worse disclosure.
                </p>
                {changeRows.length ? (
                  <div className="ranked-bars">
                    {changeRows.map((change) => (
                      <button
                        type="button"
                        key={change.section}
                        className={`ranked-row ${selectedChangeSection === change.section ? "chosen" : ""}`}
                        aria-pressed={selectedChangeSection === change.section}
                        aria-label={`${change.section_label}, change magnitude ${formatScore(change.change_score)} out of 100`}
                        onClick={() => selectChange(change.section)}
                      >
                        <span className="ranked-label">
                          {change.section_label}
                        </span>
                        <span className="bar-track" aria-hidden="true">
                          <span
                            className="change-fill"
                            style={{ width: scoreWidth(change.change_score) }}
                          />
                        </span>
                        <strong>{formatScore(change.change_score)}</strong>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="card-empty">
                    <strong>No prior comparison available</strong>
                    <span>
                      {review.changes.change_score.missing_reason ===
                      "compare=none"
                        ? "Comparison was not requested."
                        : "A prior comparable filing could not be scored."}
                    </span>
                  </div>
                )}
              </section>

              <section
                className="overview-card components-card"
                aria-labelledby="components-title"
              >
                <div className="card-heading">
                  <div>
                    <p className="eyebrow">02 · Score anatomy</p>
                    <h3 id="components-title">Component scores</h3>
                  </div>
                  <span>Weight</span>
                </div>
                <p className="card-description">
                  Each bar uses the 0–100 component scale; weight is shown
                  separately.
                </p>
                <div className="component-list">
                  {review.display.headline_rows.map((row) => (
                    <button
                      type="button"
                      key={row.key}
                      className={`component-row ${selectedComponent === row.key ? "chosen" : ""}`}
                      aria-pressed={selectedComponent === row.key}
                      aria-label={`${row.label}, score ${formatScore(row.score)} out of 100, weight ${row.weight_pct}%`}
                      onClick={() => selectComponent(row.key)}
                    >
                      <span className="component-name">{row.label}</span>
                      <span
                        className="component-bar bar-track"
                        aria-hidden="true"
                      >
                        <span
                          className={`risk-fill ${band(row.score)}`}
                          style={{ width: scoreWidth(row.score) }}
                        />
                      </span>
                      <strong className={band(row.score)}>
                        {formatScore(row.score)}
                      </strong>
                      <span className="component-weight">
                        {row.weight_pct}%
                      </span>
                    </button>
                  ))}
                </div>
                {review.scores.missing_components.length > 0 && (
                  <p className="missing-note">
                    Missing scores are shown as —, not zero.
                  </p>
                )}
              </section>

              <section
                className="overview-card flags-card"
                aria-labelledby="flags-title"
              >
                <div className="card-heading">
                  <div>
                    <p className="eyebrow">03 · Evidence</p>
                    <h3 id="flags-title">Matched language</h3>
                  </div>
                  <span>{review.evidence.length} phrases</span>
                </div>
                <p className="card-description">
                  Phrase matches in extracted text; these are not confirmed
                  events.
                </p>
                {review.display.flag_summary.length ? (
                  <div className="flag-list">
                    {review.display.flag_summary.map((flag) => {
                      const hit = review.evidence.find(
                        (item) => item.flag === flag.flag,
                      );
                      const count = review.evidence.filter(
                        (item) => item.flag === flag.flag,
                      ).length;
                      return (
                        <button
                          className="flag-row"
                          key={flag.flag}
                          type="button"
                          disabled={!hit}
                          onClick={() => hit && selectEvidence(hit)}
                        >
                          <span className={`flag-dot tier-${flag.tier}`} />
                          <span>{flag.label}</span>
                          <small>
                            {count} {count === 1 ? "phrase" : "phrases"}
                          </small>
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  <p className="card-empty">
                    No active flags in extracted sections.
                  </p>
                )}
              </section>
            </div>
          </section>

          <main
            ref={workspaceRef}
            className="review-workspace"
            aria-label="Filing inspection"
          >
            <div className="workspace-title">
              <div>
                <p className="eyebrow">Filing inspection</p>
                <h2>Read the source text</h2>
              </div>
              <span>{review.sections.length} extracted sections</span>
            </div>
            <div className="review-grid">
              <section
                className="panel reader-panel"
                aria-label="Filing reader"
              >
                <div className="panel-heading">
                  <span>Filing reader</span>
                  <span>
                    {section
                      ? sectionLabel(section.section_name)
                      : "No section"}
                  </span>
                </div>
                <div className="reader-toolbar">
                  <div className="section-select-wrap">
                    <label htmlFor="section-select">Section</label>
                    <select
                      id="section-select"
                      value={activeSection}
                      onChange={(event) =>
                        selectReaderSection(event.target.value)
                      }
                    >
                      {review.sections.map((item) => (
                        <option
                          key={item.section_name}
                          value={item.section_name}
                        >
                          {sectionLabel(item.section_name)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="search-wrap">
                    <label htmlFor="filing-search">Search text</label>
                    <div>
                      <input
                        ref={searchInputRef}
                        id="filing-search"
                        type="search"
                        placeholder="Find text…"
                        value={search}
                        onChange={(event) => {
                          setSearch(event.target.value);
                          setActiveSearchIndex(-1);
                        }}
                        onKeyDown={(event) => {
                          if (event.key === "Enter") {
                            event.preventDefault();
                            moveSearch(event.shiftKey ? -1 : 1);
                          }
                        }}
                      />
                    </div>
                  </div>
                  <div className="search-navigation" aria-label="Search matches">
                    <button
                      type="button"
                      aria-label="Previous search match"
                      disabled={!searchMatches.length}
                      onClick={() => {
                        moveSearch(-1);
                        searchInputRef.current?.focus();
                      }}
                    >
                      ↑
                    </button>
                    <span aria-live="polite">
                      {searchMatches.length
                        ? activeSearchIndex < 0
                          ? `${searchMatches.length} matches`
                          : `${activeSearchIndex + 1} of ${searchMatches.length}`
                        : search.trim()
                          ? "0 matches"
                          : ""}
                    </span>
                    <button
                      type="button"
                      aria-label="Next search match"
                      disabled={!searchMatches.length}
                      onClick={() => {
                        moveSearch(1);
                        searchInputRef.current?.focus();
                      }}
                    >
                      ↓
                    </button>
                  </div>
                  <button
                    ref={evidenceToggleRef}
                    className="evidence-toggle"
                    type="button"
                    aria-controls="evidence-panel"
                    aria-expanded={evidenceOpen}
                    onClick={() => setEvidenceOpen(true)}
                  >
                    Details & evidence <span>{review.evidence.length}</span>
                  </button>
                </div>
                <div className="reader-body">
                  <nav className="section-rail" aria-label="Filing sections">
                    <span className="section-rail-title">Sections</span>
                    {review.sections.map((item) => {
                      const count = sectionCounts.get(item.section_name) ?? 0;
                      return (
                        <button
                          key={item.section_name}
                          type="button"
                          aria-current={
                            activeSection === item.section_name ? "true" : undefined
                          }
                          onClick={() => selectReaderSection(item.section_name)}
                        >
                          <span>{sectionLabel(item.section_name)}</span>
                          <small aria-label={`${count} matched phrases`}>
                            {count}
                          </small>
                        </button>
                      );
                    })}
                  </nav>
                  <div className="reader-content">
                    {selectedEvidence && (
                      <div className="selected-evidence-context">
                        Matched phrase:{" "}
                        <strong>{selectedEvidence.matched_text}</strong>
                      </div>
                    )}
                    {section ? (
                      <>
                        <div className="section-head">
                          <p className="eyebrow">Extracted filing text</p>
                          <h2>{sectionLabel(section.section_name)}</h2>
                          <p>
                            {section.word_count.toLocaleString()} words ·{" "}
                            {sectionEvidence.length} marked{" "}
                            {sectionEvidence.length === 1 ? "phrase" : "phrases"} ·
                            Extraction confidence{" "}
                            {Math.round(section.extraction_confidence * 100)}%
                          </p>
                          {selectedChangeSection === section.section_name && (
                            <span className="reading-caveat">
                              Current filing text · no passage diff is shown
                            </span>
                          )}
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
                              <h3 key={index}>
                                {block.segments.map(renderSegment)}
                              </h3>
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
                  </div>
                </div>
              </section>

              {evidenceOpen && (
                <button
                  className="drawer-backdrop"
                  type="button"
                  aria-label="Close details"
                  onClick={() => {
                    setEvidenceOpen(false);
                    evidenceToggleRef.current?.focus();
                  }}
                />
              )}
              <aside
                ref={evidencePanelRef}
                id="evidence-panel"
                className={`panel evidence-panel ${evidenceOpen ? "drawer-open" : ""}`}
                aria-label="Review context"
                role={evidenceOpen ? "dialog" : undefined}
                aria-modal={evidenceOpen ? true : undefined}
              >
                <div className="panel-heading">
                  <span>Context & evidence</span>
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
                <div className="context-content">
                  {selectedChange ? (
                    <>
                      <p className="eyebrow">Section comparison</p>
                      <h2>{selectedChange.section_label}</h2>
                      <div className="context-score">
                        <strong>
                          {formatScore(selectedChange.change_score)}
                        </strong>
                        <span>/ 100 change magnitude</span>
                      </div>
                      {selectedDrivers ? (
                        <ChangeDrivers drivers={selectedDrivers} />
                      ) : (
                        <p className="context-note">
                          No driver details are available for this section.
                        </p>
                      )}
                    </>
                  ) : selectedComponent ? (
                    <>
                      <p className="eyebrow">Component inputs</p>
                      <h2>
                        {review.display.headline_rows.find(
                          (row) => row.key === selectedComponent,
                        )?.label ?? humanize(selectedComponent)}
                      </h2>
                      {!provenance || !Object.keys(provenance.inputs).length ? (
                        <p className="context-note">
                          No input breakdown is available for this component.
                        </p>
                      ) : (
                        <>
                          <dl className="provenance-list">
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
                              <span>Related sections</span>
                              {provenanceSections(provenance).map((name) => (
                                <button
                                  type="button"
                                  key={name}
                                  onClick={() => {
                                    selectReaderSection(name);
                                    setEvidenceOpen(false);
                                    scrollToWorkspace();
                                  }}
                                >
                                  {sectionLabel(name)} ↗
                                </button>
                              ))}
                            </div>
                          )}
                        </>
                      )}
                    </>
                  ) : selectedEvidence ? (
                    <>
                      <p className="eyebrow">Selected phrase</p>
                      <h2>{selectedEvidence.label}</h2>
                      <p className="context-note">
                        “{selectedEvidence.sentence}”
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="eyebrow">Inspection guide</p>
                      <h2>Select a signal</h2>
                      <p className="context-note">
                        Choose a change bar, component, or phrase to see its
                        details alongside the filing.
                      </p>
                    </>
                  )}
                </div>
                <div className="evidence-section">
                  <div className="evidence-intro">
                    <h2>Marked language</h2>
                    <p>
                      Phrase matches, not confirmed events. Choose one to read
                      it in context.
                    </p>
                  </div>
                  <div className="evidence-filters">
                    <label>
                      Section
                      <select
                        aria-label="Filter evidence by section"
                        value={sectionFilter}
                        onChange={(event) =>
                          setEvidenceFilters(event.target.value, flagFilter)
                        }
                      >
                        <option value="">All sections</option>
                        {review.sections.map((item) => (
                          <option key={item.section_name} value={item.section_name}>
                            {sectionLabel(item.section_name)} ({sectionCounts.get(item.section_name) ?? 0})
                          </option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Flag
                      <select
                        aria-label="Filter evidence by flag"
                        value={flagFilter}
                        onChange={(event) =>
                          setEvidenceFilters(sectionFilter, event.target.value)
                        }
                      >
                        <option value="">All flags</option>
                        {flagOptions.map((item) => (
                          <option key={item.flag} value={item.flag}>
                            {item.label}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                  {(sectionFilter || flagFilter) && (
                    <button
                      className="clear-evidence-filters"
                      type="button"
                      onClick={() => setEvidenceFilters("", "")}
                    >
                      Clear filters
                    </button>
                  )}
                  <div className="evidence-controls">
                    <button
                      type="button"
                      onClick={() => moveEvidence(-1)}
                      disabled={
                        !filteredEvidence.length ||
                        selectedEvidenceId === filteredEvidence[0]?.id
                      }
                    >
                      ← Previous
                    </button>
                    <span>
                      {selectedEvidenceId &&
                      filteredEvidence.some((item) => item.id === selectedEvidenceId)
                        ? `${filteredEvidence.findIndex((item) => item.id === selectedEvidenceId) + 1} / ${filteredEvidence.length}`
                        : `${filteredEvidence.length} of ${review.evidence.length} phrases`}
                    </span>
                    <button
                      type="button"
                      onClick={() => moveEvidence(1)}
                      disabled={
                        !filteredEvidence.length ||
                        selectedEvidenceId === filteredEvidence.at(-1)?.id
                      }
                    >
                      Next →
                    </button>
                  </div>
                  {review.evidence.length === 0 ? (
                    <p className="no-evidence">
                      No unsuppressed flag phrases were detected in the
                      extracted sections.
                    </p>
                  ) : filteredEvidence.length === 0 ? (
                    <p className="no-evidence">
                      No phrases match these filters.
                    </p>
                  ) : (
                    <div className="evidence-groups">
                      {review.sections.map((item) => {
                        const groups = evidenceGroups.filter(
                          (group) => group.section === item.section_name,
                        );
                        if (!groups.length) return null;
                        return (
                          <div
                            className="evidence-group"
                            key={item.section_name}
                          >
                            <div className="group-heading">
                              <span>{sectionLabel(item.section_name)}</span>
                              <span>
                                {groups.reduce(
                                  (count, group) => count + group.hits.length,
                                  0,
                                )}
                              </span>
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
                                      aria-current={
                                        selectedEvidenceId === hit.id
                                          ? "true"
                                          : undefined
                                      }
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
                </div>
              </aside>
            </div>
          </main>
          <footer className="footer">
            <span>
              Scores describe filing language, not an investment recommendation.
            </span>
            <details>
              <summary>Method details</summary>
              <span>
                {review.versions.scoring_model_version} ·{" "}
                {review.versions.parser_version}
              </span>
            </details>
          </footer>
        </>
      )}
    </div>
  );
}
