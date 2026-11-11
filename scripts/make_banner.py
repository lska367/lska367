#!/usr/bin/env python3
"""Generate the light/dark profile banners (assets/banner-{light,dark}.svg).

Run:  python3 scripts/make_banner.py
GitHub renders these through <picture> with prefers-color-scheme, so both
files must share identical geometry — only the palette differs.
"""

from pathlib import Path

W, H = 1280, 280
OUT = Path(__file__).resolve().parent.parent / "assets"

PALETTES = {
    "light": {
        "bg_from": "#F8FAFF",
        "bg_to": "#E6EFFE",
        "dot": "#0B1220",
        "dot_opacity": "0.055",
        "name": "#0B1220",
        "handle": "#5B6B85",
        "role": "#1F2937",
        "role_strong": "#0B1220",
        "role_sub": "#4B5563",
        "mono_fill": "#FFFFFF",
        "mono_fill_opacity": "0.55",
        "mono_text": "#1D3A8A",
        "blob_a": "#3B82F6",
        "blob_b": "#8B5CF6",
        "blob_opacity": "0.20",
    },
    "dark": {
        "bg_from": "#0B1220",
        "bg_to": "#101C33",
        "dot": "#FFFFFF",
        "dot_opacity": "0.05",
        "name": "#F3F7FF",
        "handle": "#93A6C4",
        "role": "#D7E2F5",
        "role_strong": "#FFFFFF",
        "role_sub": "#A9BAD4",
        "mono_fill": "#0F1729",
        "mono_fill_opacity": "0.60",
        "mono_text": "#D6E4FF",
        "blob_a": "#3B82F6",
        "blob_b": "#8B5CF6",
        "blob_opacity": "0.30",
    },
}

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Kai Yang — Big Data Development Intern at ByteDance; M.S. in AI at ECNU">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="{w}" y2="{h}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{bg_from}"/>
      <stop offset="1" stop-color="{bg_to}"/>
    </linearGradient>
    <linearGradient id="accent" x1="64" y1="0" x2="232" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#2563EB"/>
      <stop offset="0.55" stop-color="#4F46E5"/>
      <stop offset="1" stop-color="#8B5CF6"/>
    </linearGradient>
    <radialGradient id="blobA" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{blob_a}" stop-opacity="{blob_opacity}"/>
      <stop offset="1" stop-color="{blob_a}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="blobB" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{blob_b}" stop-opacity="{blob_opacity}"/>
      <stop offset="1" stop-color="{blob_b}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="1.2" fill="{dot}" opacity="{dot_opacity}"/>
    </pattern>
  </defs>

  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  <circle cx="1140" cy="10" r="300" fill="url(#blobA)"/>
  <circle cx="1010" cy="270" r="260" fill="url(#blobB)"/>
  <rect width="{w}" height="{h}" fill="url(#dots)"/>

  <g font-family="'Segoe UI', -apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Ubuntu, Helvetica, Arial, sans-serif">
    <text x="64" y="102" font-size="54" font-weight="700" letter-spacing="-1.2" fill="{name}">Kai Yang</text>
    <text x="64" y="136" font-size="19" fill="{handle}">杨锴 · lska367 · M.S. in AI, ECNU</text>

    <rect x="64" y="158" width="168" height="4" rx="2" fill="url(#accent)"/>

    <text x="64" y="200" font-size="23" fill="{role}">Big Data Development Intern @ <tspan font-weight="600" fill="{role_strong}">ByteDance</tspan> · International Ads &amp; Transactions</text>
    <text x="64" y="230" font-size="23" fill="{role_sub}">TikTok Ads conversion attribution &amp; data pipeline optimization</text>
  </g>

  <g transform="translate(1052, 84)">
    <rect width="132" height="132" rx="30" fill="none" stroke="url(#accent)" stroke-width="2"/>
    <rect x="9" y="9" width="114" height="114" rx="24" fill="{mono_fill}" opacity="{mono_fill_opacity}"/>
    <text x="66" y="80" text-anchor="middle" font-size="44" font-weight="700" letter-spacing="-1"
          font-family="'Segoe UI', -apple-system, Ubuntu, Helvetica, Arial, sans-serif" fill="{mono_text}">KY</text>
  </g>
</svg>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, palette in PALETTES.items():
        svg = TEMPLATE.format(w=W, h=H, **palette)
        path = OUT / f"banner-{name}.svg"
        path.write_text(svg, encoding="utf-8")
        print(f"wrote {path.relative_to(OUT.parent)} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
