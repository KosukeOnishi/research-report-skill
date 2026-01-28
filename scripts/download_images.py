#!/usr/bin/env python3
"""
Download and optimize images from URLs for research reports.
- Downloads images from URLs
- Converts PNG to JPG
- Resizes to max 800px width
- Compresses to 85% quality
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from io import BytesIO

import requests
from PIL import Image


def sanitize_filename(url: str) -> str:
    """Create a safe filename from URL hash."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    return url_hash


def download_image(url: str, output_dir: Path, timeout: int = 30) -> dict | None:
    """Download an image from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type.lower():
            return None

        filename = sanitize_filename(url)

        # Determine extension from content type
        if 'png' in content_type:
            ext = '.png'
        elif 'gif' in content_type:
            ext = '.gif'
        elif 'webp' in content_type:
            ext = '.webp'
        elif 'svg' in content_type:
            ext = '.svg'
        else:
            ext = '.jpg'

        output_path = output_dir / f"{filename}{ext}"
        output_path.write_bytes(response.content)

        return {
            'path': str(output_path),
            'url': url,
            'size': len(response.content),
            'format': ext
        }
    except Exception as e:
        print(f"Failed to download {url}: {e}", file=sys.stderr)
        return None


def optimize_image(input_path: Path, output_dir: Path, max_width: int = 800, quality: int = 85) -> dict | None:
    """
    Optimize an image:
    - Convert PNG to JPG (unless transparent)
    - Resize to max_width
    - Compress to specified quality
    """
    try:
        with Image.open(input_path) as img:
            original_size = input_path.stat().st_size
            original_format = img.format

            # Get dimensions
            width, height = img.size

            # Skip very small images (likely icons/logos)
            if width < 200 or height < 100:
                return None

            # Calculate new size if needed
            if width > max_width:
                ratio = max_width / width
                new_height = int(height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Determine output format
            has_transparency = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)

            if has_transparency:
                # Keep PNG for transparent images
                output_format = 'PNG'
                ext = '.png'
            else:
                # Convert to JPEG
                output_format = 'JPEG'
                ext = '.jpg'
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

            # Generate output filename
            output_filename = input_path.stem + '_optimized' + ext
            output_path = output_dir / output_filename

            # Save with optimization
            if output_format == 'JPEG':
                img.save(output_path, format=output_format, quality=quality, optimize=True)
            else:
                img.save(output_path, format=output_format, optimize=True)

            new_size = output_path.stat().st_size

            return {
                'path': str(output_path),
                'original_path': str(input_path),
                'original_size': original_size,
                'new_size': new_size,
                'width': img.size[0],
                'height': img.size[1],
                'format': ext,
                'compression_ratio': round(new_size / original_size, 2) if original_size > 0 else 1.0
            }
    except Exception as e:
        print(f"Failed to optimize {input_path}: {e}", file=sys.stderr)
        return None


def process_images(urls: list[str], pool_dir: Path, output_dir: Path, max_width: int = 800, quality: int = 85) -> dict:
    """Download and optimize multiple images."""
    pool_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    optimized = []
    failed = []

    # Download all images
    for url in urls:
        result = download_image(url, pool_dir)
        if result:
            downloaded.append(result)
        else:
            failed.append({'url': url, 'reason': 'download_failed'})

    # Optimize downloaded images
    for img_info in downloaded:
        input_path = Path(img_info['path'])
        if input_path.suffix.lower() == '.svg':
            # SVGs don't need optimization, just copy
            import shutil
            output_path = output_dir / input_path.name
            shutil.copy(input_path, output_path)
            optimized.append({
                'path': str(output_path),
                'url': img_info['url'],
                'format': '.svg'
            })
        else:
            result = optimize_image(input_path, output_dir, max_width, quality)
            if result:
                result['url'] = img_info['url']
                optimized.append(result)
            else:
                failed.append({'url': img_info['url'], 'reason': 'optimization_failed'})

    return {
        'downloaded': len(downloaded),
        'optimized': len(optimized),
        'failed': len(failed),
        'images': optimized,
        'failures': failed
    }


def main():
    parser = argparse.ArgumentParser(description='Download and optimize images')
    parser.add_argument('--urls', '-u', help='JSON array of URLs or comma-separated URLs')
    parser.add_argument('--url-file', '-f', help='File containing URLs (one per line)')
    parser.add_argument('--pool-dir', '-p', default='./images/pool', help='Directory for raw downloads')
    parser.add_argument('--output-dir', '-o', default='./images/optimized', help='Directory for optimized images')
    parser.add_argument('--max-width', '-w', type=int, default=800, help='Max width in pixels')
    parser.add_argument('--quality', '-q', type=int, default=85, help='JPEG quality (0-100)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    # Collect URLs
    urls = []
    if args.urls:
        try:
            urls = json.loads(args.urls)
        except json.JSONDecodeError:
            urls = [u.strip() for u in args.urls.split(',') if u.strip()]

    if args.url_file:
        url_path = Path(args.url_file)
        if url_path.exists():
            urls.extend([line.strip() for line in url_path.read_text().splitlines() if line.strip() and not line.startswith('#')])

    if not urls:
        print("No URLs provided", file=sys.stderr)
        return 1

    result = process_images(
        urls,
        Path(args.pool_dir),
        Path(args.output_dir),
        args.max_width,
        args.quality
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Downloaded: {result['downloaded']}")
        print(f"Optimized: {result['optimized']}")
        print(f"Failed: {result['failed']}")
        for img in result['images']:
            print(f"  {img['path']}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
