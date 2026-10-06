"""Subset JetBrains Mono to the characters a graphic uses and return a base64 @font-face."""
import base64, io, pathlib
from fontTools import subset
from fontTools.ttLib import TTFont

FONTS = pathlib.Path(__file__).parent / "fonts"

def font_face(text: str, weight: int = 400, family: str = "JBM") -> str:
    src = FONTS / f"jetbrains-mono-latin-{weight}-normal.woff2"
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = []
    opts.notdef_outline = True
    font = TTFont(str(src))
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(set(text))) + " ")
    sub.subset(font)
    font.flavor = "woff2"
    buf = io.BytesIO()
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
