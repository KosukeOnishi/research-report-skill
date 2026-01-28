#!/usr/bin/env python3
"""
Generate PDF research reports from markdown content and images.
Uses weasyprint for HTML to PDF conversion.
"""

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


def image_to_data_uri(img_path: Path) -> str:
    """Convert image file to data URI for embedding."""
    suffix = img_path.suffix.lower()
    if suffix == '.svg':
        content = img_path.read_bytes()
        encoded = base64.b64encode(content).decode()
        return f"data:image/svg+xml;base64,{encoded}"
    elif suffix in ['.jpg', '.jpeg']:
        content = img_path.read_bytes()
        encoded = base64.b64encode(content).decode()
        return f"data:image/jpeg;base64,{encoded}"
    elif suffix == '.png':
        content = img_path.read_bytes()
        encoded = base64.b64encode(content).decode()
        return f"data:image/png;base64,{encoded}"
    elif suffix == '.gif':
        content = img_path.read_bytes()
        encoded = base64.b64encode(content).decode()
        return f"data:image/gif;base64,{encoded}"
    elif suffix == '.webp':
        content = img_path.read_bytes()
        encoded = base64.b64encode(content).decode()
        return f"data:image/webp;base64,{encoded}"
    else:
        return ""


def svg_to_data_uri(svg_path: Path) -> str:
    """Convert SVG file to data URI for embedding."""
    return image_to_data_uri(svg_path)


