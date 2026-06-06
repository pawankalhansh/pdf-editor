#!/usr/bin/env python3
"""Standalone PDF decoloring tool.

Removes colored backgrounds from PDF files, preserving black/gray text.
This is a deterministic tool - same input always produces the same output.

Usage:
    python decolor_pdf.py input.pdf
    python decolor_pdf.py input.pdf --threshold 80
    python decolor_pdf.py input.pdf -o output.pdf
"""

import argparse
import os
import sys
import time
from pdf_tools import decolor_pdf


def main():
    parser = argparse.ArgumentParser(
        description='Remove colored backgrounds from PDF files, keeping black/gray text.'
    )
    parser.add_argument('input', help='Input PDF file path')
    parser.add_argument(
        '-o', '--output', help='Output PDF file path (default: <name>-decolored.pdf)'
    )
    parser.add_argument(
        '-t', '--threshold', type=int, default=60,
        help='Color difference threshold (0-255). Higher = more aggressive color removal. Default: 60'
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File '{args.input}' not found.")
        sys.exit(1)

    if not args.input.lower().endswith('.pdf'):
        print("Error: Input file must be a PDF.")
        sys.exit(1)

    if args.output:
        output_path = args.output
    else:
        base = os.path.splitext(args.input)[0]
        output_path = f"{base}-decolored.pdf"

    print(f"Processing: {args.input}")
    print(f"Threshold:  {args.threshold}")
    print(f"Output:     {output_path}")
    print()

    start = time.time()
    try:
        decolor_pdf(args.input, output_path, threshold=args.threshold)
        elapsed = time.time() - start

        orig_size = os.path.getsize(args.input)
        new_size = os.path.getsize(output_path)

        print(f"Done in {elapsed:.1f}s")
        print(f"Original: {orig_size/1024:.1f} KB")
        print(f"Output:   {new_size/1024:.1f} KB")
        print(f"\nSaved to: {output_path}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
