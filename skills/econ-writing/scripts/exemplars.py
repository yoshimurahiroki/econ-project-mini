#!/usr/bin/env python3
"""Build a local exemplar library from the user's papers, notes and slides and retrieve passages to imitate.

The library lives outside the repository (``$ERS_EXEMPLARS`` or the user data directory). Commands:

  add PATH... [--genre G] [--refresh]
                                   extract PDF/TXT/MD/TEX; refresh upgrades registered documents
  list                             show the registered documents
  remove DOC_ID...                 delete documents
  find   --lang ja|en [--function F] [--kind prose|slide] [--query WORDS] [--limit N] [--max-chars N]
  outline --lang en [--function F] [--query WORDS] [--doc DOC_ID]
                                   first sentence of every paragraph in one section: the argument moves
  style --lang ja|en [--genre G] [--ngram N]
                                   openings, endings, lengths, transitions and frequent n-grams
  sentences --lang ja|en [--doc ID] [--draft]
                                   original sentences (JSON), or editable source prose (Markdown)
  borrow --lang ja|en --level phrase|sentence|paragraph --query WORDS [--query WORDS...]
                                   source wording ranked within sentences, with local context
  transitions --lang ja|en [--position N] [--previous-ending TEXT]
                                   previous ending -> next opening, with original sentence IDs
  layout DOC_ID [--page N]          slide layout JSON and the saved 150 dpi PNG paths

PDF support: pip install -r requirements-exemplars.txt. SQLite must support FTS5/trigram.
PDFs require selectable text; use --ocr-language jpn+eng with Tesseract language data for scans.
Japanese tokens use SudachiPy when installed, otherwise explicitly labelled character tokens.
References use doc:seq (units) and doc:seq:position (sentences). Refresh re-extracts unit boundaries.
Sentence positions start at 1. Coordinates are PDF points in the rendered page's orientation.
Semantic embeddings, figure/table units and LLM role annotation are outside this first extension.

Functions: introduction, background, data, model, method, results, mechanism, robustness, conclusion.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import statistics
import tempfile
from collections import Counter
from functools import lru_cache
from itertools import pairwise
from pathlib import Path

FUNCTIONS = {
    'introduction': ('introduction', 'motivation', 'はじめに', '序論', '問題意識', '序'),
    'background': ('background', 'institutional', 'institution', 'setting', 'context', '制度', '背景', '概要'),
    'data': ('data', 'sample', 'measurement', 'descriptive', 'データ', '標本', '資料', '記述統計'),
    'model': ('model', 'theory', 'theoretical', 'framework', 'equilibrium', 'モデル', '理論', '枠組み', '均衡'),
    'method': ('empirical strategy', 'identification', 'estimation', 'specification', 'econometric', 'research design',
               'methodology', '実証戦略', '推定方法', '識別', '分析方法', '推定式', '分析の枠組み'),
    'results': ('results', 'findings', 'estimates', 'main effects', 'evidence', '結果', '推定結果', '分析結果'),
    'mechanism': ('mechanism', 'channel', 'heterogeneity', 'interpretation', '経路', 'メカニズム', '異質性', '解釈'),
    'robustness': ('robustness', 'sensitivity', 'placebo', 'alternative', '頑健', '感度', 'プラセボ'),
    'conclusion': ('conclusion', 'concluding', 'discussion', 'summary', 'おわりに', '結論', 'まとめ', '結び', '終わりに'),
}
SKIP_HEADINGS = ('references', 'bibliography', 'appendix', 'acknowledg', '参考文献', '引用文献', '付録', '補論', '謝辞')
JA_END = '。．'
EN_END = '.?!'


def library_path(value=None):
    if value:
        return Path(value).expanduser()
    if os.environ.get('ERS_EXEMPLARS'):
        return Path(os.environ['ERS_EXEMPLARS']).expanduser()
    base = os.environ.get('LOCALAPPDATA') or os.environ.get('XDG_DATA_HOME') or str(Path.home() / '.local' / 'share')
    return Path(base) / 'econ-exemplars' / 'library.sqlite'


def connect(path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.executescript('''
        create table if not exists docs(id text primary key, name text, path text, lang text, kind text, units integer);
        create table if not exists units(doc text, seq integer, lang text, kind text, function text,
                                         section text, page integer, text text);
        create index if not exists units_filter on units(lang, kind, function);
        create index if not exists units_document on units(doc, seq);
        create table if not exists blocks(
            doc text, page integer, seq integer, kind text, text text,
            bbox text, spans text, column_no integer, primary key(doc, page, seq));
        create table if not exists layouts(
            doc text, page integer, layout text, image text, primary key(doc, page));
        create table if not exists sentences(
            id text primary key, doc text, unit_seq integer, position integer, lang text,
            text text, opening text, ending text, length integer, previous_id text, next_id text,
            tokens text, tokenizer text, unique(doc, unit_seq, position));
        create index if not exists sentences_document on sentences(doc, unit_seq, position);
        create table if not exists exemplar_meta(key text primary key, value text);''')
    if 'genre' not in {row[1] for row in db.execute('pragma table_info(docs)')}:
        db.execute("alter table docs add column genre text not null default ''")
    try:
        db.executescript('''
            create virtual table if not exists units_fts using fts5(
                text, content='units', content_rowid='rowid', tokenize='trigram');
            create trigger if not exists units_insert after insert on units begin
                insert into units_fts(rowid, text) values(new.rowid, new.text);
            end;
            create trigger if not exists units_delete after delete on units begin
                insert into units_fts(units_fts, rowid, text) values('delete', old.rowid, old.text);
            end;
            create trigger if not exists units_update after update on units begin
                insert into units_fts(units_fts, rowid, text) values('delete', old.rowid, old.text);
                insert into units_fts(rowid, text) values(new.rowid, new.text);
            end;''')
    except sqlite3.OperationalError as exc:
        db.close()
        if 'no such module' in str(exc) or 'no such tokenizer' in str(exc):
            raise SystemExit('SQLite with FTS5 and the trigram tokenizer is required.') from exc
        raise
    with db:
        if not db.execute("select 1 from exemplar_meta where key='search_index'").fetchone():
            db.execute("insert into units_fts(units_fts) values('rebuild')")
            db.execute("insert into exemplar_meta values('search_index','trigram-v1')")
        if not db.execute("select 1 from exemplar_meta where key='sentence_index'").fetchone():
            # Backfill legacy libraries once; add/refresh writes sentence records directly.
            missing = db.execute('''select doc, seq, lang, kind, text from units u where not exists
                (select 1 from sentences s where s.doc=u.doc and s.unit_seq=u.seq)''').fetchall()
            for doc, seq, lang, kind, text in missing:
                store_sentences(db, doc, seq, lang, kind, text)
            db.execute("insert into exemplar_meta values('sentence_index','v1')")
    return db


def cjk_share(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum('぀' <= c <= 'ヿ' or '一' <= c <= '鿿' for c in letters) / len(letters)


def language(text):
    return 'ja' if cjk_share(text) > 0.2 else 'en'


def word_share(text):
    """Share of characters that belong to words; equations and tables score low."""
    if not text:
        return 0.0
    return sum(c.isalpha() or c.isspace() or c in '、。，．,.()（）' for c in text) / len(text)


def pymupdf_module():
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError('PDF support requires: pip install -r '
                           'skills/econ-writing/scripts/requirements-exemplars.txt') from exc
    return pymupdf


def reading_order(blocks, width):
    """Read each column in full, respecting headings that span both columns."""
    narrow = [b for b in blocks if b['text'] and b['kind'] in ('body', 'list')
              and b['bbox'][2] - b['bbox'][0] < width * .6]
    starts = sorted({b['bbox'][0] for b in narrow})
    gaps = [(right - left, left, right) for left, right in pairwise(starts)]
    if not gaps or max(gaps)[0] < width * .15:
        return sorted(blocks, key=lambda b: (b['bbox'][1], b['bbox'][0]))
    _, left, right = max(gaps)
    left_edge = max(b['bbox'][2] for b in narrow if b['bbox'][0] <= left)
    if left_edge > right - width * .02:
        return sorted(blocks, key=lambda b: (b['bbox'][1], b['bbox'][0]))
    cut = (left_edge + right) / 2
    spanning, columns = [], []
    for block in blocks:
        x0, _, x1, _ = block['bbox']
        if x0 < cut < x1:
            spanning.append(block)
        else:
            block['column_no'] = int(x0 >= cut)
            columns.append(block)
    ordered = []
    # shortcut: one gutter per page; use a layout parser for three columns or irregular sidebars.
    for divider in sorted(spanning, key=lambda b: b['bbox'][1]):
        before = [b for b in columns if b['bbox'][1] < divider['bbox'][1]]
        ordered.extend(sorted(before, key=lambda b: (b['column_no'], b['bbox'][1], b['bbox'][0])))
        columns = [b for b in columns if b['bbox'][1] >= divider['bbox'][1]]
        ordered.append(divider)
    ordered.extend(sorted(columns, key=lambda b: (b['column_no'], b['bbox'][1], b['bbox'][0])))
    return ordered


def split_pdf_blocks(raw):
    """Separate headings and disjoint columns that MuPDF groups into one block."""
    groups = []
    for original in raw['blocks']:
        if original['type'] != 0:
            continue
        group, previous = None, None
        for line in original['lines']:
            sizes = Counter()
            for span in line['spans']:
                sizes[round(span['size'], 1)] += len(span['text'])
            size = sizes.most_common(1)[0][0] if sizes else 0
            bold = all(s['flags'] & 16 for s in line['spans'] if s['text'].strip())
            x0, y0, x1, y1 = line['bbox']
            if previous:
                (px0, _, px1, py1), previous_size, previous_bold = previous
                disjoint = (x0 >= px1 or px0 >= x1) and abs(x0 - px0) > size * 2
                changed = abs(size - previous_size) > max(.8, previous_size * .12) or bold != previous_bold
                split = disjoint or changed or y0 - py1 > size * .8
            else:
                split = True
            if split:
                group = {'lines': [], 'bbox': [x0, y0, x1, y1]}
                groups.append(group)
            group['lines'].append(line)
            bbox = group['bbox']
            group['bbox'] = [min(bbox[0], x0), min(bbox[1], y0), max(bbox[2], x1), max(bbox[3], y1)]
            previous = line['bbox'], size, bold
    return groups


def extract_pdf(path, ocr_language=None):
    pdf = pymupdf_module()
    pages = []
    with pdf.open(path) as document:
        for number, page in enumerate(document, 1):
            flags = pdf.TEXTFLAGS_DICT & ~pdf.TEXT_PRESERVE_IMAGES
            raw = page.get_text('dict', flags=flags)
            has_text = any(s['text'].strip() for b in raw['blocks'] if b['type'] == 0
                           for line in b['lines'] for s in line['spans'])
            used_ocr = not has_text and bool(ocr_language)
            if used_ocr:
                textpage = page.get_textpage_ocr(language=ocr_language, dpi=150, full=True, flags=flags)
                raw = page.get_text('dict', textpage=textpage)
            blocks, sizes = [], Counter()
            for original in split_pdf_blocks(raw):
                spans, lines = [], []
                for line_no, line in enumerate(original['lines']):
                    lines.append(''.join(s['text'] for s in line['spans']))
                    for span in line['spans']:
                        sizes[round(span['size'], 1)] += len(span['text'].strip())
                        spans.append({'text': span['text'], 'font': span['font'], 'size': span['size'],
                                      'bold': bool(span['flags'] & 16), 'color': f"#{span['color']:06x}",
                                      'bbox': list(pdf.Rect(span['bbox']) * page.rotation_matrix), 'line': line_no})
                if any(line.strip() for line in lines):
                    blocks.append({'kind': 'body', 'text': '\n'.join(lines).strip(),
                                   'bbox': list(pdf.Rect(original['bbox']) * page.rotation_matrix),
                                   'spans': spans, 'column_no': 0})
            body_size = sizes.most_common(1)[0][0] if sizes else 0
            for block in blocks:
                text, spans = block['text'], block['spans']
                short = len(text) <= 100 and text[-1:] not in JA_END + EN_END + '、，,:;'
                bold_share = sum(len(s['text']) for s in spans if s['bold']) / max(1, len(text))
                if re.fullmatch(r'\s*(?:\d+|\d+\s*/\s*\d+)\s*', text):
                    block['kind'] = 'footnote'
                elif short and (max(s['size'] for s in spans) > body_size * 1.15 or bold_share > .6
                                or is_heading(text, language(text))):
                    block['kind'] = 'heading'
                elif re.match(r'^(?:[•・\-–▶■□◆○●]|\d+[.)])\s*', text):
                    block['kind'] = 'list'
                elif re.match(r'^(?:Figure|Fig\.|Table|図|表)\s*\d', text, re.IGNORECASE):
                    block['kind'] = 'caption'
                elif max(s['size'] for s in spans) < body_size * .8 and block['bbox'][1] > page.rect.height * .8:
                    block['kind'] = 'footnote'
                elif word_share(text) < .55:
                    block['kind'] = 'equation'
            figures = [list(info['bbox']) for info in page.get_image_info()]
            figures += [list(drawing['rect']) for drawing in page.get_drawings()]
            for bbox in figures:
                blocks.append({'kind': 'figure', 'text': '', 'bbox': list(pdf.Rect(bbox) * page.rotation_matrix),
                               'spans': [], 'column_no': 0})
            ordered = reading_order(blocks, page.rect.width)
            for seq, block in enumerate(ordered):
                block['seq'] = seq
            pages.append({'page': number, 'width': page.rect.width, 'height': page.rect.height,
                          'coordinate_unit': 'pt', 'body_font_size': body_size,
                          'ocr': used_ocr, 'blocks': ordered})
    return pages


def pdf_prose_units(pages, lang):
    units, function, section = [], None, ''
    for page in pages:
        for block in page['blocks']:
            text = join(block['text'].splitlines(), lang)
            if block['kind'] == 'heading':
                function, section = heading_function(text), text
            elif block['kind'] in ('body', 'list') and function != 'skip' and text:
                if units and units[-1][0:2] == [function, section] and units[-1][3][-1:] not in JA_END + EN_END + '」）)”:':
                    units[-1][3] = join([units[-1][3], text], lang)
                else:
                    units.append([function, section, page['page'], text])
    return [tuple(u) for u in units if len(u[3]) >= 20 and word_share(u[3]) >= .7]


def heading_function(line):
    text = re.sub(r'^\s*(?:[IVX]+\.|\d+(?:\.\d+)*\.?|第\s*\d+\s*[章節]|[A-Z]\.)\s*', '', line).strip().lower()
    if not text or len(text) > 60:
        return None
    if any(text.startswith(word) for word in SKIP_HEADINGS):
        return 'skip'
    for function, words in FUNCTIONS.items():
        if any(text.startswith(word) or (len(text) < 25 and word in text) for word in words):
            return function
    return None


def is_heading(line, lang):
    stripped = line.strip()
    if not stripped or len(stripped) > 70 or stripped[-1] in JA_END + EN_END + '、，,:;':
        return False
    numbered = re.match(r'^(?:[IVX]+\.|\d+(?:\.\d+)*\.?|第\s*\d+\s*[章節]|[A-Z]\.)\s+\S', stripped)
    return bool(numbered) or heading_function(stripped) is not None


def join(lines, lang):
    out = ''
    for line in lines:
        line = line.strip()
        if not out:
            out = line
        elif lang == 'ja' or cjk_share(out[-1:] + line[:1]) > 0:
            out += line
        elif out.endswith('-') and line[:1].islower():
            out = out[:-1] + line
        else:
            out += ' ' + line
    return re.sub(r'\s+', ' ', out).strip()


def prose_units(pages, lang):
    """Rebuild paragraphs across line, column and page breaks; a paragraph ends where a sentence ends on a short line
    or before a blank line."""
    units, function, section, block, start = [], None, '', [], 1
    ends = JA_END if lang == 'ja' else EN_END

    def flush(force=False):
        nonlocal block
        if block and (force or join(block, lang)[-1:] in ends + '」）)'):
            if function != 'skip':
                units.append([function, section, start, join(block, lang)])
            block = []
    for number, page in enumerate(pages, 1):
        lines = [x for x in page.split('\n') if not re.fullmatch(r'\s*(?:\d{1,4}|\d+\s*/\s*\d+|-\s*\d+\s*-)\s*', x)]
        widths = sorted(len(x.strip()) for x in lines if len(x.strip()) > 20)
        full = widths[len(widths) * 3 // 4] if widths else 60
        for line in lines:
            stripped = line.strip()
            if not stripped:
                flush()
                continue
            if is_heading(stripped, lang):
                flush(force=True)
                found = heading_function(stripped)
                if found:
                    function, section = found, stripped
                continue
            if not block:
                start = number
            block.append(stripped)
            if stripped[-1] in ends and len(stripped) < 0.8 * full:
                flush()
    flush(force=True)
    merged = []
    for unit in units:
        text = unit[3]
        continues = merged and (merged[-1][3][-1:] not in ends + '」）)' or (lang == 'en' and text[:1].islower()))
        if continues and merged[-1][0] == unit[0]:
            merged[-1][3] = join([merged[-1][3], text], lang)
        else:
            merged.append(unit)
    keep = []
    for function, section, page, text in merged:
        low = text.lower()
        if not (80 <= len(text) <= 2500) or word_share(text) < 0.8:
            continue
        if '@' in text or 'we thank' in low or ('university' in low and len(text) < 300):
            continue
        if lang == 'en' and text.count(' ') < 8:
            continue
        keep.append((function, section, page, text))
    return keep


def slide_units(pages, lang):
    units, function = [], None
    for number, page in enumerate(pages, 1):
        lines = [x.strip() for x in page.split('\n') if x.strip()]
        if not lines:
            continue
        title = lines[0]
        found = heading_function(title)
        if found:
            function = None if found == 'skip' else found
        items = []
        for line in lines[1:]:
            if items and line == items[-1]:
                continue
            bullet = re.match(r'^[•・\-–▶■□◆○●]\s*', line)
            if items and not bullet and items[-1][-1:] not in JA_END + EN_END + ':：' and word_share(line) > 0.7:
                items[-1] = join([items[-1], line], lang)
            else:
                items.append(line[bullet.end():] if bullet else line)
        body = title + '\n' + '\n'.join('- ' + x for x in items if x != title and word_share(x) > 0.7 and len(x) > 1)
        if body.strip():
            units.append((function, title, number, body.rstrip()))
    return units


def rectangle_area(boxes, width, height):
    """Union area, so overlapping vector paths and images are counted once."""
    boxes = [(max(0, x0), max(0, y0), min(width, x1), min(height, y1)) for x0, y0, x1, y1 in boxes]
    boxes = [b for b in boxes if b[2] > b[0] and b[3] > b[1]]
    if not boxes:
        return 0
    ys = sorted({y for _, y0, _, y1 in boxes for y in (y0, y1)})
    positions = {y: i for i, y in enumerate(ys)}
    events = sorted((x, delta, positions[y0], positions[y1])
                    for x0, y0, x1, y1 in boxes
                    for x, delta in ((x0, 1), (x1, -1)))
    counts = [0] * (4 * len(ys))
    lengths = [0] * (4 * len(ys))

    def update(node, left, right, low, high, delta):
        if low <= left and right <= high:
            counts[node] += delta
        else:
            middle = (left + right) // 2
            if low < middle:
                update(node * 2, left, middle, low, high, delta)
            if high > middle:
                update(node * 2 + 1, middle, right, low, high, delta)
        if counts[node] > 0:
            lengths[node] = ys[right] - ys[left]
        elif right - left == 1:
            lengths[node] = 0
        else:
            lengths[node] = lengths[node * 2] + lengths[node * 2 + 1]

    area, previous = 0, events[0][0]
    for x, delta, low, high in events:
        area += (x - previous) * lengths[1]
        update(1, 0, len(ys) - 1, low, high, delta)
        previous = x
    return area


def slide_layout(page):
    blocks = page['blocks']
    text_blocks = [b for b in blocks if b['text'] and b['kind'] != 'footnote']
    title = min(text_blocks, key=lambda b: (b['bbox'][1], b['bbox'][0]), default=None)
    sizes, colors, bullets = Counter(), Counter(), []
    for block in text_blocks:
        for span in block['spans']:
            colors[span['color']] += len(span['text'])
            if block is not title:
                sizes[round(span['size'], 1)] += len(span['text'])
        for line_no in sorted({s['line'] for s in block['spans']}):
            spans = [s for s in block['spans'] if s['line'] == line_no]
            text = ''.join(s['text'] for s in spans).strip()
            if re.match(r'^(?:[•・\-–▶■□◆○●]|\d+[.)])\s*', text):
                bbox = [min(s['bbox'][0] for s in spans), min(s['bbox'][1] for s in spans),
                        max(s['bbox'][2] for s in spans), max(s['bbox'][3] for s in spans)]
                bullets.append({'text': text, 'bbox': bbox})
    body_size = sizes.most_common(1)[0][0] if sizes else page['body_font_size']
    indents = []
    for bullet in sorted(bullets, key=lambda b: b['bbox'][0]):
        x = bullet['bbox'][0]
        if not indents or x - indents[-1] > max(body_size * .6, 1):
            indents.append(x)
        bullet['depth'] = len(indents) - 1
    return {**page, 'dpi': 150, 'title': title, 'body_font_size': body_size, 'bullets': bullets,
            'character_count': sum(len(b['text']) for b in text_blocks),
            'figure_area_ratio': rectangle_area([b['bbox'] for b in blocks if b['kind'] == 'figure'],
                                                page['width'], page['height']) / (page['width'] * page['height']),
            'colors': dict(colors)}


def asset_root(db):
    path = Path(db.execute('pragma database_list').fetchone()[2])
    return path.parent / (path.stem + '.assets')


def saved_asset_dirs(db, doc):
    root = asset_root(db).resolve()
    directories = {Path(image).resolve().parent for image, in db.execute('select image from layouts where doc=?', (doc,))}
    return {directory for directory in directories if directory.parent == root}


def delete_document(db, doc):
    for table in ('sentences', 'blocks', 'layouts', 'units'):
        db.execute(f'delete from {table} where doc=?', (doc,))
    db.execute('delete from docs where id=?', (doc,))


def cmd_add(args, db):
    files = []
    for item in args.paths:
        path = Path(item).expanduser()
        if path.is_dir():
            files += sorted(p for p in path.rglob('*') if p.suffix.lower() in ('.pdf', '.txt', '.md', '.tex'))
        elif path.is_file():
            if path.suffix.lower() not in ('.pdf', '.txt', '.md', '.tex'):
                raise ValueError(f'unsupported input type: {path}')
            files.append(path)
        else:
            raise ValueError(f'input does not exist: {path}')
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        registered = db.execute('select lang, kind, genre from docs where id=?', (digest,)).fetchone()
        if registered and not args.refresh:
            print(f'{digest}  already registered  {path.name}')
            continue
        records = extract_pdf(path, args.ocr_language) if path.suffix.lower() == '.pdf' else []
        pages = ['\n\n'.join(b['text'] for b in p['blocks'] if b['text']) for p in records] if records else [
            path.read_text(encoding='utf-8', errors='replace')]
        landscape = bool(records) and sum(p['width'] > p['height'] for p in records) > len(records) / 2
        lang = args.lang or (registered[0] if registered else language(' '.join(pages)[:20000]))
        kind = args.kind or (registered[1] if registered else 'slide' if landscape else 'prose')
        genre = args.genre if args.genre is not None else registered[2] if registered else ''
        if records and not any(p.strip() for p in pages) and kind == 'prose':
            raise ValueError(f'{path.name}: no extractable text; use --ocr-language jpn+eng for scanned PDFs')
        if kind == 'slide':
            # Slide text follows its visual top-to-bottom order, rather than prose column order.
            pages = ['\n'.join(b['text'] for b in sorted(p['blocks'], key=lambda b: (b['bbox'][1], b['bbox'][0]))
                               if b['text'] and b['kind'] != 'footnote') for p in records] if records else pages
            units = slide_units(pages, lang)
        else:
            units = pdf_prose_units(records, lang) if records else prose_units(pages, lang)
        old_dirs, new_dir, layouts = saved_asset_dirs(db, digest), None, []
        try:
            if records and kind == 'slide':
                root = asset_root(db)
                root.mkdir(parents=True, exist_ok=True)
                new_dir = Path(tempfile.mkdtemp(prefix=digest + '-', dir=root))
                with pymupdf_module().open(path) as document:
                    for record, page in zip(records, document):
                        image = new_dir / f"page-{record['page']:04}.png"
                        page.get_pixmap(dpi=150, alpha=False).save(image)
                        layout = {**slide_layout(record), 'image': str(image.resolve()),
                                  'json_path': str(image.with_suffix('.json').resolve())}
                        raw = json.dumps(layout, ensure_ascii=False)
                        image.with_suffix('.json').write_text(raw, encoding='utf-8')
                        layouts.append((digest, record['page'], raw, layout['image']))
            with db:
                delete_document(db, digest)
                db.executemany('insert into units(doc,seq,lang,kind,function,section,page,text) values(?,?,?,?,?,?,?,?)',
                               [(digest, i, lang, kind, f, s, p, t) for i, (f, s, p, t) in enumerate(units)])
                db.execute('insert into docs(id,name,path,lang,kind,units,genre) values(?,?,?,?,?,?,?)',
                           (digest, path.name, str(path.resolve()), lang, kind, len(units), genre))
                for record in records:
                    db.executemany('insert into blocks values(?,?,?,?,?,?,?,?)',
                                   [(digest, record['page'], b['seq'], b['kind'], b['text'], json.dumps(b['bbox']),
                                     json.dumps(b['spans'], ensure_ascii=False), b['column_no']) for b in record['blocks']])
                db.executemany('insert into layouts values(?,?,?,?)', layouts)
                for seq, (_, _, _, text) in enumerate(units):
                    store_sentences(db, digest, seq, lang, kind, text)
        except BaseException:
            if new_dir:
                shutil.rmtree(new_dir)
            raise
        for directory in old_dirs:
            shutil.rmtree(directory, ignore_errors=True)
        print(f'{digest}  {lang} {kind:5} {len(units):4} units  {path.name}')


def cmd_list(args, db):
    if args.summary:
        rows = db.execute('select lang, kind, count(*), coalesce(sum(units),0) '
                          'from docs group by lang, kind order by lang, kind').fetchall()
        for lang, kind, count, units in rows:
            print(f'{lang} {kind}: {count} documents, {units} units')
        print(f'Total: {sum(row[2] for row in rows)} documents, {sum(row[3] for row in rows)} units')
        return
    for row in db.execute('select id, lang, kind, units, name from docs order by lang, kind, name'):
        print('{}  {} {:5} {:4} units  {}'.format(*row))


def cmd_remove(args, db):
    for doc in args.docs:
        directories = saved_asset_dirs(db, doc)
        with db:
            delete_document(db, doc)
        for directory in directories:
            shutil.rmtree(directory, ignore_errors=True)


def candidates(args, db):
    sql, params = ' where u.lang=?', [args.lang]
    if args.kind:
        sql += ' and u.kind=?'
        params.append(args.kind)
    if args.function:
        sql += ' and u.function=?'
        params.append(args.function)
    if getattr(args, 'doc', None):
        sql += ' and u.doc=?'
        params.append(args.doc)
    if args.genre is not None:
        sql += ' and d.genre=?'
        params.append(args.genre)
    select = 'select u.doc,u.seq,u.function,u.section,u.page,u.text'
    source = ' from units u join docs d on d.id=u.doc'
    terms = list(dict.fromkeys(t.lower() for t in re.split(r'[\s,、，]+', args.query or '') if t))
    if not terms:
        return db.execute(select + source + sql + ' order by length(u.text)>1200,u.doc,u.seq', params).fetchall()
    long_terms, short_terms = [t for t in terms if len(t) >= 3], [t for t in terms if len(t) < 3]
    scored = []
    if long_terms:
        expression = ' OR '.join('"' + term.replace('"', '""') + '"' for term in long_terms)
        scored = db.execute(select + ',bm25(units_fts)' + source +
                            ' join units_fts on units_fts.rowid=u.rowid' + sql + ' and units_fts match ?',
                            [*params, expression]).fetchall()
    if short_terms:
        # FTS5 trigrams cannot match one- or two-character queries such as 需要 or 均衡.
        condition = ' or '.join('instr(lower(u.text),?)>0' for _ in short_terms)
        scored += db.execute(select + ',0.0' + source + sql + ' and (' + condition + ')',
                             [*params, *short_terms]).fetchall()
    def relevance(row):
        text = row[5].lower()
        return (-sum(term in text for term in terms), row[6], len(row[5]) > 1200, row[0], row[1])
    scored.sort(key=relevance)
    seen, rows = set(), []
    for row in scored:
        if row[:2] not in seen:
            seen.add(row[:2])
            rows.append(row[:6])
    return rows


def names(db):
    return dict(db.execute('select id, name from docs'))


def cmd_find(args, db):
    rows, label, used, shown, total = candidates(args, db), names(db), set(), 0, 0
    for doc, seq, function, section, page, text in rows:
        if doc in used or shown >= args.limit or total + len(text) > args.max_chars:
            continue
        used.add(doc)
        shown += 1
        total += len(text)
        print(f'--- [{doc}:{seq}] {label.get(doc, doc)} p.{page} {function or "-"} | {section}\n{text}\n')
        if args.with_layout:
            row = db.execute('select layout from layouts where doc=? and page=?', (doc, page)).fetchone()
            if row:
                print(row[0])
    print(f'({shown} passages, {total} characters)')


def cmd_outline(args, db):
    rows = candidates(args, db)
    if not rows:
        raise SystemExit('no matching passages')
    doc = args.doc or rows[0][0]
    function = args.function or rows[0][2]
    args.query = None
    args.doc, args.function = doc, function
    selected = sorted((row for row in candidates(args, db) if row[2] == function), key=lambda row: row[1])
    print(f'--- outline [{doc}] {names(db).get(doc, doc)} | {function}')
    total = 0
    for number, (_, seq, _, section, _, text) in enumerate(selected, 1):
        first = first_sentence(text, args.lang)[:240]
        total += len(first)
        print(f'{number}. {first}')
    print(f'({len(selected)} paragraphs, {total} characters)')


ABBREVIATIONS = re.compile(r'(?:\bet al|\be\.g|\bi\.e|\bcf|\bp|\bpp|\bFig|\bNo|\bVol|\bU\.S|\bDr|\bMr|\bMrs|\bProf|\b[A-Z])\.$')


def first_sentence(text, lang):
    parts = sentences(text, lang)
    return parts[0] if parts else text


def sentences(text, lang='ja'):
    pattern = r'[。．！？!?][」』”）)]*' if lang == 'ja' else r'''[.?!]+[”"')\]]*(?=\s+|$)'''
    result, start = [], 0
    for match in re.finditer(pattern, text):
        prefix = text[start:match.end()].rstrip('”"\')]').strip()
        if lang == 'en' and ABBREVIATIONS.search(prefix):
            continue
        sentence = text[start:match.end()].strip()
        if sentence:
            result.append(sentence)
        start = match.end()
    if text[start:].strip():
        result.append(text[start:].strip())
    return result


@lru_cache(maxsize=1)
def japanese_tokenizer():
    try:
        from sudachipy import dictionary
        return dictionary.Dictionary().create()
    except ImportError:
        return None


def tokenize(text, lang):
    if lang == 'en':
        return re.findall(r"[a-z]+(?:['’-][a-z]+)*|\d+(?:\.\d+)?", text.lower()), 'english-words'
    tokenizer = japanese_tokenizer()
    if tokenizer:
        return [m.surface() for m in tokenizer.tokenize(text) if not m.surface().isspace()], 'sudachipy'
    return [c for c in text if not c.isspace()], 'japanese-characters'


def sentence_edges(text, lang):
    if lang == 'ja':
        head = re.match(r'^([^、，]{1,12})[、，]', text)
        opening = head.group(1) if head else text[:8]
        core = text.rstrip('。．！？!?」』”）)')
        tail = re.search(r'(のである|である|であった|となる|となった|といえる|と考えられる|とみられる|'
                         r'を表す|と呼ぶ|ている|ていた|られる|される|する|した|ない|なる|ある|あった|だ|ます|ました|です|でした)$', core)
        return opening, tail.group(1) if tail else core[-3:]
    words = re.findall(r"[\w]+(?:['’-][\w]+)*", text.lower())
    head = re.match(r'^([^,]{1,50}),', text)
    return (head.group(1).lower() if head else ' '.join(words[:3]), ' '.join(words[-3:]))


def store_sentences(db, doc, seq, lang, kind, text):
    parts = [re.sub(r'^-\s*', '', line.strip()) for line in text.splitlines()] if kind == 'slide' else [text]
    parts = [sentence for part in parts for sentence in sentences(part, lang)]
    ids = [f'{doc}:{seq}:{position}' for position in range(1, len(parts) + 1)]
    records = []
    for offset, sentence in enumerate(parts):
        opening, ending = sentence_edges(sentence, lang)
        tokens, tokenizer = tokenize(sentence, lang)
        records.append((ids[offset], doc, seq, offset + 1, lang, sentence, opening, ending, len(sentence),
                        ids[offset - 1] if offset else None, ids[offset + 1] if offset + 1 < len(ids) else None,
                        json.dumps(tokens, ensure_ascii=False), tokenizer))
    db.executemany('insert into sentences values(?,?,?,?,?,?,?,?,?,?,?,?,?)', records)


def matching_sentences(args, db):
    rows = []
    columns = [column[1] for column in db.execute('pragma table_info(sentences)')]
    selected = candidates(args, db)
    if getattr(args, 'draft', False) and args.function is None:
        selected = [row for row in selected if row[2] in ('results', 'mechanism', 'conclusion')]
    for doc, seq, function, _section, page, *_ in selected[:args.sample]:
        records = db.execute('select * from sentences where doc=? and unit_seq=? order by position', (doc, seq))
        for record in records:
            row = dict(zip(columns, record))
            if args.position is None or row['position'] == args.position:
                row['tokens'] = json.loads(row['tokens'])
                row.update(page=page, function=function, section=_section)
                rows.append(row)
    return rows


def sentence_transitions(rows, args):
    ending_filter = getattr(args, 'previous_ending', None)
    return [(previous, current) for previous, current in pairwise(rows)
            if current['previous_id'] == previous['id']
            and (args.position is None or current['position'] == args.position)
            and (ending_filter is None or previous['ending'] == ending_filter)]


def print_transitions(pairs, top):
    counts = Counter((previous['ending'], current['opening']) for previous, current in pairs)
    print('transitions (previous ending -> next opening):')
    for (ending, opening), count in counts.most_common(top):
        previous, current = next((p, c) for p, c in pairs if p['ending'] == ending and c['opening'] == opening)
        print(f"{ending} -> {opening} ({count}) [{previous['id']} -> {current['id']}]\n"
              f"  {previous['text']}\n  {current['text']}")


def style_sentences(rows):
    roots = Path(__file__).resolve().parents
    policy = next(path for root in roots
                  for path in (root / 'quality/prose_rules.json', root / 'PROSE_CHECK_RULES.json')
                  if path.is_file())
    rules = json.loads(policy.read_text(encoding='utf-8'))['rules']
    patterns = [re.compile(rule['pattern'], re.IGNORECASE) for rule in rules]
    return [row for row in rows if not any(pattern.search(row['text']) for pattern in patterns)
            and not re.search(r'(?:\d+\.\d+){3,}', row['text'])]


def cmd_sentences(args, db):
    rows = matching_sentences(args, db)
    if getattr(args, 'draft', False):
        rows = [row for row in style_sentences(rows)
                if not re.match(r'^[ぁ-ゖ][、，]', row['text'])]
        for row in rows[:args.limit]:
            print(f"<!-- source {row['id']}; page {row['page']}; {row['function']} -->\n{row['text']}\n")
        return
    print(json.dumps({'sentences': rows[:args.limit]}, ensure_ascii=False, indent=2))


def cmd_borrow(args, db):
    """Retrieve wording at the unit currently being written or revised."""
    results, budget = [], args.max_chars
    for query in args.query or ['']:
        request = argparse.Namespace(**dict(vars(args), query=query))
        terms = list(dict.fromkeys(t.casefold() for t in re.split(r'[\s,、，]+', query) if t))
        rows = matching_sentences(request, db)
        for row in rows:
            row['text'] = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', row['text']).strip()
        rows = style_sentences(rows)
        coverage = lambda text: sum(term in text.casefold() for term in terms)
        rows = [row for row in rows
                if coverage(row['text']) >= min(2, len(terms))
                and re.search(r'[。．.!?！？][）)」』”"]*$', row['text'])
                and not re.match(r'^[ぁ-ゖ][、，]', row['text'])
                and not any(word in str(row.get('section') or '').casefold() for word in SKIP_HEADINGS)]
        rows.sort(key=lambda row: (-coverage(row['text']),
                  row['function'] not in ('results', 'mechanism', 'conclusion'),
                  abs(len(row['text']) - 80), row['id']))
        matches, seen = [], set()
        for row in rows:
            key = (row['doc'], row['unit_seq']) if args.level == 'paragraph' else row['text']
            if key in seen or len(matches) >= args.limit:
                continue
            seen.add(key)
            match = {'source': row['id'], 'page': row['page'],
                     'function': row['function'], 'text': row['text']}
            if args.level == 'phrase':
                clauses = [part.strip() for part in re.split(r'[、，,;；]', row['text']) if part.strip()]
                match['phrase'] = min(clauses, key=lambda text: (-coverage(text), abs(len(text) - 40)))
            elif args.level == 'sentence':
                for label, source_id in (('before', row['previous_id']), ('after', row['next_id'])):
                    context = db.execute('select text from sentences where id=?', (source_id,)).fetchone()
                    if context:
                        match[label] = context[0]
            else:
                match['paragraph'] = db.execute('select text from units where doc=? and seq=?',
                                               (row['doc'], row['unit_seq'])).fetchone()[0]
            size = len(json.dumps(match, ensure_ascii=False))
            if size <= budget:
                matches.append(match)
                budget -= size
        results.append({'query': query, 'matches': matches})
    print(json.dumps({'level': args.level, 'queries': results}, ensure_ascii=False, indent=2))


def cmd_transitions(args, db):
    position = args.position
    args.position = None
    rows = style_sentences(matching_sentences(args, db))
    args.position = position
    print_transitions(sentence_transitions(rows, args), args.top)


def cmd_layout(args, db):
    sql, params = 'select layout from layouts where doc=?', [args.doc]
    if args.page is not None:
        sql += ' and page=?'
        params.append(args.page)
    pages = [json.loads(row[0]) for row in db.execute(sql + ' order by page', params)]
    if not pages:
        raise ValueError('no saved slide layouts; add the PDF with --kind slide --refresh')
    print(json.dumps({'doc': args.doc, 'pages': pages}, ensure_ascii=False, indent=2))


def cmd_style(args, db):
    position = args.position
    args.position = None
    rows = style_sentences(matching_sentences(args, db))
    args.position = position
    for row in rows[:3]:
        print(f"expression [{row['id']}]: {row['text']}")
    pairs = sentence_transitions(rows, args)
    if position is not None:
        rows = [row for row in rows if row['position'] == position]
    lengths = [row['length'] for row in rows]
    if not lengths:
        raise SystemExit('no matching sentences')
    opening, ending = Counter(row['opening'] for row in rows), Counter(row['ending'] for row in rows)
    comma = Counter('、。' if '、' in row['text'] else '，．' if '，' in row['text'] else '-' for row in rows)
    q = statistics.quantiles(lengths, n=4) if len(lengths) > 3 else [min(lengths), statistics.median(lengths), max(lengths)]
    passages = len({(row['doc'], row['unit_seq']) for row in rows})
    print(f'--- {args.lang} style of {passages} passages, {len(lengths)} sentences')
    print('punctuation: ' + ', '.join(f'{k} {v}' for k, v in comma.most_common()))
    print(f'sentence length (characters): quartiles {q[0]:.0f} / {q[1]:.0f} / {q[2]:.0f}; '
          f'short (<30) {sum(x < 30 for x in lengths) / len(lengths):.0%}, long (>70) {sum(x > 70 for x in lengths) / len(lengths):.0%}')
    print('openings: ' + '、'.join(f'{k}({v})' for k, v in opening.most_common(args.top)))
    print('endings: ' + '、'.join(f'{k}({v})' for k, v in ending.most_common(args.top)))
    ngrams = Counter()
    for row in rows:
        tokens = row['tokens']
        ngrams.update(tuple(tokens[i:i + args.ngram]) for i in range(len(tokens) - args.ngram + 1))
    print('tokenizers: ' + ', '.join(sorted({row['tokenizer'] for row in rows})))
    print(f'{args.ngram}-grams (ngram): ' + ', '.join(' '.join(gram) + f'({n})' for gram, n in ngrams.most_common(args.top)))
    print_transitions(pairs, args.top)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--library', help='library file (default: $ERS_EXEMPLARS or the user data directory)')
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('add')
    add.add_argument('paths', nargs='+')
    add.add_argument('--lang', choices=('ja', 'en'))
    add.add_argument('--kind', choices=('prose', 'slide'))
    add.add_argument('--genre', help='free-form genre, e.g. paper, textbook, lecture, talk')
    add.add_argument('--refresh', action='store_true', help='re-extract registered files without changing their document IDs')
    add.add_argument('--ocr-language', help='OCR textless pages with Tesseract language data, e.g. jpn+eng')
    listing = sub.add_parser('list')
    listing.add_argument('--summary', action='store_true', help='show counts by language and kind')
    remove = sub.add_parser('remove')
    remove.add_argument('docs', nargs='+')
    layout = sub.add_parser('layout')
    layout.add_argument('doc')
    layout.add_argument('--page', type=int)
    for name in ('find', 'outline', 'style', 'sentences', 'transitions', 'borrow'):
        p = sub.add_parser(name)
        p.add_argument('--lang', choices=('ja', 'en'), required=True)
        p.add_argument('--function', choices=tuple(FUNCTIONS))
        p.add_argument('--kind', choices=('prose', 'slide'))
        p.add_argument('--genre')
        p.add_argument('--query', action='append' if name == 'borrow' else 'store')
        p.add_argument('--doc')
        p.add_argument('--limit', type=int, default=1 if name == 'borrow' else 3)
        p.add_argument('--max-chars', type=int, default=2400)
        p.add_argument('--sample', type=int, default=40)
        p.add_argument('--top', type=int, default=15)
        p.add_argument('--position', type=int, help='sentence position within a paragraph/slide (1-based)')
        if name == 'find':
            p.add_argument('--with-layout', action='store_true', help='include saved slide layout JSON and image path')
        if name == 'sentences':
            p.add_argument('--draft', action='store_true', help='Write filtered original prose as an editable Markdown draft')
        if name == 'borrow':
            p.add_argument('--level', choices=('phrase', 'sentence', 'paragraph'), default='phrase')
        if name == 'style':
            p.add_argument('--ngram', type=int, default=2)
        if name == 'transitions':
            p.add_argument('--previous-ending')
    args = parser.parse_args(argv)
    for name in ('limit', 'max_chars', 'sample', 'top', 'position', 'ngram', 'page'):
        value = getattr(args, name, None)
        if value is not None and value < 1:
            parser.error(f'--{name.replace("_", "-")} must be positive')
    path = library_path(args.library).resolve()
    if path.is_relative_to(Path(__file__).resolve().parents[3]):
        parser.error('the exemplar library and images must be outside the repository; set $ERS_EXEMPLARS')
    if args.command not in ('add',) and not path.exists():
        raise SystemExit(f'no exemplar library at {path}; register files with: exemplars.py add PATH')
    db = connect(path)
    try:
        {'add': cmd_add, 'list': cmd_list, 'remove': cmd_remove, 'find': cmd_find,
         'outline': cmd_outline, 'style': cmd_style, 'sentences': cmd_sentences,
         'transitions': cmd_transitions, 'borrow': cmd_borrow, 'layout': cmd_layout}[args.command](args, db)
    except (ValueError, RuntimeError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    finally:
        db.close()


if __name__ == '__main__':
    main()