def generate_toc(markdown: str) -> tuple[str, str]:
    """
    Generate a Table of Contents from markdown headers.
    Returns (toc_html, modified_markdown_with_anchors)
    """
    lines = markdown.split('\n')
    toc_items = []
    modified_lines = []
    header_counts = {}  # Track duplicate headers for unique anchors

    for line in lines:
        # Match headers ## and ### (skip # as it's usually the title)
        match = re.match(r'^(#{2,3})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()

            # Remove any existing anchor like {#anchor}
            title_clean = re.sub(r'\s*\{#[^}]+\}', '', title)

            # Create anchor from title
            anchor = re.sub(r'[^\w\s\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff-]', '', title_clean.lower())
            anchor = re.sub(r'\s+', '-', anchor)

            # Handle duplicate anchors
            if anchor in header_counts:
                header_counts[anchor] += 1
                anchor = f"{anchor}-{header_counts[anchor]}"
            else:
                header_counts[anchor] = 0

            # Add to TOC
            indent = '  ' * (level - 2)  # ## = 0 indent, ### = 1 indent
            toc_items.append(f'{indent}- [{title_clean}](#{anchor})')

            # Add anchor to the line
            modified_lines.append(f'{match.group(1)} {title_clean} {{#{anchor}}}')
        else:
            modified_lines.append(line)

    if not toc_items:
        return '', markdown

    toc_md = "## 目次\n\n" + '\n'.join(toc_items) + "\n\n---\n\n"
    return toc_md, '\n'.join(modified_lines)


def markdown_to_html(markdown: str, base_path: Path = None, include_toc: bool = True) -> str:
    """Convert markdown to HTML with full feature support."""

    # Generate TOC if requested
    toc_html = ''
    if include_toc:
        toc_md, markdown = generate_toc(markdown)
        if toc_md:
            # Convert TOC markdown to HTML separately
            toc_html = markdown_to_html_internal(toc_md, base_path)
            toc_html = f'<nav class="toc">{toc_html}</nav>'

    content_html = markdown_to_html_internal(markdown, base_path)

    return toc_html + content_html


def markdown_to_html_internal(markdown: str, base_path: Path = None) -> str:
    """Internal: Convert markdown to HTML with full feature support."""
    html = markdown

    # Process multi-column image sections (<!-- columns --> ... <!-- /columns -->)
    def process_columns(match):
        content = match.group(1)
        # Find all images in the column section
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        if not images:
            return match.group(0)

        column_html = '<div class="image-columns">'
        for alt_text, img_path_str in images:
            if base_path:
                img_path = base_path / img_path_str
            else:
                img_path = Path(img_path_str)

            if img_path.exists():
                data_uri = image_to_data_uri(img_path)
                if data_uri:
                    column_html += f'<figure class="column-item"><img src="{data_uri}" alt="{alt_text}"/><figcaption>{alt_text}</figcaption></figure>'
        column_html += '</div>'
        return column_html

    html = re.sub(r'<!--\s*columns\s*-->(.*?)<!--\s*/columns\s*-->', process_columns, html, flags=re.DOTALL)

    # Process inline multi-image (images on same line become columns)
    def process_inline_columns(match):
        line = match.group(0)
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if len(images) < 2:
            return line  # Not multi-image, return unchanged

        column_html = '<div class="image-columns">'
        for alt_text, img_path_str in images:
            if base_path:
                img_path = base_path / img_path_str
            else:
                img_path = Path(img_path_str)

            if img_path.exists():
                data_uri = image_to_data_uri(img_path)
                if data_uri:
                    column_html += f'<figure class="column-item"><img src="{data_uri}" alt="{alt_text}"/><figcaption>{alt_text}</figcaption></figure>'
        column_html += '</div>'
        return column_html

    # Match lines with 2+ images
    html = re.sub(r'^.*!\[[^\]]*\]\([^)]+\).*!\[[^\]]*\]\([^)]+\).*$', process_inline_columns, html, flags=re.MULTILINE)

    # Process headers with anchors first (extract anchor, create id)
    def header_with_anchor(match):
        hashes = match.group(1)
        title = match.group(2)
        anchor_match = re.search(r'\{#([^}]+)\}', title)
        if anchor_match:
            anchor = anchor_match.group(1)
            title_clean = re.sub(r'\s*\{#[^}]+\}', '', title)
            level = len(hashes)
            return f'<h{level} id="{anchor}">{title_clean}</h{level}>'
        return match.group(0)  # Return unchanged if no anchor

    html = re.sub(r'^(#{1,6})\s+(.+\{#[^}]+\})$', header_with_anchor, html, flags=re.MULTILINE)

    # Remove remaining {#anchor} tags from headers (ones without anchors processed above)
    html = re.sub(r'\s*\{#[^}]+\}', '', html)

    # Process images FIRST (before other conversions)
    # ![alt text](path) -> <figure><img src="..." alt="..."></figure>
    def replace_image(match):
        alt_text = match.group(1)
        img_path_str = match.group(2)

        if base_path:
            img_path = base_path / img_path_str
        else:
            img_path = Path(img_path_str)

        if img_path.exists():
            data_uri = image_to_data_uri(img_path)
            if data_uri:
                return f'<figure><img src="{data_uri}" alt="{alt_text}" style="max-width:100%; height:auto;"/><figcaption>{alt_text}</figcaption></figure>'

        # Return placeholder if image not found
        return f'<figure class="missing-image"><div style="background:#f0f0f0; padding:40px; text-align:center; border:1px dashed #ccc;">[Image: {alt_text}]</div></figure>'

    html = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_image, html)

    # Process blockquotes (> text)
    lines = html.split('\n')
    result_lines = []
    in_blockquote = False
    blockquote_content = []

    for line in lines:
        if line.strip().startswith('> '):
            if not in_blockquote:
                in_blockquote = True
                blockquote_content = []
            blockquote_content.append(line.strip()[2:])
        else:
            if in_blockquote:
                result_lines.append('<blockquote>' + '<br/>'.join(blockquote_content) + '</blockquote>')
                in_blockquote = False
                blockquote_content = []
            result_lines.append(line)

    if in_blockquote:
        result_lines.append('<blockquote>' + '<br/>'.join(blockquote_content) + '</blockquote>')

    html = '\n'.join(result_lines)

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold and italic (be careful with order)
    html = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', html)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<em>\1</em>', html)

    # Links [text](url)
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Horizontal rules
    html = re.sub(r'^---+$', '<hr/>', html, flags=re.MULTILINE)

    # Process markdown tables
    def convert_table(table_lines):
        """Convert markdown table lines to HTML table."""
        if len(table_lines) < 2:
            return '\n'.join(table_lines)

        html_parts = ['<table>']

        # Process header
        header = table_lines[0]
        cells = [c.strip() for c in header.split('|')[1:-1]]  # Remove empty first/last from split
        if not cells:
            cells = [c.strip() for c in header.split('|') if c.strip()]

        html_parts.append('<thead><tr>')
        for cell in cells:
            html_parts.append(f'<th>{cell}</th>')
        html_parts.append('</tr></thead>')

        # Skip separator line (index 1) and process body
        html_parts.append('<tbody>')
        for line in table_lines[2:]:
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if not cells:
                cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                html_parts.append('<tr>')
                for cell in cells:
                    html_parts.append(f'<td>{cell}</td>')
                html_parts.append('</tr>')
        html_parts.append('</tbody></table>')

        return '\n'.join(html_parts)

    # Find and convert tables
    lines = html.split('\n')
    result_lines = []
    table_buffer = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        # Check if line looks like a table row (starts and ends with |, or contains |)
        is_table_line = stripped.startswith('|') and stripped.endswith('|')
        is_separator = re.match(r'^\|[\s\-:|]+\|$', stripped)

        if is_table_line or is_separator:
            in_table = True
            table_buffer.append(stripped)
        else:
            if in_table and table_buffer:
                # End of table, convert it
                result_lines.append(convert_table(table_buffer))
                table_buffer = []
                in_table = False
            result_lines.append(line)

    # Handle table at end of document
    if table_buffer:
        result_lines.append(convert_table(table_buffer))

    html = '\n'.join(result_lines)

    # Process lists (both unordered and ordered)
    lines = html.split('\n')
    in_ul = False
    in_ol = False
    result = []

    for line in lines:
        stripped = line.strip()

        # Check for unordered list
        if stripped.startswith('- ') or stripped.startswith('* '):
            if in_ol:
                result.append('</ol>')
                in_ol = False
            if not in_ul:
                result.append('<ul>')
                in_ul = True
            content = stripped[2:]
            result.append(f'<li>{content}</li>')
        # Check for ordered list (1. 2. etc)
        elif re.match(r'^\d+\.\s', stripped):
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if not in_ol:
                result.append('<ol>')
                in_ol = True
            content = re.sub(r'^\d+\.\s', '', stripped)
            result.append(f'<li>{content}</li>')
        else:
            if in_ul:
                result.append('</ul>')
                in_ul = False
            if in_ol:
                result.append('</ol>')
                in_ol = False
            result.append(line)

    if in_ul:
        result.append('</ul>')
    if in_ol:
        result.append('</ol>')

    html = '\n'.join(result)

    # Paragraphs - wrap text blocks that aren't already in HTML tags
    blocks = html.split('\n\n')
    processed_blocks = []

    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue
        # Skip if already starts with an HTML tag
        if re.match(r'^<(h[1-6]|ul|ol|li|blockquote|figure|hr|p|div|table)', stripped, re.IGNORECASE):
            processed_blocks.append(stripped)
        elif stripped.startswith('<'):
            processed_blocks.append(stripped)
        else:
            # Wrap in paragraph
            processed_blocks.append(f'<p>{stripped}</p>')

    html = '\n'.join(processed_blocks)

    return html


