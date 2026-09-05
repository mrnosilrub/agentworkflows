import unittest
try:
    from tools import web
except ImportError:
    web = None


class RenderingTests(unittest.TestCase):
    def test_markdown_renders_plain_text_without_executing_html(self):
        self.assertIsNotNone(web, 'The safe Markdown renderer is not implemented')
        self.assertEqual(web.markdown('<script>alert(1)</script>'),
                         '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>')


    def test_markdown_handles_document_structure(self):
        result = web.markdown('---\nname: sample\ndescription: sample\n---\n\n## Steps\n\n- Read\n- Check\n\n```sh\n<do-not-execute>\n```')
        self.assertIn('<h2>Steps</h2>', result)
        self.assertIn('<ul><li>Read</li><li>Check</li></ul>', result)
        self.assertIn('<pre><code>&lt;do-not-execute&gt;</code></pre>', result)
        self.assertNotIn('name: sample', result)


    def test_homepage_links_to_workflow(self):
        self.assertTrue(hasattr(web, 'homepage'), 'The catalog homepage is missing')
        item = {'id': 'sample-job', 'title': 'Sample job', 'summary': 'A useful task.',
                'category': 'research', 'status': 'draft', 'tags': ['research']}
        result = web.homepage([item])
        self.assertIn('Workflows agents can use, improve, and share.', result)
        self.assertIn('href="/workflows/sample-job/"', result)
        self.assertIn('A useful task.', result)
        self.assertIn('Repository not published', result)


    def test_workflow_page_exposes_instructions_and_source_download(self):
        from pathlib import Path
        import json
        self.assertTrue(hasattr(web, 'workflow_page'), 'The workflow detail page is missing')
        folder = Path(__file__).resolve().parents[1] / 'workflows/documentation-update'
        item = json.loads((folder / 'workflow.json').read_text())
        item.update(instructions=(folder / 'SKILL.md').read_text(),
                    example_input=(folder / 'examples/input.md').read_text(),
                    example_output=(folder / 'examples/output.md').read_text())
        result = web.workflow_page(item)
        self.assertIn('Draft guide', result)
        self.assertIn('/workflows/documentation-update/SKILL.md', result)
        self.assertIn('Human approval', result)
        self.assertIn('Fictional documentation-change example', result)


if __name__ == '__main__':
    unittest.main()
