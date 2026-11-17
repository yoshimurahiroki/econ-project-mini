"""Exercise library migrations and the public CLI with disposable source documents.

Run: python3 -m unittest discover -s skills/econ-writing/scripts -p 'test_exemplars.py' -v
"""
import hashlib
import importlib.util
import json
import random
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('exemplars.py')
PDF_AVAILABLE = importlib.util.find_spec('pymupdf') is not None


class ExemplarLibraryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix='exemplars-test-')
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.library = self.root / 'library.sqlite'

    def cli(self, *arguments):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), '--library', str(self.library), *map(str, arguments)],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result.stdout

    def query(self, sql, parameters=()):
        with sqlite3.connect(self.library) as db:
            return db.execute(sql, parameters).fetchall()

    def source(self, name, text):
        path = self.root / name
        path.write_text(text, encoding='utf-8')
        return path

    def add(self, path, *options):
        self.cli('add', path, *options)
        return hashlib.sha256(path.read_bytes()).hexdigest()[:12]

    def sentence_records(self, *arguments):
        result = json.loads(self.cli('sentences', *arguments))
        return result if isinstance(result, list) else result['sentences']

    def test_borrow_ranks_same_sentence_terms_and_returns_revision_context(self):
        text = ('Results\n\nEmployment rose after the reform. Demand followed a seasonal cycle. '
                'Higher demand increased employment. Firms expanded production. '
                'Prices rose by 0.13 percent with demand. Firms adjusted prices after the reform. '
                'Employment demand table 0.130.130.540.540.090.09 reports regional figures.')
        self.add(self.source('wording.txt', text), '--lang', 'en')
        result = json.loads(self.cli('borrow', '--lang', 'en', '--level', 'sentence',
                                    '--query', 'employment demand', '--query', 'prices demand', '--limit', '1'))
        first, second = [row['matches'][0] for row in result['queries']]
        self.assertEqual(first['text'], 'Higher demand increased employment.')
        self.assertEqual(first['before'], 'Demand followed a seasonal cycle.')
        self.assertEqual(first['after'], 'Firms expanded production.')
        self.assertEqual(second['text'], 'Prices rose by 0.13 percent with demand.')
        self.assertIn('source', first)

    def test_short_and_mixed_queries_rank_matching_terms_first(self):
        spec = importlib.util.spec_from_file_location('exemplars_ranking', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with module.connect(self.library) as db:
            db.execute('insert into docs values(?,?,?,?,?,?,?)',
                       ('doc', 'source.txt', '/source.txt', 'ja', 'prose', 2, ''))
            db.executemany('insert into units values(?,?,?,?,?,?,?,?)', [
                ('doc', 0, 'ja', 'prose', None, '', 1, '研究成果を述べる。'),
                ('doc', 1, 'ja', 'prose', None, '', 1, '営業の成果と報酬を計算する。'),
            ])
            for query in ('営業 成果 報酬', '研究成果 営業 報酬'):
                args = SimpleNamespace(lang='ja', kind='prose', function=None, genre=None, query=query)
                self.assertEqual(module.candidates(args, db)[0][1], 1)

    def test_opening_indexed_library_does_not_read_paragraph_text(self):
        self.add(self.source('indexed.txt', '営業の成果と報酬を計算する。' * 10), '--lang', 'ja')
        spec = importlib.util.spec_from_file_location('exemplars_open', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_connect = sqlite3.connect

        def metadata_connection(*args, **kwargs):
            db = original_connect(*args, **kwargs)
            db.set_authorizer(lambda action, table, column, *_:
                              sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_READ
                              and (table, column) == ('units', 'text') else sqlite3.SQLITE_OK)
            return db

        with patch.object(module.sqlite3, 'connect', metadata_connection):
            db = module.connect(self.library)
            self.addCleanup(db.close)
            self.assertEqual(db.execute('select count(*) from docs').fetchone()[0], 1)

    def test_list_summary_counts_documents_without_dumping_names(self):
        self.add(self.source('one.txt', 'Introduction\n\n' + 'We study resource allocation across regions and compare policy outcomes. ' * 4), '--lang', 'en', '--kind', 'prose')
        self.add(self.source('two.txt', '資源の配分を考える。地域ごとの政策の効果を比較する。' * 5), '--lang', 'ja', '--kind', 'prose')
        summary = self.cli('list', '--summary')
        self.assertIn('en prose: 1 documents, 1 units', summary)
        self.assertIn('ja prose: 1 documents, 1 units', summary)
        self.assertIn('Total: 2 documents, 2 units', summary)
        self.assertNotIn('one.txt', summary)
        self.assertIn('one.txt', self.cli('list'))

    def test_figure_area_handles_overlap_clipping_and_dense_drawings(self):
        spec = importlib.util.spec_from_file_location('exemplars_test', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        boxes = [(-2, -1, 4, 4), (2, 2, 6, 6), (5, 5, 15, 7),
                 (-2, -1, 4, 4), (4, 4, 4, 9), (20, 20, 30, 30)]
        self.assertEqual(module.rectangle_area(boxes, 10, 10), 37)
        rng = random.Random(1701)
        for _ in range(50):
            boxes = [tuple(rng.randrange(-3, 13) for _ in range(4)) for _ in range(30)]
            cells = {(x, y) for x in range(10) for y in range(10)
                     if any(x0 <= x < x1 and y0 <= y < y1 for x0, y0, x1, y1 in boxes)}
            self.assertEqual(module.rectangle_area(boxes, 10, 10), len(cells))
        dense = [(x, 0, x + 2, 10) for x in range(86020)]
        self.assertEqual(module.rectangle_area(dense, 86022, 10), 860210)

    def test_slide_text_remains_searchable_after_references_heading(self):
        spec = importlib.util.spec_from_file_location('exemplars_test', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pages = ['Introduction\nMain research question.',
                 'References\nA cited paper.',
                 'Treatment effects\nAdditional results.']
        units = module.slide_units(pages, 'en')
        self.assertEqual([unit[2] for unit in units], [1, 2, 3])
        self.assertEqual([unit[0] for unit in units], ['introduction', None, None])

    def test_migration_retains_legacy_data_and_backfills_search_and_sentences(self):
        text = ('最低賃金の変更は労働市場に影響を与える。'
                'しかし，雇用の反応は企業の選択によって異なる。'
                'したがって，地域ごとの制度と雇用の推移を調べる。')
        with sqlite3.connect(self.library) as db:
            db.executescript('''
                create table docs(id text primary key, name text, path text, lang text, kind text, units integer);
                create table units(doc text, seq integer, lang text, kind text, function text,
                                   section text, page integer, text text);
            ''')
            db.execute('insert into docs values(?,?,?,?,?,?)',
                       ('legacy', 'legacy.txt', '/original/legacy.txt', 'ja', 'prose', 1))
            db.execute('insert into units values(?,?,?,?,?,?,?,?)',
                       ('legacy', 0, 'ja', 'prose', 'results', '結果', 3, text))
        self.assertIn('legacy.txt', self.cli('list'))
        self.assertIn(text, self.cli('find', '--lang', 'ja', '--query', '最低'))
        self.assertIn(text, self.cli('find', '--lang', 'ja', '--query', '最低賃金'))
        self.assertNotIn(text, self.cli('find', '--lang', 'ja', '--query', '存在しない語句'))
        records = self.sentence_records('--lang', 'ja', '--doc', 'legacy', '--limit', '20')
        self.assertEqual(len(records), 3)
        self.assertEqual([r['text'] for r in records], [
            '最低賃金の変更は労働市場に影響を与える。',
            'しかし，雇用の反応は企業の選択によって異なる。',
            'したがって，地域ごとの制度と雇用の推移を調べる。',
        ])
        self.assertEqual(records[0]['next_id'], records[1]['id'])
        self.assertEqual(records[1]['previous_id'], records[0]['id'])
        self.assertIsNone(records[0]['previous_id'])
        self.assertIsNone(records[-1]['next_id'])
        self.assertEqual([r['position'] for r in records], [1, 2, 3])
        self.assertEqual([r['length'] for r in records], [len(r['text']) for r in records])
        self.assertTrue(all('opening' in r and 'ending' in r for r in records))
        self.assertEqual(self.query('select text from units'), [(text,)])
        self.cli('list')
        self.assertEqual(self.query('select count(*) from sentences')[0][0], 3)
        self.assertEqual([r['id'] for r in records],
                         [r['id'] for r in self.sentence_records('--lang', 'ja', '--doc', 'legacy', '--limit', '20')])
        self.cli('remove', 'legacy')
        self.assertEqual(self.query('select count(*) from sentences')[0][0], 0)
        self.assertEqual(self.query("select count(*) from units_fts where units_fts match '最低賃金'"), [(0,)])

    def test_english_sentences_transitions_and_genre_filters(self):
        paragraph = ('We examine policy changes, e.g. California wage floors and U.S. Census records, using regional data. '
                     'However, regional employment responds differently across industries. '
                     'Therefore, the estimates describe the adjustment of firms over time.')
        paper = self.source('paper.txt', 'Introduction\n\n' + paragraph)
        note = self.source('note.txt', 'Introduction\n\n' + paragraph + ' These notes discuss policy changes.')
        paper_id = self.add(paper, '--lang', 'en', '--genre', 'paper')
        self.add(note, '--lang', 'en', '--genre', 'lecture')
        found = self.cli('find', '--lang', 'en', '--query', 'policy', '--genre', 'paper')
        self.assertIn('paper.txt', found)
        self.assertNotIn('note.txt', found)
        records = self.sentence_records('--lang', 'en', '--doc', paper_id, '--limit', '20')
        self.assertEqual(len(records), 3)
        self.assertTrue(records[0]['text'].endswith('using regional data.'))
        self.assertEqual(records[1]['previous_id'], records[0]['id'])
        self.assertEqual(records[1]['next_id'], records[2]['id'])
        self.assertTrue(records[1]['opening'].lower().startswith('however'))
        style = self.cli('style', '--lang', 'en', '--genre', 'paper', '--ngram', '2')
        self.assertIn('ngram', style.lower())
        transitions = self.cli('transitions', '--lang', 'en', '--doc', paper_id)
        self.assertIn('however', transitions.lower())
        self.assertTrue(any(r['id'] in transitions for r in records))
        self.assertIn('We examine policy changes', self.cli('outline', '--lang', 'en', '--doc', paper_id))

    def test_transitions_stay_within_paragraphs_and_support_position(self):
        first = ('Firms choose employment using local demand and expected revenue in the coming year. '
                 'However, wage changes alter the cost of hiring workers across regions.')
        second = ('Regional estimates describe how output responds to a change in the policy environment. '
                  'Therefore, the analysis follows establishments before and after the reform.')
        path = self.source('paragraphs.txt', 'Introduction\n\n' + first + '\n\n' + second)
        doc = self.add(path, '--lang', 'en')
        records = self.sentence_records('--lang', 'en', '--doc', doc, '--limit', '20')
        self.assertEqual(len(records), 4)
        self.assertEqual([r['position'] for r in records], [1, 2, 1, 2])
        self.assertIsNone(records[1]['next_id'])
        self.assertIsNone(records[2]['previous_id'])
        transitions = self.cli('transitions', '--lang', 'en', '--doc', doc, '--position', '2')
        for previous, current in [(records[0], records[1]), (records[2], records[3])]:
            self.assertIn(f"[{previous['id']} -> {current['id']}]", transitions)
        self.assertNotIn(f"[{records[1]['id']} -> {records[2]['id']}]", transitions)
        selected = self.sentence_records('--lang', 'en', '--doc', doc, '--position', '2', '--limit', '20')
        self.assertEqual([r['id'] for r in selected], [records[1]['id'], records[3]['id']])
        self.assertNotIn('[', self.cli('transitions', '--lang', 'en', '--doc', doc, '--position', '1'))

    @unittest.skipUnless(PDF_AVAILABLE, 'PyMuPDF is required for PDF integration tests')
    def test_pdf_splits_mixed_typography_and_merged_columns(self):
        import pymupdf
        path = self.root / 'merged-blocks.pdf'
        evidence = 'The reform changes employment across local markets and affects the demand for workers.'
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=600, height=800)
            page.insert_text((40, 50), 'Results', fontname='hebo', fontsize=14)
            page.insert_text((40, 65), evidence, fontsize=11)
            for y in (120, 135, 150):
                page.insert_text((40, y), 'Left column line with words.', fontsize=11)
                page.insert_text((330, y), 'Right column line with words.', fontsize=11)
            pdf.save(path)
        doc = self.add(path, '--lang', 'en', '--kind', 'prose')
        blocks = self.query('select kind, text from blocks where doc=? order by page, seq', (doc,))
        self.assertIn(('heading', 'Results'), blocks)
        self.assertTrue(any(evidence in text and kind != 'heading' for kind, text in blocks))
        text = '\n'.join(text for _, text in blocks)
        self.assertEqual(text.count('Left column line with words.'), 3)
        self.assertEqual(text.count('Right column line with words.'), 3)
        self.assertLess(text.rfind('Left column line'), text.find('Right column line'), text)
        self.assertIn(evidence, self.cli('find', '--lang', 'en', '--doc', doc, '--function', 'results'))

    @unittest.skipUnless(PDF_AVAILABLE, 'PyMuPDF is required for PDF integration tests')
    def test_pdf_columns_typography_and_headings(self):
        import pymupdf
        path = self.root / 'columns.pdf'
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=600, height=800)
            page.insert_text((40, 50), 'Introduction', fontname='hebo', fontsize=18, color=(0, 0, 1))
            for label, x, y in [('RIGHT TOP', 330, 100), ('LEFT BOTTOM', 40, 240),
                                ('LEFT TOP', 40, 100), ('RIGHT BOTTOM', 330, 240)]:
                text = (f'{label} describes how firms adjust to policy changes. '
                        'Regional data reveal differences in employment and output across local markets.')
                remaining = page.insert_textbox((x, y, x + 230, y + 120), text, fontsize=11)
                self.assertGreaterEqual(remaining, 0)
            pdf.save(path)
        doc = self.add(path, '--lang', 'en', '--kind', 'prose')
        blocks = self.query('select kind, text, spans from blocks where doc=? order by page, seq', (doc,))
        body = '\n'.join(b[1] for b in blocks)
        positions = [body.index(label) for label in ('LEFT TOP', 'LEFT BOTTOM', 'RIGHT TOP', 'RIGHT BOTTOM')]
        self.assertEqual(positions, sorted(positions), body)
        headings = [b for b in blocks if b[0] == 'heading' and 'Introduction' in b[1]]
        self.assertEqual(len(headings), 1)
        title_spans = json.loads(headings[0][2])
        self.assertTrue(any(s['bold'] and abs(s['size'] - 18) < 0.1 for s in title_spans))
        self.assertTrue(any(s['color'] in ('#0000ff', '#0000FF', 255) for s in title_spans))
        self.assertIn('LEFT TOP', self.cli('find', '--lang', 'en', '--function', 'introduction', '--doc', doc))

    @unittest.skipUnless(PDF_AVAILABLE, 'PyMuPDF is required for PDF integration tests')
    def test_slide_layout_image_refresh_and_removal(self):
        import pymupdf
        path = self.root / 'slides.pdf'
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=720, height=405)
            page.insert_text((40, 55), 'Results', fontname='hebo', fontsize=30, color=(0, 0, 1))
            page.insert_text((50, 140), '- Employment rises after the reform.', fontsize=18)
            page.insert_text((80, 180), '- Gains are concentrated in small firms.', fontsize=18)
            page.draw_rect((450, 130, 650, 300), color=(1, 0, 0), fill=(0, 1, 0))
            pdf.save(path)
        doc = self.add(path, '--lang', 'en', '--kind', 'slide', '--genre', 'talk')
        output = json.loads(self.cli('layout', doc, '--page', '1'))
        self.assertEqual(len(output['pages']), 1)
        layout = output['pages'][0]
        image = Path(layout['image'])
        self.assertTrue(image.is_file())
        self.assertTrue(image.is_relative_to(self.root))
        pixmap = pymupdf.Pixmap(str(image))
        self.assertEqual((pixmap.width, pixmap.height), (1500, 844))
        self.assertEqual((pixmap.xres, pixmap.yres), (150, 150))
        stored = json.loads(self.query('select layout from layouts where doc=? and page=1', (doc,))[0][0])
        self.assertIn('Results', json.dumps(stored))
        self.assertTrue(self.query('select count(*) from blocks where doc=?', (doc,))[0][0] >= 3)
        initial_png_count = len(list(self.root.rglob('*.png')))
        self.add(path, '--lang', 'en', '--kind', 'slide', '--genre', 'talk', '--refresh')
        refreshed = json.loads(self.cli('layout', doc, '--page', '1'))['pages'][0]
        self.assertTrue(Path(refreshed['image']).is_file())
        self.assertEqual(len(list(self.root.rglob('*.png'))), initial_png_count)
        self.assertEqual(self.query('select count(*) from docs where id=?', (doc,)), [(1,)])
        self.assertEqual(self.query('select count(*) from layouts where doc=?', (doc,)), [(1,)])
        self.cli('remove', doc)
        for table in ('docs', 'units', 'blocks', 'sentences', 'layouts'):
            self.assertEqual(self.query(f'select count(*) from {table}'), [(0,)], table)
        self.assertEqual(list(self.root.rglob('*.png')), [])


    @unittest.skipUnless(PDF_AVAILABLE, 'PyMuPDF is required for PDF integration tests')
    def test_failed_refresh_keeps_original_rows_and_images(self):
        import pymupdf
        path = self.root / 'refresh.pdf'
        with pymupdf.open() as pdf:
            page = pdf.new_page(width=720, height=405)
            page.insert_text((40, 50), 'Results', fontsize=30)
            page.insert_text((40, 120), 'Employment rises after the reform in smaller local markets.', fontsize=18)
            pdf.save(path)
        doc = self.add(path, '--lang', 'en', '--kind', 'slide')
        tables = ('docs', 'units', 'blocks', 'sentences', 'layouts')
        before = {table: self.query(f'select * from {table}') for table in tables}
        image_paths = set(self.root.rglob('*.png'))
        with sqlite3.connect(self.library) as db:
            db.execute("""create trigger fail_refresh before insert on docs begin
                          select raise(abort, 'forced refresh failure'); end""")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), '--library', str(self.library), 'add', str(path), '--refresh'],
            text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('forced refresh failure', result.stderr)
        for table in tables:
            self.assertEqual(self.query(f'select * from {table}'), before[table], table)
        self.assertEqual(set(self.root.rglob('*.png')), image_paths)
        self.assertTrue(all(path.is_file() for path in image_paths))
        self.assertIn('Employment rises', self.cli('find', '--lang', 'en', '--doc', doc, '--query', 'Employment'))


if __name__ == '__main__':
    unittest.main()
