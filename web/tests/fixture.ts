import type { Evidence, Review } from "../src/types";

const riskText =
  "We received a subpoena from the SEC. A regulatory investigation is ongoing.";
const controlText =
  "Management identified a material weakness. Another material weakness remains.";

function hit(
  section: string,
  flag: string,
  label: string,
  text: string,
  phrase: string,
  occurrence = 0,
): Evidence {
  let start = -1;
  for (let index = 0; index <= occurrence; index += 1)
    start = text.indexOf(phrase, start + 1);
  const sentenceStart = text.lastIndexOf(".", start) + 1;
  const sentenceEnd = text.indexOf(".", start) + 1;
  return {
    id: `${section}:${flag}:${start}-${start + phrase.length}`,
    section,
    flag,
    label,
    pattern: phrase,
    matched_text: phrase,
    start,
    end: start + phrase.length,
    sentence_start: sentenceStart,
    sentence_end: sentenceEnd,
    sentence: text.slice(sentenceStart, sentenceEnd).trim(),
  };
}

export function makeReview(): Review {
  const evidence = [
    hit(
      "item_1a_risk_factors",
      "investigation_flag",
      "Investigation",
      riskText,
      "subpoena",
    ),
    hit(
      "item_9a_controls",
      "material_weakness_flag",
      "Material Weakness",
      controlText,
      "material weakness",
    ),
    hit(
      "item_9a_controls",
      "material_weakness_flag",
      "Material Weakness",
      controlText,
      "material weakness",
      1,
    ),
  ];
  return {
    filing: {
      ticker: "AAPL",
      cik: "0000320193",
      accession_number: "0000320193-25-000079",
      form_type: "10-K",
      fiscal_year: 2025,
      quarter: null,
      filing_date: "2025-10-31",
      report_date: "2025-09-27",
      prior_accession_number: null,
      source_url:
        "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl.htm",
    },
    scores: {
      overall_disclosure_risk_score: 37.42,
      score_coverage_ratio: 0.7778,
      confidence_score: 0.68,
      missing_components: ["disclosure_change_score", "event_severity_score"],
      components: {
        risk_factor_intensity_score: 43.2,
        disclosure_change_score: null,
      },
      provenance: [
        {
          score_name: "risk_factor_intensity_score",
          value: 43.2,
          source: "deterministic",
          inputs: {
            negative_word_ratio: {
              value: 0.05,
              section: "item_1a_risk_factors",
            },
          },
        },
      ],
    },
    sections: [
      {
        section_name: "item_1a_risk_factors",
        cleaned_text: riskText,
        word_count: 13,
        extraction_confidence: 0.9,
        parser_version: "section_extractor_v1",
        warnings: [],
        reading_blocks: [{ start: 0, end: riskText.length, kind: "paragraph" }],
      },
      {
        section_name: "item_9a_controls",
        cleaned_text: controlText,
        word_count: 10,
        extraction_confidence: 0.8,
        parser_version: "section_extractor_v1",
        warnings: [],
        reading_blocks: [{ start: 0, end: controlText.length, kind: "paragraph" }],
      },
    ],
    active_flags: [
      {
        section: "item_1a_risk_factors",
        flag: "investigation_flag",
        label: "Investigation",
      },
      {
        section: "item_9a_controls",
        flag: "material_weakness_flag",
        label: "Material Weakness",
      },
    ],
    evidence,
    changes: {
      change_score: {
        value: null,
        missing_reason: "no prior filing comparison available",
      },
    },
    display: {
      headline_rows: [
        {
          key: "risk_factor_intensity_score",
          label: "Risk-factor tone & volatility",
          weight_pct: 20,
          score: 43.2,
        },
        {
          key: "disclosure_change_score",
          label: "Year-over-year disclosure change",
          weight_pct: 15,
          score: null,
        },
        {
          key: "mdna_uncertainty_score",
          label: "MD&A uncertainty & demand stress",
          weight_pct: 15,
          score: 20,
        },
        {
          key: "legal_regulatory_risk_score",
          label: "Legal & regulatory risk language",
          weight_pct: 10,
          score: 30,
        },
        {
          key: "liquidity_stress_score",
          label: "Liquidity & covenant stress",
          weight_pct: 10,
          score: 14,
        },
        {
          key: "boilerplate_risk_score",
          label: "Boilerplate & vague risk language",
          weight_pct: 10,
          score: 25,
        },
        {
          key: "internal_controls_risk_score",
          label: "Internal controls weakness signals",
          weight_pct: 5,
          score: 60,
        },
        {
          key: "event_severity_score",
          label: "Material event severity (diff-only)",
          weight_pct: 5,
          score: null,
        },
        {
          key: "tone_negativity_score",
          label: "Cross-section negative tone",
          weight_pct: 5,
          score: 42,
        },
      ],
      section_labels: {
        item_1a_risk_factors: "Item 1A Risk Factors",
        item_9a_controls: "Item 9A Controls",
      },
      flag_summary: [
        {
          flag: "material_weakness_flag",
          label: "Material Weakness",
          tier: "critical",
          section_count: 1,
        },
        {
          flag: "investigation_flag",
          label: "Investigation",
          tier: "elevated",
          section_count: 1,
        },
      ],
      change_rows: [],
    },
    versions: {
      scoring_model_version: "deterministic_scoring_v2",
      parser_version: "section_extractor_v1",
    },
  };
}
