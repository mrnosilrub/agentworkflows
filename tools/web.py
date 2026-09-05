"""Static presentation. Contributed Markdown is text, never HTML/code."""
from html import escape


SITE_ORIGIN = 'https://agentworkflows.wiki'
SHARE_IMAGE_URL = SITE_ORIGIN + '/assets/share-card.png'
FOUNDER_URL = 'https://eliasburlison.com'
HOMEPAGE_DESCRIPTION = ('An open library of reusable workflows for AI agents. '
                        'Find a job, inspect the steps, and contribute improvements.')


def _default_description(title):
    descriptions = {
        'Contribute a workflow': ('Share a reusable way to finish a job—not a transcript '
                                  'or a list of prompts.'),
        'Not found': 'The requested workflow is not in the AgentWorkflows collection.',
    }
    return descriptions.get(title, HOMEPAGE_DESCRIPTION)


def _canonical_url(path):
    if not path.startswith('/'):
        path = '/' + path
    return SITE_ORIGIN + path


def _demo_link(demo_url):
    if not demo_url:
        return ''
    return '<a class="text-link" href="' + escape(demo_url, quote=True) + '">See a real run →</a>'


def shell(title, content, repository_url=None, description=None, canonical_path=None):
    repo = ('<a href="' + escape(repository_url, quote=True) + '">GitHub ↗</a>'
            if repository_url else '<span class="muted">Repository not published</span>')
    notice = '' if repository_url else '<div class="local-note">Local build · not the live website</div>'
    description = _default_description(title) if description is None else description
    canonical_path = canonical_path or {
        'Contribute a workflow': '/contribute/',
        'Not found': '/404.html',
    }.get(title, '/')
    canonical_url = _canonical_url(canonical_path)
    metadata = (
        '<meta name="description" content="' + escape(description, quote=True) + '">\n'
        '<meta property="og:type" content="website">\n'
        '<meta property="og:site_name" content="AgentWorkflows">\n'
        '<meta property="og:title" content="' + escape(title, quote=True) + '">\n'
        '<meta property="og:description" content="' + escape(description, quote=True) + '">\n'
        '<meta property="og:url" content="' + escape(canonical_url, quote=True) + '">\n'
        '<meta property="og:image" content="' + SHARE_IMAGE_URL + '">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        '<meta property="og:image:alt" content="AgentWorkflows — reusable methods for AI agents">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        '<meta name="twitter:title" content="' + escape(title, quote=True) + '">\n'
        '<meta name="twitter:description" content="' + escape(description, quote=True) + '">\n'
        '<meta name="twitter:image" content="' + SHARE_IMAGE_URL + '">\n'
        '<meta name="twitter:image:alt" content="AgentWorkflows — reusable methods for AI agents">'
    )
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">''' + metadata + '''
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'">
<title>''' + escape(title) + ''' · AgentWorkflows</title><link rel="icon" href="/assets/icon.svg"><link rel="stylesheet" href="/assets/site.css"><script src="/assets/site.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a>''' + notice + '''<div class="shell"><header><a class="brand" href="/">agentworkflows<span>.wiki</span></a><nav aria-label="Main"><a href="/#workflows">Workflows</a><a href="/contribute/">Contribute</a>''' + repo + '''</nav></header><main id="main">''' + content + '''</main><footer><span>Open workflows. Shared knowledge. <a href="''' + FOUNDER_URL + '''">Created by Elias Burlison</a></span><nav aria-label="Resources"><a href="/catalog.json">Catalog JSON</a><a href="/llms.txt">For agents</a><a href="/LICENSE.txt">MIT license</a></nav></footer></div></body></html>'''


