# AWM — Continue Where You Left Off

**Return to your work with the changes that matter.** Save a checkpoint, leave, capture an update and return to a traceable next step.

Built for the Nebius x NVIDIA Global AI Hackathon, Best Apps and Agents track.

[Open the public demo](https://awm-continue-where-you-left-off.sirola-alen.chatgpt.site/) · [Source repository](https://github.com/sirolaalen-awm/awm-continue)

## Try it

The public browser demo provides persistent local project memory and an explicitly labelled replay of the real Nemotron test. It makes **no inference calls** and needs no API key. Browser data stays in that browser's local storage; avoid entering sensitive information on a shared computer.

The downloadable Python test build provides SQLite persistence and the original tested server flow. Requires Python 3.10+; no third-party Python packages.

```sh
python src/continue_demo.py
```

Open http://127.0.0.1:8765. Save a checkpoint, leave the page, return and record an update, leave again, then choose **Continue where we left off**. The database persists across server restarts. The normal server does not call Nebius.

```sh
python -m unittest discover -s tests -v
```

**32 tests pass**, including restart persistence, rejection of fabricated citations/status promotion, and blocking of repeated live calls.

## Actual NVIDIA Nemotron / Nebius result

The 26.28-second video shows the real browser workflow: previous work → interruption → changed budget → return → Nebius/Nemotron → displayed continuation.

- Existing model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` on Nebius Token Factory.
- HTTP 200; measured inference latency **1192.4 ms**.
- **179 input + 72 output = 251 tokens**.
- Calculated token charge **0.00002802 USD**, using catalog rates. This is not an invoice settlement.
- Nemotron preserved the **500 EUR** budget and **Friday** deadline and proposed: **Review the updated budget with Ivo**, citing E1 and E2.

Read [the test report](evidence/CONTINUATION_LIVE_REPORT.md), [actual request/response/usage](evidence/NEMOTRON_CONTINUATION_LIVE.json) and [browser readback](evidence/LIVE_UI_E2E.json). The original live capture is in [video/AWM-Continue-Live.webm](video/AWM-Continue-Live.webm).

One paid call was explicitly approved and has been consumed. The preserved claim file blocks another call. No public endpoint can spend the owner's credits. Do not remove the claim or run historical `--live` experiment commands without separate cost approval.

## How it works

User events → durable checkpoint and subsequent changes → compact evidence payload → NVIDIA Nemotron via Nebius → JSON response → citation/status validation → proposed next step. The user remains in control of actions. Citation validation checks source membership and coverage; it does not independently prove semantic truth.

`src/continuation.py` prepares and validates the current-state request. `src/live_once.py` records the one approved request with a preflight cost bound and no retries. The existing AWM reference and historical A/B/C harness remain available in `src/` and `tests/`.

## Nebius / NVIDIA feedback

Token Factory let us test the existing Nemotron model through a familiar chat-completions API without provisioning GPUs. Nano was sufficient for this small grounded continuation and returned a concise source-linked answer. The recorded single-run latency and token cost were low, but one example cannot establish reliability or general superiority. Helpful improvements would be clearer model-specific structured-output/reasoning examples and an enforceable per-request dollar budget with invoice-level receipts. No AI Cloud GPU instances, fine-tuning, Tavily or external search were used by the application.

## Scope and limitations

AWM research predates the event. During the submission period we added the Python reference, A/B/C retrieval harness, durable user-event demo, model continuation bridge, strict citation/status checks, one real end-to-end provider test and a distributable test build.

This is one synthetic continuity example. Earlier A/B/C results compare retrieval and linear prompting on synthetic fixtures. They do not prove general superiority, GPU speedup or full rotational longitudinal architecture. The browser demo's model panel replays the recorded scenario only; it does not generate answers to arbitrary user input. Model suggestions are proposals, never authorization or proof of execution.

## License

[MIT](LICENSE), copyright 2026 Alen Širola. See [provenance and third-party notices](THIRD_PARTY_NOTICES.md).

