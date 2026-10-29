# One approved Nemotron continuity test — PASS

Date: 2026-10-29. One paid inference; no retry.

## User flow
The browser saved a launch-brief checkpoint, navigated away, saved a changed budget, navigated away again, then recovered both records. The user-facing button sent that recovered state to the existing Nebius NVIDIA Nemotron model and displayed its actual response.

Model: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`.
HTTP: 200. Inference latency: 1192.4 ms.

Actual proposed next step: **Review the updated budget with Ivo.**
The summary preserved the new **500 EUR** budget and unchanged **Friday** launch. Citations E1 and E2 match the saved checkpoint and update. No action was executed or falsely marked verified. This is one synthetic user scenario, not general accuracy evidence.

## Consumption and budget
- Provider usage: 179 input + 72 output = 251 tokens.
- Catalog rates: 0.06 USD / million input; 0.24 USD / million output.
- Calculated token charge: **0.00002802 USD**.
- Conservative preflight bound: 0.00038808 USD; approval ceiling: 1 USD.
- Token charge is calculated from provider usage and published prices, not an account invoice readback.

Source: https://tokenfactory.nebius.com/api/public/models_info

## Evidence
`NEMOTRON_CONTINUATION_LIVE.json`: request, persisted state, actual raw response, provider ID/model, usage, limits and validation.
`LIVE_UI_E2E.json`: browser workflow and displayed actual model answer.
`NEMOTRON_SINGLE_CALL.claim`: exclusive call-consumption record; preserve it to prevent another call.
`../video/AWM-Continue-Live.webm`: actual uninterrupted browser capture including the live inference.

No credential was printed or included in evidence. A private process used the existing configured account credential; no key was passed through conversation content.

## Remaining gates
The owner subsequently approved MIT licensing of project-authored code and public hack publication. No further paid inference is approved. Historical A/B/C results remain unchanged. Full rotational longitudinal architecture remains untested.

