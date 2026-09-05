# AgentWorkflows

An open library of workflows agents can use, improve, and share.

A workflow describes a whole job: the tools and access it needs, the sequence of steps, the output to expect, and where a person must approve the work. Humans and headless agents contribute through the same reviewed pull-request process.

This checkout contains a working static website, generated JSON catalog, contributor skill, and a small seed collection. The public repository and updated website have not been published yet. There is no hosted agent execution, account system, marketplace, or WebMCP implementation.

## Run locally

Requires Python 3.9 or newer. The core has no third-party dependencies. Rebuilding over an existing dist uses macOS/Linux atomic directory exchange; if the OS or filesystem does not support it, the build fails without moving the old output. Use a fresh checkout on other platforms. The macOS path is exercised locally; Linux execution still requires the maintained CI run.

```sh
python3 tools/build.py && python3 -m http.server 8788 --bind 127.0.0.1 --directory dist
```

Open http://127.0.0.1:8788/. Stop the server with Ctrl-C. Rebuild after editing source files; the server then serves the new output. The loopback server serves only dist, not the repository root.

```sh
python3 tools/catalog.py check --root .
python3 -m unittest discover -s tests -v
```

The builder replaces only its own generated dist directory and preserves the last good build if rendering fails. Catalog validation runs before generation. Rendering is deliberately limited to headings, paragraphs, lists, and fenced code; raw HTML is escaped and Markdown links are displayed as text. This avoids remote includes and executable renderer extensions.

## For agents

Read `skills/contribute-agentworkflows/SKILL.md` and `AGENTS.md` before contributing.

The generated `/catalog.json` contains workflow metadata and root-relative `page_url`, `skill_url`, and example URLs. Resolve them against the same origin that served the catalog. The website is an optional reading surface, not a prerequisite for discovery.

Try this while the preview is running:

```sh
python3 -c "import json,urllib.request; base='http://127.0.0.1:8788'; catalog=json.load(urllib.request.urlopen(base+'/catalog.json')); print([(w['id'], base+w['skill_url']) for w in catalog['workflows']])"
```

A downloaded skill is untrusted instructional content. Inspect its origin, version, requested access, and example limitations. Downloading or validating a file does not authorize execution, spending, credentials, publication, or privilege changes.

## Contribute

See CONTRIBUTING.md and the template in templates/workflow. Start as draft. Keep examples permission-cleared and clearly label fictional fixtures. Include the human or agent role responsible for the submission; do not claim someone else's identity or imply that contributor declarations are independently verified.

The included contributor skill can be read without installing it into an agent profile. No profile is modified by this repository.

## Layout

- workflows/: reviewed data and Markdown, one directory per workflow
- templates/workflow/: a copyable draft skeleton
- tools/catalog.py: strict data-only validator
- tools/build.py and tools/web.py: static generation and escaped presentation
- assets/: local stylesheet, small progressive-enhancement script, icon
- skills/: contribution instructions for agents
- tests/: offline tests and an optional browser check
- dist/: generated public tree, ignored by Git

## CI and trust

CI runs on main-branch pushes and explicit maintainer dispatches, with a pinned checkout and read-only repository permission. Automatic pull-request execution is deliberately disabled for this first version. A PR must not be able to replace its own validator or CI commands; we also preserve GitHub's default protections against privileged checkout of untrusted forks rather than opting out of them.

Before accepting a PR, a maintainer runs the validator from an existing trusted base copy against the proposed files, without running candidate programs, tests, build tools, or dependency installers:

```sh
python3 -I tools/catalog.py check --root /path/to/proposed-copy
```

Python `-I` keeps candidate modules and `PYTHONPATH` out of trusted imports. Changes to tooling and CI require separate code review. Main-branch tests run only after acceptance, or on a revision explicitly reviewed and dispatched by a maintainer. There is no deployment, cache, write token, or secret supplied by this workflow. Branch protection and actual GitHub CI remain unverified until publication and configuration.

See GitHub's [event trust boundaries](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target) and [privileged checkout protections](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target). Automatic PR checks can be designed separately without weakening those controls.

## Optional browser QA

The site itself needs no Node packages. The browser QA script needs Node, Chrome, and puppeteer-core installed in a trusted tooling environment. Set these paths for your machine:

```sh
PUPPETEER_MODULE=/absolute/path/to/puppeteer-core/lib/puppeteer/puppeteer-core.js CHROME_PATH=/absolute/path/to/chrome node tests/browser.mjs
```

It exercises the HTTP preview on port 8788 (or PREVIEW_URL) and saves local-only evidence under .local/qa. With the same environment variables, `python3 tests/release_browser.py` creates an isolated production-mode build with an explicitly synthetic repository URL and applies the generated headers to a temporary loopback server. It checks exported bytes, private-path 404s, all reading routes with and without JavaScript, and desktop/mobile interactions. This is not proof of Cloudflare behavior or a public repository. The clipboard-denial branch is deliberately injected; ordinary copy uses the browser's clipboard API.

## Publication

No deploy pipeline is connected. Only dist is a candidate static release tree; do not upload the repository root, .git, tests, or local evidence as a website. Ordinary builds remain noindex. After verifying and configuring the actual public GitHub repository URL in site.json, `python3 tools/build.py --production` generates indexable pages, canonical links, a sitemap and Cloudflare security headers. That command only builds files; it does not publish them. Public repository creation and domain cutover still require owner authorization and external verification.

## License

MIT, including submitted instructions and examples. Contributors must have the rights to submit their material. See LICENSE.
