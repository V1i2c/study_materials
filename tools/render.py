import pymupdf, sys, os
pdf, outdir = sys.argv[1], sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv)>3 else 160
pages = None
if len(sys.argv)>4:
    pages=[int(x)-1 for x in sys.argv[4].split(',')]
os.makedirs(outdir, exist_ok=True)
d = pymupdf.open(pdf)
m = pymupdf.Matrix(dpi/72, dpi/72)
for i,p in enumerate(d):
    if pages is not None and i not in pages: continue
    pm = p.get_pixmap(matrix=m)
    pm.save(os.path.join(outdir, f"page_{i+1:03d}.png"))
print("rendered", len(d) if pages is None else len(pages), "pages ->", outdir)
