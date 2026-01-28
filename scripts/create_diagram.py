#!/usr/bin/env python3
"""
Create diagrams for research reports.
Generates comparison tables, flowcharts, bar charts, pie charts, and other visual elements.
"""

import argparse
import json
import math
import sys
from pathlib import Path


def create_bar_chart_svg(data: list[dict], title: str, output_path: Path,
                         bar_color: str = "#2563eb", show_values: bool = True) -> dict:
    """
    Create a horizontal bar chart SVG.

    data format: [{"label": "Item A", "value": 75}, {"label": "Item B", "value": 50}, ...]
    """
    if not data:
        return None

    # Dimensions
    padding = 40
    label_width = 200
    bar_height = 35
    bar_gap = 15
    chart_width = 400

    width = padding * 2 + label_width + chart_width + 60
    height = padding * 2 + len(data) * (bar_height + bar_gap) + 40

    max_value = max(item.get('value', 0) for item in data)
    if max_value == 0:
        max_value = 100

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>',
        '  .title { font-family: Inter, Arial, sans-serif; font-size: 18px; font-weight: 600; fill: #1a1a1a; }',
        '  .label { font-family: Inter, Arial, sans-serif; font-size: 13px; fill: #374151; }',
        '  .value { font-family: Inter, Arial, sans-serif; font-size: 12px; font-weight: 600; fill: #1f2937; }',
        '  .bar { rx: 4; }',
        '  .axis { stroke: #e5e7eb; stroke-width: 1; }',
        '</style>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width/2}" y="{padding - 10}" text-anchor="middle" class="title">{title}</text>',
    ]

    # Draw bars
    y_start = padding + 20
    for i, item in enumerate(data):
        y = y_start + i * (bar_height + bar_gap)
        value = item.get('value', 0)
        label = item.get('label', f'Item {i+1}')

        # Truncate label if too long
        display_label = label[:28] + '...' if len(label) > 28 else label

        bar_width = (value / max_value) * chart_width
        x_bar = padding + label_width

        # Label
        svg_parts.append(f'<text x="{padding + label_width - 10}" y="{y + bar_height/2 + 5}" text-anchor="end" class="label">{display_label}</text>')

        # Bar background
        svg_parts.append(f'<rect x="{x_bar}" y="{y}" width="{chart_width}" height="{bar_height}" fill="#f3f4f6" class="bar"/>')

        # Bar
        if bar_width > 0:
            svg_parts.append(f'<rect x="{x_bar}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{bar_color}" class="bar"/>')

        # Value
        if show_values:
            unit = item.get('unit', '%')
            value_text = f"{value}{unit}"
            svg_parts.append(f'<text x="{x_bar + bar_width + 8}" y="{y + bar_height/2 + 5}" class="value">{value_text}</text>')

    svg_parts.append('</svg>')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(svg_parts))

    return {
        'path': str(output_path),
        'caption': title,
        'type': 'bar_chart'
    }


def create_pie_chart_svg(data: list[dict], title: str, output_path: Path) -> dict:
    """
    Create a pie chart SVG.

    data format: [{"label": "Item A", "value": 30}, {"label": "Item B", "value": 70}, ...]
    """
    if not data:
        return None

    # Dimensions
    width = 500
    height = 350
    cx, cy = 180, 175
    radius = 120

    total = sum(item.get('value', 0) for item in data)
    if total == 0:
        total = 1

    colors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#84cc16']

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>',
        '  .title { font-family: Inter, Arial, sans-serif; font-size: 18px; font-weight: 600; fill: #1a1a1a; }',
        '  .legend-label { font-family: Inter, Arial, sans-serif; font-size: 12px; fill: #374151; }',
        '  .legend-value { font-family: Inter, Arial, sans-serif; font-size: 12px; font-weight: 600; fill: #1f2937; }',
        '</style>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width/2}" y="30" text-anchor="middle" class="title">{title}</text>',
    ]

    # Draw pie slices
    start_angle = -90  # Start from top
    for i, item in enumerate(data):
        value = item.get('value', 0)
        percentage = (value / total) * 100
        angle = (value / total) * 360

        color = colors[i % len(colors)]

        # Calculate arc
        end_angle = start_angle + angle

        # Convert to radians
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)

        # Calculate points
        x1 = cx + radius * math.cos(start_rad)
        y1 = cy + radius * math.sin(start_rad)
        x2 = cx + radius * math.cos(end_rad)
        y2 = cy + radius * math.sin(end_rad)

        # Large arc flag
        large_arc = 1 if angle > 180 else 0

        # Draw slice
        if angle < 360:
            path = f'M {cx},{cy} L {x1},{y1} A {radius},{radius} 0 {large_arc},1 {x2},{y2} Z'
        else:
            # Full circle
            path = f'M {cx},{cy - radius} A {radius},{radius} 0 1,1 {cx},{cy + radius} A {radius},{radius} 0 1,1 {cx},{cy - radius} Z'

        svg_parts.append(f'<path d="{path}" fill="{color}" stroke="#ffffff" stroke-width="2"/>')

        start_angle = end_angle

    # Legend
    legend_x = 330
    legend_y = 70
    for i, item in enumerate(data):
        y = legend_y + i * 32
        label = item.get('label', f'Item {i+1}')[:15]
        value = item.get('value', 0)
        percentage = (value / total) * 100
        color = colors[i % len(colors)]

        svg_parts.append(f'<rect x="{legend_x}" y="{y}" width="16" height="16" fill="{color}" rx="2"/>')
        svg_parts.append(f'<text x="{legend_x + 24}" y="{y + 12}" class="legend-label">{label}</text>')
        svg_parts.append(f'<text x="{legend_x + 24}" y="{y + 26}" class="legend-value">{percentage:.1f}%</text>')

    svg_parts.append('</svg>')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(svg_parts))

    return {
        'path': str(output_path),
        'caption': title,
        'type': 'pie_chart'
    }


