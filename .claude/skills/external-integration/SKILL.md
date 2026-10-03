---
name: external-integration
description: Use before writing or reviewing code that calls any third-party library, API, or tool — LLM vendor SDKs, cloud-provider clients (AWS/GCP/Azure), datastore clients (Postgres, BigQuery, Mongo), messaging clients (Kafka, Slack), or any httpx/requests integration with a non-trivial external API. Read the current official docs first (Context7 / WebFetch) instead of trusting training data. Also triggers when tempted to assume "a 200 means success" or "X can never happen". Skip only for the Python stdlib and pure utility libraries with no network surface.
---

# External Integration — verify against current docs

**Before writing code that calls any library, API, or tool: read the current official docs first.** Do not trust training data — use Context7 (`resolve-library-id` → `query-docs`) or `WebFetch` to pull current documentation. Check response schemas, recommended patterns, and configuration options.

## Why this matters

Training data has a cut-off. Library APIs evolve. The recommended pattern from your training era is often deprecated, renamed, or quietly superseded:

- **Parameter renames** that compile fine but behave differently (`response_format` vs `text_format`, `messages=[]` vs `instructions=` + `input=`).
- **Result-extraction path moves** between releases.
- **Endpoints added or removed**; **auth flows change** (env-var names, scope strings, header conventions).

If you write from memory and it happens to work on a 200, you've still likely missed newer streaming / tool-use / structured-output features, quiet behaviour changes (default parameter values, error semantics), and type-stub mismatches.

## How to verify

1. **Context7 first** for documented libraries: `resolve-library-id "<name>"` → `query-docs <id> "<targeted question, with version>"`.
2. **`WebFetch`** for first-party docs pages, changelogs, migration guides, deprecation notices.
3. **Inspect installed types** as a tie-breaker: `inspect.signature(client.<resource>.<method>)`, `Model.model_fields`, `dir(module)` — the SDK in your `.venv` is the source of truth.
4. **Don't infer from cached examples** — the same SDK can change minor-version conventions.

For LLM vendor SDKs, read the vendor's current official SDK reference, not a remembered one.

## A 200 is not a success

Always read the response body. Check the `errors` field, the `status` enum, the `refusal` field, the partial output. LLM APIs routinely return 200 with refusals or empty parses; cloud APIs return 200 with `Errors: [...]` arrays. Never short-circuit on status code alone.

## "X can never happen" is a hypothesis, not a fact

A claim that a whole *class* of failure is impossible — "server-side fetches never hit CORS", "this path can't deadlock", "ordering is guaranteed here" — is the highest-value thing to test, not trust, precisely because the code is built assuming it. Treat such claims the same whether they come from your own reasoning, a teammate, or an inherited research note: write the one cheap probe that would falsify it before relying on it. (Observed: an inherited note asserted SvelteKit's server-side `load` fetches "never" hit CORS; Node's undici enforces CORS server-side, and the assumption cost a debugging cycle — a 30-second curl would have caught it.)