def homepage(records, repository_url=None, demo_url=None):
    rows = []
    for item in records:
        status = 'Example checked' if item['status'] == 'fixture-tested' else 'Draft guide'
        rows.append('<article class="workflow-row" data-workflow data-category="' + escape(item['category']) + '">'
                    '<div class="row-meta"><span>' + escape(item['category'].title()) + '</span><span class="badge">' + status + '</span></div>'
                    '<h3><a href="/workflows/' + escape(item['id']) + '/">' + escape(item['title']) + ' <span aria-hidden="true">↗</span></a></h3>'
                    '<p>' + escape(item['summary']) + '</p><p class="tags">' + escape(' · '.join(item['tags'])) + '</p></article>')
    categories = sorted({item['category'] for item in records})
    options = ''.join('<option value="' + escape(c) + '">' + escape(c.title()) + '</option>' for c in categories)
    demo_link = _demo_link(demo_url)
    content = '''<section class="hero"><p class="eyebrow">An open library for AI agents</p><h1>Workflows agents can use, improve, and share.</h1><p class="lede">Reusable methods for getting a whole job done—not just a prompt. Find the steps, tools, examples, and places where a person needs to check the work.</p><div class="hero-actions"><a class="button" href="#workflows">Explore workflows ↓</a><a class="text-link" href="/contribute/">Contribute what you’ve learned ↗</a>''' + demo_link + '''</div></section>\n<div class="intro-rule"><p><strong>For people and headless agents.</strong> Read a guide here, fetch its skill file, or discover it through the open catalog.</p><span>No accounts. No hosted execution.</span></div>
<div class="catalog-layout"><section id="workflows" aria-labelledby="collection-title"><div class="section-heading"><h2 id="collection-title">The collection</h2><span id="result-count" role="status">''' + str(len(records)) + ''' workflows</span></div>
<div class="filters" hidden><div><label for="search">Find a job</label><input id="search" type="search" placeholder="Try documentation or release notes" autocomplete="off"></div><div><label for="category">Category</label><select id="category"><option value="">All categories</option>''' + options + '''</select></div></div>
<div id="results">''' + ''.join(rows) + '''</div><p id="empty" class="empty" hidden>No matching workflows. Try another task or clear your filters.</p><p class="small muted">A small seed collection, not a claim of broad compatibility. “Example checked” describes a local fixture check—not a safety certification.</p></section>
<aside class="community"><p class="eyebrow">Leave a useful trail</p><h2>Solved it once?<br>Help the next agent.</h2><p>Package the method, add an example, and propose an improvement. Human and agent contributions follow the same review process.</p><a class="text-link" href="/contribute/">How to contribute →</a><div class="agent-box"><h3>Start without a browser</h3><p>Read the catalog and follow each workflow’s skill URL.</p><a href="/catalog.json">/catalog.json</a><br><a href="/contribute/SKILL.md">Contributor skill ↗</a></div></aside></div>'''
    return shell('Workflows agents can use, improve, and share', content, repository_url,
                 description=HOMEPAGE_DESCRIPTION, canonical_path='/')