def generate_html_report(
    title: str,
    content: str,
    images: list[dict],
    diagrams: list[dict],
    metadata: dict = None,
    base_path: Path = None
) -> str:
    """Generate full HTML report."""

    metadata = metadata or {}
    date = metadata.get('date', datetime.now().strftime('%Y-%m-%d'))
    author = metadata.get('author', 'Research Report Generator')

    # Convert markdown content to HTML (with base_path for image resolution)
    content_html = markdown_to_html(content, base_path)

    # Build images section
    images_html = ''
    if images:
        images_html = '<div class="images-section"><h2>Figures</h2>'
        for i, img in enumerate(images):
            img_path = Path(img['path'])
            if img_path.exists():
                if img_path.suffix.lower() == '.svg':
                    data_uri = svg_to_data_uri(img_path)
                    images_html += f'''
                    <figure>
                        <img src="{data_uri}" alt="{img.get('caption', '')}"/>
                        <figcaption>Figure {i+1}: {img.get('caption', '')}</figcaption>
                    </figure>
                    '''
        images_html += '</div>'

    # Build diagrams section
    diagrams_html = ''
    if diagrams:
        diagrams_html = '<div class="diagrams-section"><h2>Diagrams</h2>'
        for i, diag in enumerate(diagrams):
            diag_path = Path(diag['path'])
            if diag_path.exists():
                if diag_path.suffix.lower() == '.svg':
                    data_uri = svg_to_data_uri(diag_path)
                    diagrams_html += f'''
                    <figure>
                        <img src="{data_uri}" alt="{diag.get('caption', '')}"/>
                        <figcaption>Diagram {i+1}: {diag.get('caption', '')}</figcaption>
                    </figure>
                    '''
        diagrams_html += '</div>'

    html = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        @page {{
            size: A4;
            margin: 1.2cm 1.5cm;
        }}
        body {{
            font-family: "Inter", "Helvetica Neue", "Arial", "Hiragino Kaku Gothic Pro", "Yu Gothic", sans-serif;
            line-height: 1.8;
            color: #1a1a1a;
            max-width: 100%;
            margin: 0 auto;
            padding: 16px;
            font-size: 20px;
        }}
        h1 {{
            color: #111;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 12px;
            font-size: 38px;
            font-weight: 700;
            margin-bottom: 24px;
        }}
        h2 {{
            color: #1f2937;
            border-left: 4px solid #2563eb;
            padding-left: 16px;
            margin-top: 40px;
            margin-bottom: 16px;
            font-size: 30px;
            font-weight: 600;
        }}
        h3 {{
            color: #374151;
            font-size: 24px;
            font-weight: 600;
            margin-top: 24px;
        }}
        .metadata {{
            color: #7f8c8d;
            font-size: 18px;
            margin-bottom: 30px;
        }}
        p {{
            margin: 16px 0;
            text-align: justify;
            font-size: 20px;
        }}
        ul {{
            margin: 16px 0;
            padding-left: 28px;
        }}
        li {{
            margin: 8px 0;
            font-size: 20px;
        }}
        figure {{
            margin: 20px 0;
            text-align: center;
            page-break-inside: avoid;
        }}
        figure img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        figcaption {{
            font-size: 16px;
            color: #666;
            margin-top: 8px;
            font-style: italic;
        }}
        .images-section, .diagrams-section {{
            margin-top: 40px;
            page-break-before: always;
        }}
        strong {{
            color: #2c3e50;
        }}
        blockquote {{
            margin: 24px 0;
            padding: 16px 24px;
            background: #f8f9fa;
            border-left: 4px solid #2563eb;
            font-style: italic;
            color: #4b5563;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 32px 0;
        }}
        ol {{
            margin: 16px 0;
            padding-left: 28px;
        }}
        ol li {{
            margin: 8px 0;
        }}
        a {{
            color: #2563eb;
            text-decoration: none;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th, td {{
            border: 1px solid #e5e7eb;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f8fafc;
            font-weight: 600;
            color: #1f2937;
        }}
        tr:nth-child(even) {{
            background-color: #f9fafb;
        }}
        .content > h1:first-child {{
            display: none;
        }}
        /* Table of Contents Styles */
        .toc {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px 24px;
            margin: 20px 0 32px 0;
        }}
        .toc h2 {{
            margin-top: 0;
            border-left: none;
            padding-left: 0;
            font-size: 20px;
            color: #1f2937;
        }}
        .toc ul {{
            list-style: none;
            padding-left: 0;
            margin: 12px 0 0 0;
        }}
        .toc li {{
            margin: 6px 0;
            font-size: 14px;
        }}
        .toc li ul {{
            padding-left: 20px;
            margin: 4px 0;
        }}
        .toc li ul li {{
            font-size: 13px;
            color: #4b5563;
        }}
        .toc a {{
            color: #2563eb;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
        /* Multi-column image layout */
        .image-columns {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            justify-content: center;
            margin: 20px 0;
        }}
        .image-columns .column-item {{
            flex: 1 1 calc(50% - 16px);
            max-width: calc(50% - 8px);
            margin: 0;
        }}
        .image-columns .column-item img {{
            max-height: 400px;
            width: auto;
            max-width: 100%;
            object-fit: contain;
            border: none;
        }}
        .image-columns figcaption {{
            font-size: 11px;
            text-align: center;
        }}
        /* Tall image constraint */
        figure img {{
            max-height: 500px;
            width: auto;
            object-fit: contain;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="metadata">
        <p>Date: {date} | Author: {author}</p>
    </div>
    <div class="content">
        {content_html}
    </div>
    {diagrams_html}
    {images_html}
</body>
</html>'''

    return html


def generate_pdf(html_content: str, output_path: Path) -> bool:
    """Generate PDF from HTML content."""
    if not WEASYPRINT_AVAILABLE:
        print("Warning: weasyprint not available, saving HTML instead", file=sys.stderr)
        html_path = output_path.with_suffix('.html')
        html_path.write_text(html_content)
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html_content).write_pdf(output_path)
    return True


def main():
    parser = argparse.ArgumentParser(description='Generate PDF research report')
    parser.add_argument('--title', '-t', required=True, help='Report title')
    parser.add_argument('--content', '-c', required=True, help='Markdown content or path to .md file')
    parser.add_argument('--images', '-i', default='[]', help='JSON array of image objects')
    parser.add_argument('--diagrams', '-d', default='[]', help='JSON array of diagram objects')
    parser.add_argument('--output', '-o', required=True, help='Output PDF path')
    parser.add_argument('--author', default='Research Report Generator', help='Author name')

    args = parser.parse_args()

    # Load content
    content_path = Path(args.content)
    base_path = None
    if content_path.exists():
        content = content_path.read_text()
        base_path = content_path.parent  # Use content file's directory as base for image paths
    else:
        content = args.content

    # Parse images and diagrams
    images = json.loads(args.images)
    diagrams = json.loads(args.diagrams)

    # Generate HTML
    html = generate_html_report(
        title=args.title,
        content=content,
        images=images,
        diagrams=diagrams,
        metadata={'author': args.author},
        base_path=base_path
    )

    # Generate PDF
    output_path = Path(args.output)
    success = generate_pdf(html, output_path)

    if success:
        print(f"Generated PDF: {output_path}")
    else:
        print(f"Generated HTML (weasyprint not available): {output_path.with_suffix('.html')}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
