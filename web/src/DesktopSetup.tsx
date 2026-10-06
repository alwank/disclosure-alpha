import { useState, type FormEvent } from "react";
import { saveDesktopSettings } from "./api";

type Props = {
  onComplete: () => void;
};

export function DesktopSetup({ onComplete }: Props) {
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    void saveDesktopSettings({ displayName, email })
      .then(() => onComplete())
      .catch((cause: unknown) =>
        setError(
          cause instanceof Error
            ? cause.message
            : "Could not save the SEC contact details.",
        ),
      )
      .finally(() => setSaving(false));
  }

  return (
    <main className="desktop-setup">
      <section className="desktop-setup-card" aria-labelledby="setup-title">
        <p className="eyebrow">One-time setup</p>
        <h1 id="setup-title">Set up SEC filing access</h1>
        <p>
          The SEC requires a contact name and email with each live EDGAR
          request. These details stay on this Windows account and are used only
          as the application&apos;s SEC User-Agent.
        </p>
        <form onSubmit={submit}>
          <label>
            Your name
            <input
              autoComplete="name"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              maxLength={120}
              required
            />
          </label>
          <label>
            Contact email
            <input
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              maxLength={254}
              required
            />
          </label>
          {error && <p className="setup-error" role="alert">{error}</p>}
          <button className="run-button" type="submit" disabled={saving}>
            {saving ? "Saving…" : "Continue to filing review"}
          </button>
        </form>
      </section>
    </main>
  );
}