def create_stat_cards_svg(data: list[dict], title: str, output_path: Path) -> dict:
    """
    Create stat cards showing key metrics.

    data format: [{"label": "ROI", "value": "9,900%", "description": "Return on UX investment"}, ...]
    """
    if not data:
        return None

    card_width = 180
    card_height = 100
    gap = 20
    cols = min(len(data), 4)
    rows = math.ceil(len(data) / cols)

    padding = 30
    width = padding * 2 + cols * card_width + (cols - 1) * gap
    height = padding * 2 + rows * card_height + (rows - 1) * gap + 40

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>',
        '  .title { font-family: Inter, Arial, sans-serif; font-size: 18px; font-weight: 600; fill: #1a1a1a; }',
        '  .stat-value { font-family: Inter, Arial, sans-serif; font-size: 28px; font-weight: 700; fill: #2563eb; }',
        '  .stat-label { font-family: Inter, Arial, sans-serif; font-size: 12px; font-weight: 600; fill: #374151; }',
        '  .stat-desc { font-family: Inter, Arial, sans-serif; font-size: 10px; fill: #6b7280; }',
        '  .card { fill: #f8fafc; stroke: #e2e8f0; stroke-width: 1; rx: 8; }',
        '</style>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width/2}" y="{padding}" text-anchor="middle" class="title">{title}</text>',
    ]

    y_start = padding + 30
    for i, item in enumerate(data):
        col = i % cols
        row = i // cols
        x = padding + col * (card_width + gap)
        y = y_start + row * (card_height + gap)

        value = str(item.get('value', ''))
        label = item.get('label', '')[:20]
        desc = item.get('description', '')[:30]

        # Card background
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{card_width}" height="{card_height}" class="card"/>')

        # Value
        svg_parts.append(f'<text x="{x + card_width/2}" y="{y + 40}" text-anchor="middle" class="stat-value">{value}</text>')

        # Label
        svg_parts.append(f'<text x="{x + card_width/2}" y="{y + 60}" text-anchor="middle" class="stat-label">{label}</text>')

        # Description
        if desc:
            svg_parts.append(f'<text x="{x + card_width/2}" y="{y + 80}" text-anchor="middle" class="stat-desc">{desc}</text>')

    svg_parts.append('</svg>')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(svg_parts))

    return {
        'path': str(output_path),
        'caption': title,
        'type': 'stat_cards'
    }


