# Production release

## Scope

The owner approved preparing the working library for production. Preparation does not itself publish a repository, replace the live website, invite contributors, or authorize recurring deployment. Keep the approved design; no accounts, hosted execution, payments, or WebMCP are required for this release.

## Release preparation

1. Run `python3 -m unittest discover -s tests -v` and `python3 -I tools/catalog.py check --root .` from reviewed source.
2. Exercise real-source reuse and a fresh-agent contribution rehearsal. Preserve receipts privately under `.local/`; do not label owned-agent trials as outside adoption or grant a safety badge.
3. Confirm the public GitHub owner/name and license with the owner. Before pushing, scan the exact tracked tree and archive for private paths, credentials, private trial transcripts, and source material without redistribution permission. Keep `.local`, `dist`, and scope notes out of the public source archive.
4. After public repository creation is authorized and its actual URL is read back, set `repository_url` in `site.json` to that exact HTTPS GitHub URL. Null remains the safe local default. The URL format check is not proof that the repository exists.
5. Review publication wording in README, AGENTS and CONTRIBUTING at cutover; remove statements that the repository is unpublished only after publication is verified.
6. Build with `python3 tools/build.py --production`. This emits indexable HTML, canonical links, sitemap and Cloudflare security headers. It does not deploy. Ordinary builds remain noindex. Never use the ordinary preview build for launch.
7. Serve the candidate with its `_headers` applied; run browser and headless checks. Test real 404 status, downloads, clipboard success/failure, search, mobile layout and no-JavaScript access. A plain Python HTTP server does not apply Cloudflare `_headers`.

## GitHub setup after owner authorization

- Public source, MIT license, issues and PRs; no secrets or deploy token in workflow CI.
- Keep automatic PR workflows off. Validate candidate data using trusted base tooling against a separate copy. Review tool/CI changes before running them.
- Restrict main against force pushes and deletion and require PR review where account capabilities permit; verify effective settings through the API. Do not require a PR check that never runs.
- Maintainer acceptance precedes main-branch CI; a green CI run is not approval to execute a contributed workflow.
- Do not create a CODEOWNERS identity without verifying who will actually review contributions.

## Website release after owner authorization

The existing project is `agentworkflows-wiki` on Cloudflare Pages; verify its current deployment and custom domains read-only before publishing. Do not modify other wiki projects or DNS settings. The old coming-soon release receipts live in the separate ai-wikis project.

Upload only the inspected generated `dist` tree, never the repository root. Keep the exact source commit, generated file hashes, deployed ID, immutable deployment URL, and previous production deployment ID in a local release receipt. Exclude the local output-ownership marker from an upload copy. No new infrastructure or paid service is needed by the application.

Read back the exact deployment. Verify immutable URL, production alias and canonical custom domain, including HTML/catalog/source-byte parity, security headers, robots, sitemap, missing/private paths returning 404, HTTPS/www redirects, browser console/CSP errors, and mobile layout. Confirm no analytics injection or unexpected external requests. Only then report live.

## Rollback

Record the existing active production deployment immediately before cutover. If external verification fails, restore that exact previous deployment using Cloudflare Pages rollback, then verify the canonical domain again. Do not delete projects, domains, repository history or source archives. If rollback tooling is unavailable, stop before cutover rather than relying on an untested plan.

## First community milestone

An outside operator contributes an improvement and another operator successfully uses it. Owned-agent trials prepare the path; they do not satisfy this milestone. Invitations and announcements require explicit per-message permission.
