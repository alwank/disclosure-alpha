export interface Filing {
  ticker: string;
  cik: string;
  accession_number: string;
  form_type: string;
  fiscal_year: number;
  quarter: string | null;
  filing_date: string;
  report_date: string | null;
  prior_accession_number: string | null;
  source_url?: string;
}

export interface ReviewSection {
  section_name: string;
  cleaned_text: string;
  word_count: number;
  extraction_confidence: number;
  parser_version: string;
  warnings: string[];
  reading_blocks?: Array<{ start: number; end: number; kind: "paragraph" | "heading" }>;
}

export interface Evidence {
  id: string;
  section: string;
  flag: string;
  label: string;
  pattern: string;
  matched_text: string;
  start: number;
  end: number;
  sentence_start?: number | null;
  sentence_end?: number | null;
  sentence: string;
}

export interface ComponentRow {
  key: string;
  label: string;
  weight_pct: number;
  score: number | null;
}

export interface Provenance {
  score_name: string;
  value: number | null;
  inputs: Record<string, unknown>;
  source: string;
}

export interface SectionChangeDrivers {
  added_sentence_count: number;
  removed_sentence_count: number;
  changed_numeric_count: number;
  new_topics: string[];
  intensified_topics: string[];
  removed_topics: string[];
  language_deltas: Record<string, number>;
  confidence_score: number;
}

export interface Review {
  filing: Filing;
  scores: {
    overall_disclosure_risk_score: number | null;
    score_coverage_ratio: number;
    confidence_score: number;
    missing_components: string[];
    components: Record<string, number | null>;
    provenance: Provenance[];
  };
  sections: ReviewSection[];
  active_flags: Array<{ section: string; flag: string; label: string }>;
  evidence: Evidence[];
  changes: {
    change_score: { value: number | null; missing_reason: string | null };
    section_drivers: Record<string, SectionChangeDrivers>;
  };
  display: {
    headline_rows: ComponentRow[];
    section_labels: Record<string, string>;
    flag_summary: Array<{
      flag: string;
      label: string;
      tier: string;
      section_count: number;
    }>;
    change_rows: Array<{
      section: string;
      section_label: string;
      change_score: number | null;
      top_delta_name: string | null;
      top_delta_value: number | null;
    }>;
  };
  versions: Record<string, string>;
}

export interface ReviewQuery {
  ticker: string;
  fiscalYear: string;
  formType: "10-K" | "10-Q";
  quarter: "" | "Q1" | "Q2" | "Q3";
}
