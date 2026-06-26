# Quickstart: OpenBB Workspace

Score a filing in OpenBB Workspace in under five minutes.

**Audience:** Analysts using [OpenBB Workspace](https://pro.openbb.co) with a local `disclosure-alpha-api` backend.
**Before you start:** {doc}`installation` (`[api,mcp]` extras). For live EDGAR scoring, also {doc}`sec-edgar-setup`.

## Summary

Install the API extra, start `disclosure-alpha-api`, connect Workspace to `http://127.0.0.1:8000`, and run the **Disclosure Company** widget. Use `demo=1` first (no SEC), then switch to live ticker scoring.

## Demo path (no EDGAR)

**Goal:** Confirm the widget works before connecting Workspace.

```bash
pip install "disclosure-alpha[api,mcp]"
disclosure-alpha-api
```

Open `http://127.0.0.1:8000/openbb/company?demo=1` in a browser — you should see an HTML score card with flags and section changes (sample data).

### What you should see

An overall disclosure risk score, nine headline components, active flags, and section changes.

## Connect OpenBB Workspace

**Goal:** Run the Company widget from Workspace. **Use Chrome** and `127.0.0.1` (not `0.0.0.0`).

1. Sign in to [OpenBB Workspace](https://pro.openbb.co).
2. **Apps → Connect backend**
3. URL: `http://127.0.0.1:8000` (match your `PORT` if overridden)
4. Click **Test** or **Add** — watch the API terminal for `GET /widgets.json`.
5. **My Apps → Disclosure Alpha → Company** — set ticker, fiscal year, and form type.
6. Set widget param **`demo`** to `1` for the first Run (fast, no SEC).
7. Clear **`demo`**, set `SEC_USER_AGENT`, and click **Run** again for live EDGAR.
8. In the **Disclosure Alpha** app, connect **Disclosure Alpha Analyst** MCP when prompted for Copilot tools.

```bash
export SEC_USER_AGENT="YourName your@email.com"
disclosure-alpha-api
```

**10-Q:** set **Quarter** to `Q1`, `Q2`, or `Q3` (required). Leave blank for **10-K**.

### How to read it

The widget shows the same deterministic scores as the CLI and HTTP matrix:

- **Overall score** — headline 0–100 disclosure risk; see {doc}`understanding-scores`
- **Components** — nine headline-weighted scores plus specificity
- **Active flags** — phrase-pattern hits grouped by section
- **Section changes** — YoY (10-K) or QoQ (10-Q) vs the prior comparable filing

### If something looks wrong

- **Test shows 500 but the demo URL works in a browser** — Chrome Local Network Access or Safari blocking localhost; see {doc}`../guides/openbb/index`.
- **Slow first Run** — cold EDGAR fetch and parse; repeat Runs on the same ticker are faster.
- **422 on 10-Q** — quarter param missing.

Full troubleshooting: {doc}`../guides/openbb/index`.

## Related

- {doc}`../guides/openbb/index` — connect flow and troubleshooting
- {doc}`choose-your-surface`
- {doc}`installation`
