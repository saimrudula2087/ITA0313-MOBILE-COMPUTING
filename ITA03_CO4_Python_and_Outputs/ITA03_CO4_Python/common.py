import io, sys, contextlib, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

def table(headers, rows, widths=None):
    widths = widths or [max(len(str(x)) for x in [h]+[r[i] for r in rows]) for i,h in enumerate(headers)]
    line = "+" + "+".join("-"*(w+2) for w in widths) + "+"
    def fmt(r): return "| " + " | ".join(str(c).ljust(w) for c,w in zip(r,widths)) + " |"
    return "\n".join([line, fmt(headers), line] + [fmt(r) for r in rows] + [line])

def wrap(text, n):
    import textwrap
    out=[]
    for l in text.split("\n"):
        out.append(l if (len(l)<=n or l.startswith(("|","+"))) else textwrap.fill(l, n, subsequent_indent="    "))
    return "\n".join(out)

def save_text_png(name, text, width_chars=150):
    text = wrap(text, width_chars)
    lines = text.split("\n"); maxlen = max(len(l) for l in lines)
    w = max(10, maxlen*0.068+0.5); h = max(2.5, 0.19*len(lines)+0.6)
    fig = plt.figure(figsize=(w, h), facecolor="#0d1117")
    fig.text(0.008, 0.995, text, family="DejaVu Sans Mono", fontsize=8, color="#e6edf3", va="top", ha="left")
    fig.savefig(f"{OUT}/{name}.png", dpi=100, facecolor=fig.get_facecolor())
    plt.close(fig)

class Capture:
    def __init__(self, name): self.name = name
    def __enter__(self):
        self.buf = io.StringIO(); self.ctx = contextlib.redirect_stdout(self.buf); self.ctx.__enter__(); return self
    def __exit__(self, *a):
        self.ctx.__exit__(*a)
        txt = self.buf.getvalue(); sys.stdout.write(txt); save_text_png(self.name, txt)
