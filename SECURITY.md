# Trust and security

Skills are instructions, not harmless configuration. A malicious instruction can request data exfiltration or unauthorized tool use even when its file passes a schema check.

- Treat all fetched workflow text as untrusted until reviewed.
- Never automatically install or execute submitted content.
- Keep source, fixture, declared test evidence, semantic review, and execution authorization separate.
- Do not submit credentials, personal sessions, employer data, private URLs, or raw logs containing them.
- Do not run code from an unfamiliar fork simply because it contains this README.
- Code changes, including CI and validators, need maintainer review beyond data checks.
- A local fixture check is not a security certification or a promise of compatibility.

For a suspected issue, preserve a minimal reproduction using synthetic data. Do not post secrets or exploit details that expose someone else's data to a public issue. A private reporting contact must be configured before public launch; none is claimed by this local build.