def create_comparison_table_svg(items: list[dict], title: str, output_path: Path) -> dict:
    """Create an SVG comparison table."""
    num_items = len(items)
    if num_items == 0:
        return None

    # Calculate dimensions
    col_width = 180
    row_height = 40
    header_height = 50
    padding = 20
    
    # Get all unique keys from items
    all_keys = []
    for item in items:
        for key in item.keys():
            if key not in all_keys and key != 'name':
                all_keys.append(key)
    
    width = padding * 2 + col_width * (num_items + 1)
    height = padding * 2 + header_height + row_height * (len(all_keys) + 1)

    # Build SVG
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>',
        '  .header { font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; fill: #2c3e50; }',
        '  .cell { font-family: Arial, sans-serif; font-size: 12px; fill: #34495e; }',
        '  .title { font-family: Arial, sans-serif; font-size: 16px; font-weight: bold; fill: #2c3e50; }',
        '</style>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
    ]

    # Title
    svg_parts.append(f'<text x="{width/2}" y="25" text-anchor="middle" class="title">{title}</text>')

    y_start = padding + header_height
    x_start = padding

    # Header row background
    svg_parts.append(f'<rect x="{x_start}" y="{y_start - row_height}" width="{width - padding*2}" height="{row_height}" fill="#3498db" opacity="0.2"/>')

    # Column headers (item names)
    svg_parts.append(f'<text x="{x_start + 10}" y="{y_start - 12}" class="header">Feature</text>')
    for i, item in enumerate(items):
        x = x_start + col_width * (i + 1) + 10
        name = item.get('name', f'Item {i+1}')
        svg_parts.append(f'<text x="{x}" y="{y_start - 12}" class="header">{name}</text>')

    # Data rows
    for row_idx, key in enumerate(all_keys):
        y = y_start + row_height * row_idx
        
        # Alternating row background
        if row_idx % 2 == 0:
            svg_parts.append(f'<rect x="{x_start}" y="{y}" width="{width - padding*2}" height="{row_height}" fill="#ecf0f1"/>')
        
        # Row label
        svg_parts.append(f'<text x="{x_start + 10}" y="{y + 25}" class="cell">{key.replace("_", " ").title()}</text>')
        
        # Cell values
        for i, item in enumerate(items):
            x = x_start + col_width * (i + 1) + 10
            value = str(item.get(key, '-'))[:20]
            svg_parts.append(f'<text x="{x}" y="{y + 25}" class="cell">{value}</text>')

    # Grid lines
    svg_parts.append(f'<rect x="{x_start}" y="{y_start - row_height}" width="{width - padding*2}" height="{row_height * (len(all_keys) + 1)}" fill="none" stroke="#bdc3c7"/>')

    svg_parts.append('</svg>')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(svg_parts))

    return {
        'path': str(output_path),
        'caption': title,
        'type': 'comparison_table'
    }


def create_flowchart_svg(steps: list[str], title: str, output_path: Path) -> dict:
    """Create a simple flowchart SVG."""
    box_width = 200
    box_height = 50
    gap = 30
    padding = 40
    
    width = box_width + padding * 2
    height = len(steps) * (box_height + gap) + padding * 2

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>',
        '  .box { fill: #3498db; stroke: #2980b9; stroke-width: 2; rx: 8; }',
        '  .text { font-family: Arial, sans-serif; font-size: 12px; fill: white; text-anchor: middle; }',
        '  .arrow { stroke: #7f8c8d; stroke-width: 2; fill: none; marker-end: url(#arrowhead); }',
        '  .title { font-family: Arial, sans-serif; font-size: 14px; font-weight: bold; fill: #2c3e50; }',
        '</style>',
        '<defs>',
        '  <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">',
        '    <polygon points="0 0, 10 3.5, 0 7" fill="#7f8c8d"/>',
        '  </marker>',
        '</defs>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
    ]

    x = padding
    for i, step in enumerate(steps):
        y = padding + i * (box_height + gap)
        
        # Box
        svg_parts.append(f'<rect x="{x}" y="{y}" width="{box_width}" height="{box_height}" class="box"/>')
        
        # Text (truncate if too long)
        text = step[:25] + ('...' if len(step) > 25 else '')
        svg_parts.append(f'<text x="{x + box_width/2}" y="{y + box_height/2 + 5}" class="text">{text}</text>')
        
        # Arrow to next box
        if i < len(steps) - 1:
            arrow_y = y + box_height
            svg_parts.append(f'<line x1="{x + box_width/2}" y1="{arrow_y}" x2="{x + box_width/2}" y2="{arrow_y + gap - 5}" class="arrow"/>')

    svg_parts.append('</svg>')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text('\n'.join(svg_parts))

    return {
        'path': str(output_path),
        'caption': title,
        'type': 'flowchart'
    }


def main():
    parser = argparse.ArgumentParser(description='Create diagrams for research report')
    parser.add_argument('--type', '-t', choices=['comparison', 'flowchart', 'bar', 'pie', 'stats'], default='comparison',
                        help='Type of diagram: comparison, flowchart, bar (bar chart), pie (pie chart), stats (stat cards)')
    parser.add_argument('--data', '-d', required=True, help='JSON data for diagram')
    parser.add_argument('--title', required=True, help='Diagram title')
    parser.add_argument('--output', '-o', required=True, help='Output file path')
    parser.add_argument('--color', default='#2563eb', help='Primary color for charts')
    parser.add_argument('--json', action='store_true', help='Output result as JSON')

    args = parser.parse_args()

    data = json.loads(args.data)
    output_path = Path(args.output)

    if args.type == 'comparison':
        result = create_comparison_table_svg(data, args.title, output_path)
    elif args.type == 'flowchart':
        result = create_flowchart_svg(data, args.title, output_path)
    elif args.type == 'bar':
        result = create_bar_chart_svg(data, args.title, output_path, bar_color=args.color)
    elif args.type == 'pie':
        result = create_pie_chart_svg(data, args.title, output_path)
    elif args.type == 'stats':
        result = create_stat_cards_svg(data, args.title, output_path)
    else:
        print(f"Unknown diagram type: {args.type}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Created {args.type} diagram: {result['path']}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
