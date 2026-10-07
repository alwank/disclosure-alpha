# Filing Review UI

The Filing Review UI puts scores, exact flag phrases, and extracted filing text in one view. It supports SEC 10-K and 10-Q ticker filings. Highlighted phrases use the same cleaned section text as the scoring pipeline; **Open original SEC filing** links to the native document.

## Run the packaged UI

```bash
pip install "disclosure-alpha[api]"
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha-api
```

Open `http://127.0.0.1:8000/app/`. Enter a ticker, fiscal year, and form; 10-Q also needs Q1, Q2, or Q3. The overview ranks section changes by magnitude, shows the nine weighted component scores, and counts matched flag phrases. Select a change bar to read the current section alongside detected sentence, topic, numeric, and language-shift drivers. Change selection does not mark passages as a text diff. Select a component for score inputs, or a flag or evidence hit to highlight its exact phrase. Text search uses a separate highlight color and does not affect scores.

The reader's section rail shows matched-phrase counts on wide screens; the section selector remains on narrower screens. In **Marked language**, filter hits by section and flag together, then use Previous and Next to move through the filtered hits. Text search covers the open section. Use its arrows, Enter, or Shift+Enter to move between matches; navigation wraps at the ends. Search and evidence highlights remain separate.

The API and OpenBB discovery remain available at their existing paths. The UI calls `GET /v1/company/{ticker}/filing-review`, which returns score provenance, extracted section text, flag evidence spans, and filing metadata from one pipeline result. The response is compressed when the client accepts gzip.

```{admonition} Interpretation
:class: note

Flag highlights are unsuppressed phrase-pattern matches, not confirmed events. Change bars summarize how much sections changed, not whether the disclosure improved or worsened. Some score components are computed from ratios or filing changes and therefore have no single keyword highlight. Missing component scores are displayed as missing, not zero.
```

## Develop the frontend

From a repository checkout with Node.js 22, use two terminals:

```bash
pip install -e ".[api,dev]"
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha-api
```

```bash
cd web
npm ci
npm run dev
```

Open `http://127.0.0.1:5173/app/`; Vite proxies `/v1` to the local API. `npm run build` places assets in `src/disclosure_alpha/web_assets`, enabling `/app/` on the Python server. Release builds include those assets in the wheel and source archive. Run `npm test` for UI unit tests and `npm run test:e2e` for the fixture-driven browser test.

## API evidence offsets

Each evidence item identifies its section, flag, pattern, matched text, sentence context, and `[start, end)` positions in that section's `cleaned_text`. Offsets count Unicode code points. Clients using UTF-16 strings, including browsers, must convert those positions before slicing or highlighting. The response includes the scoring and parser versions so consumers can identify the analytical model.

The review response also includes optional reading layout metadata. Each section's `reading_blocks` contains source-backed `{start, end, kind}` ranges in the same `cleaned_text`, where `kind` is `paragraph` or `heading`. Evidence items include `sentence_start` and `sentence_end` ranges for grouping matches from one source sentence. These additions do not change `cleaned_text`, scores, or evidence offsets. Clients can render continuous text when layout metadata is absent.

When a prior comparable section exists, `changes.section_drivers` gives detected added and removed sentence counts, numeric token changes, topic changes, signed language deltas in percentage points, and comparison confidence for that section. These drivers summarize the comparison; they do not identify exact changed passages in the reader.
