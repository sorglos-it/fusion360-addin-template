# -*- coding: utf-8 -*-
"""Generate the toolbar icon PNGs for an add-in (standard library only).

    python tools/make_icon.py                 # the template's placeholder
    python tools/make_icon.py --addin MyAddIn # a scaffolded add-in next to it

Fusion wants 16x16, 32x32 and 64x64 PNGs with transparency in the folder
handed to addButtonDefinition. Edit SHAPES below to draw your own - the
polygons are in normalised coordinates, 0..1, with y pointing up.
"""
import os
import zlib
import struct
import argparse

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(_HERE)

DARK = (0x2E, 0x3A, 0x45)
ACCENT = (0xE8, 0x8A, 0x1E)
SS = 4  # supersampling factor, 4 gives clean edges down to 16 px

# Placeholder glyph: a bracketed frame with a diagonal through it. Obviously a
# placeholder, which is the point - replace it before you ship.
SHAPES = [
    # (colour, polygon)
    (DARK, [(0.12, 0.12), (0.40, 0.12), (0.40, 0.23), (0.23, 0.23), (0.23, 0.40), (0.12, 0.40)]),
    (DARK, [(0.88, 0.12), (0.88, 0.40), (0.77, 0.40), (0.77, 0.23), (0.60, 0.23), (0.60, 0.12)]),
    (DARK, [(0.12, 0.88), (0.12, 0.60), (0.23, 0.60), (0.23, 0.77), (0.40, 0.77), (0.40, 0.88)]),
    (DARK, [(0.88, 0.88), (0.60, 0.88), (0.60, 0.77), (0.77, 0.77), (0.77, 0.60), (0.88, 0.60)]),
    (ACCENT, [(0.30, 0.36), (0.64, 0.70), (0.70, 0.64), (0.36, 0.30)]),
]


def point_in_polygon(x, y, polygon):
    inside = False
    count = len(polygon)
    j = count - 1
    for i in range(count):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y):
            crossing = xi + (y - yi) * (xj - xi) / (yj - yi)
            if x < crossing:
                inside = not inside
        j = i
    return inside


def render(size):
    buffer = bytearray(size * size * 4)
    for py in range(size):
        for px in range(size):
            # Coverage per colour, later shapes painting over earlier ones.
            red = green = blue = 0.0
            alpha = 0.0
            for colour, polygon in SHAPES:
                hits = 0
                for sy in range(SS):
                    for sx in range(SS):
                        gx = (px + (sx + 0.5) / SS) / size
                        gy = 1.0 - (py + (sy + 0.5) / SS) / size
                        if point_in_polygon(gx, gy, polygon):
                            hits += 1
                if not hits:
                    continue
                coverage = (hits / float(SS * SS)) * (1.0 - alpha)
                red += colour[0] * coverage
                green += colour[1] * coverage
                blue += colour[2] * coverage
                alpha += coverage

            if alpha <= 0.0:
                continue
            i = (py * size + px) * 4
            buffer[i] = int(round(red / alpha))
            buffer[i + 1] = int(round(green / alpha))
            buffer[i + 2] = int(round(blue / alpha))
            buffer[i + 3] = int(round(alpha * 255))
    return bytes(buffer)


def write_png(path, size, rgba):
    raw = b''.join(b'\x00' + rgba[y * size * 4:(y + 1) * size * 4]
                   for y in range(size))

    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data +
                struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff))

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 9))
    png += chunk(b'IEND', b'')
    with open(path, 'wb') as handle:
        handle.write(png)


def main():
    parser = argparse.ArgumentParser(description='Generate add-in toolbar icons.')
    parser.add_argument('--addin', default='AddInTemplate',
                        help='add-in folder name (default: AddInTemplate)')
    parser.add_argument('--root', default=REPO,
                        help='folder holding the add-in (default: this repository)')
    args = parser.parse_args()

    out = os.path.join(args.root, args.addin, 'resources', args.addin)
    os.makedirs(out, exist_ok=True)
    for size in (16, 32, 64):
        path = os.path.join(out, '%dx%d.png' % (size, size))
        write_png(path, size, render(size))
        print('written:', path)


if __name__ == '__main__':
    main()
