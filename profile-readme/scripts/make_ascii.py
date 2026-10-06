"""Turn a photo into ascii.svg: a character ramp on an exact monospace grid.
Usage: python scripts/make_ascii.py photo.jpg ascii.svg [cols]"""
import sys
from PIL import Image, ImageOps, ImageFilter
from svgfont import font_face

RAMP = " .'`,:;-~+=*i1tfLCOZ0#%&8@"   # quiet -> loud
ADV, LH, FS = 0.6, 1.15, 10  # advance (em), line height (em), font size (px)

def build(src, out, cols=96):
    im = Image.open(src)
    im = ImageOps.exif_transpose(im).convert("L")
    # crop slightly into the subject (trim 4% off each side)
    w, h = im.size
    im = im.crop((int(w*.04), int(h*.05), int(w*.98), int(h*.66)))   # head and shoulders
    w, h = im.size
    cw, ch = FS*ADV, FS*LH
    rows = round(cols * (h/w) * (cw/ch))
    im = im.resize((cols, rows), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 90, 2))
    im = ImageOps.autocontrast(im, cutoff=2)
    im = im.point(lambda v: int(255 * (1 - (v/255)) ** 1.15))   # ink density: dark pixels -> loud
    # vignette: fade the wall and edges into the dark panel
    import math
    px = im.load()
    for y in range(rows):
        for x in range(cols):
            dx, dy = (x/cols - .5) / .5, (y/rows - .46) / .55
            f = max(0.0, 1 - max(0.0, math.hypot(dx*.95, dy) - .55) / .55)
            px[x, y] = int(px[x, y] * f)
    lines = []
    for y in range(rows):
        row = "".join(RAMP[min(len(RAMP)-1, px[x, y]*len(RAMP)//256)] for x in range(cols))
        lines.append(row.rstrip())
    W, H = cols*cw + 24, rows*ch + 24
    face = font_face(RAMP, 400)
    body = []
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        esc = ln.replace("&", "&amp;").replace("<", "&lt;")
        y = 12 + (i+1)*ch - 2.5
        body.append(
            f'<text x="12" y="{y:.2f}" textLength="{len(ln)*cw:.2f}" lengthAdjust="spacing" opacity="0">{esc}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{i*0.035:.3f}s" dur="0.5s" fill="freeze"/></text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" role="img" aria-label="ASCII portrait">
<style>{face}
text{{font-family:'JBM','JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;font-size:{FS}px;fill:#1f2328;white-space:pre;font-weight:400}}
</style>
<rect width="100%" height="100%" rx="12" fill="#f6f8fa"/>
<g xml:space="preserve">
{chr(10).join(body)}
</g>
<rect x="0" y="0" width="{W:.0f}" height="3" fill="#2da44e" opacity="0.25">
<animateTransform attributeName="transform" type="translate" values="0 0; 0 {H:.0f}; 0 0" dur="9s" begin="{len(lines)*0.035+0.6:.2f}s" repeatCount="indefinite"/></rect>
</svg>'''
    open(out, "w", encoding="utf-8").write(svg)
    print(f"{cols}x{rows} chars, {len(svg)/1024:.1f} KB")
    return lines

if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 96)