def workflow_page(item, repository_url=None, demo_url=None):
    base = '/workflows/' + item['id'] + '/'
    checked = item['status'] == 'fixture-tested'
    status = 'Example checked' if checked else 'Draft guide'
    note = ('A local example check is recorded. It does not establish general compatibility or safety.'
            if checked else 'Draft guidance, not a safety certification. Read the example labels and any recorded run limitations before use.')
    evidence = ('<a href="' + base + 'evidence/run.json">Read the example-check record →</a>' if checked else '')
    facts = ''.join('<section><h3>' + label + '</h3><ul>' + ''.join('<li>' + escape(x) + '</li>' for x in item[key]) + '</ul></section>'
                    for key, label in [('requirements', 'What you need'), ('permissions', 'Access requested'), ('outputs', 'What you get')])
    content = '<a class="back" href="/#workflows">← All workflows</a><section class="detail-heading"><p class="eyebrow">' + escape(item['category']) + ' · ' + escape(item['version']) + '</p><h1>' + escape(item['title']) + '</h1><p class="lede">' + escape(item['summary']) + '</p><div class="status-note"><span class="badge">' + status + '</span><p>' + note + '</p>' + evidence + '</div></section>'
    content += '<div class="detail-layout"><article class="prose">' + markdown(item['instructions']) + '<section id="examples"><h2>See the example</h2><p class="muted">Read the input beside the expected shape of the result. Check the labels for what was actually executed.</p>' + _demo_link(demo_url) + '<details><summary>Example input</summary>' + markdown(item['example_input']) + '<a href="' + base + 'examples/input.md">Read input Markdown ↗</a></details><details><summary>Example output</summary>' + markdown(item['example_output']) + '<a href="' + base + 'examples/output.md">Read output Markdown ↗</a></details></section></article>'
    content += '<aside class="workflow-aside"><div class="use-box"><h2>Use this workflow</h2><p>Inspect the instructions and permissions before adding it to your agent. Downloading does not grant permission to execute it.</p><a class="button" href="' + base + 'SKILL.md" download>Download skill ↓</a><div class="copy-tools" hidden><button class="secondary" data-copy="skill-text">Copy skill text</button><p class="copy-status" role="status"></p></div><details><summary>View skill text</summary><textarea id="skill-text" aria-label="Workflow skill text" readonly spellcheck="false">' + escape(item['instructions']) + '</textarea></details><a href="#examples">See input and output ↓</a></div>' + facts + '<section><h3>Declared authors</h3><p>' + escape(', '.join(item['authors'])) + '</p><p class="small muted">Attribution is contributor-declared, not identity verification.</p><a href="' + base + 'workflow.json">Workflow metadata ↗</a></section><a href="/contribute/">Improve this workflow →</a></aside></div>'
    return shell(item['title'], content, repository_url, description=item['summary'],
                 canonical_path=base)


def markdown(text):
    """Small documented subset: headings, paragraphs, lists, fenced code.

    Raw HTML and Markdown links stay escaped text. No external renderer/plugins.
    """
    import re
    lines = text.splitlines()
    if lines and lines[0] == '---' and '---' in lines[1:]:
        lines = lines[lines[1:].index('---') + 2:]
    out, paragraph, code, items = [], [], [], []
    in_code, list_tag = False, None

    def flush_paragraph():
        if paragraph:
            out.append('<p>' + escape(' '.join(paragraph)) + '</p>')
            paragraph.clear()

    def flush_list():
        nonlocal list_tag
        if items:
            out.append('<' + list_tag + '>' + ''.join('<li>' + escape(x) + '</li>' for x in items) + '</' + list_tag + '>')
            items.clear()
        list_tag = None

    for line in lines:
        if line.startswith('```'):
            flush_paragraph()
            flush_list()
            if in_code:
                out.append('<pre><code>' + escape('\n'.join(code)) + '</code></pre>')
                code.clear()
            in_code = not in_code
        elif in_code:
            code.append(line)
        elif not line.strip():
            flush_paragraph()
            flush_list()
        elif re.match(r'^#{1,6} ', line):
            flush_paragraph()
            flush_list()
            level = min(len(line) - len(line.lstrip('#')), 6)
            # A workflow's own H1 is subordinate to the page's title.
            level = max(2, level)
            out.append('<h{0}>{1}</h{0}>'.format(level, escape(line.lstrip('#').strip())))
        elif line.startswith('- ') or re.match(r'^\d+\. ', line):
            flush_paragraph()
            kind = 'ul' if line.startswith('- ') else 'ol'
            if list_tag and list_tag != kind:
                flush_list()
            list_tag = kind
            items.append(line[2:] if kind == 'ul' else line.split('. ', 1)[1])
        else:
            flush_list()
            paragraph.append(line)
    if in_code:
        out.append('<pre><code>' + escape('\n'.join(code)) + '</code></pre>')
    flush_paragraph()
    flush_list()
    return ''.join(out)
