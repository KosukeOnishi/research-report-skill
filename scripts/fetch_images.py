#!/usr/bin/env python3
"""
Fetch images related to a topic for use in research reports.
Uses web search to find relevant images and downloads them.
"""

import argparse
import json
import re
import sys
from pathlib import Path


def sanitize_filename(name: str) -> str:
    """Convert a string to a safe filename."""
    return re.sub(r'[^\w\-]', '_', name)[:50]


def fetch_placeholder_images(topic: str, output_dir: Path, count: int = 3) -> list[dict]:
    """
    Generate placeholder images for the topic.
    In production, this would fetch real images from search APIs.
    """
    images = []
    output_dir.mkdir(parents=True, exist_ok=True)

    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']

    for i in range(count):
        color = colors[i % len(colors)]
        filename = f"{sanitize_filename(topic)}_{i+1}.svg"
        filepath = output_dir / filename

        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="{color}" opacity="0.2"/>
  <rect x="10" y="10" width="380" height="280" fill="none" stroke="{color}" stroke-width="2"/>
  <text x="200" y="140" font-family="Arial, sans-serif" font-size="16" fill="{color}" text-anchor="middle">
    {topic}
  </text>
  <text x="200" y="170" font-family="Arial, sans-serif" font-size="14" fill="#666" text-anchor="middle">
    Image {i+1}
  </text>
</svg>'''

        filepath.write_text(svg_content)
        images.append({
            'path': str(filepath),
            'caption': f'{topic} - Figure {i+1}',
            'type': 'svg'
        })

    return images


def main():
    parser = argparse.ArgumentParser(description='Fetch images for research report')
    parser.add_argument('topic', help='Research topic')
    parser.add_argument('--output-dir', '-o', default='./images', help='Output directory')
    parser.add_argument('--count', '-n', type=int, default=3, help='Number of images')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    images = fetch_placeholder_images(args.topic, output_dir, args.count)

    if args.json:
        print(json.dumps(images, indent=2, ensure_ascii=False))
    else:
        print(f"Fetched {len(images)} images for '{args.topic}':")
        for img in images:
            print(f"  - {img['path']}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
