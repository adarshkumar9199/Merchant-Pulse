"""
Pure Python SVG Chart Generator
Zero JavaScript, Zero External Client Dependencies.
Generates responsive, crisp, dark-mode SVG charts directly on the server.
"""

from typing import List
from app.schemas import TrendPoint, SegmentDistribution, MonthlyPerformance


def format_currency_short(val: float) -> str:
    if val >= 10_000_000:
        return f"₹{val / 10_000_000:.1f}Cr"
    if val >= 100_000:
        return f"₹{val / 100_000:.1f}L"
    if val >= 1_000:
        return f"₹{val / 1_000:.0f}K"
    return f"₹{val:.0f}"


def format_number_short(val: int) -> str:
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val / 1_000:.1f}K"
    return str(val)


def render_gmv_trend_svg(trends: List[TrendPoint], width: int = 680, height: int = 240) -> str:
    if not trends:
        return '<svg viewBox="0 0 680 240" class="svg-chart"><text x="340" y="120" fill="#9ca3af" text-anchor="middle">No Trend Data</text></svg>'

    pad_left = 65
    pad_right = 25
    pad_top = 25
    pad_bottom = 35

    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    gmvs = [t.gmv for t in trends]
    max_gmv = max(gmvs) if max(gmvs) > 0 else 1.0
    # Add 10% headroom
    y_max = max_gmv * 1.1

    n = len(trends)
    points = []
    for i, t in enumerate(trends):
        x = pad_left + (i / max(1, n - 1)) * plot_w
        y = pad_top + plot_h - (t.gmv / y_max) * plot_h
        points.append((x, y, t))

    # Build line path and area path
    path_d = f"M {points[0][0]:.1f} {points[0][1]:.1f} "
    for x, y, _ in points[1:]:
        path_d += f"L {x:.1f} {y:.1f} "

    area_d = path_d + f"L {points[-1][0]:.1f} {pad_top + plot_h:.1f} L {points[0][0]:.1f} {pad_top + plot_h:.1f} Z"

    # Gridlines (3 horizontal lines)
    grid_svg = ""
    for step in range(4):
        val = (y_max / 3) * step
        y_pos = pad_top + plot_h - (val / y_max) * plot_h
        grid_svg += f'<line x1="{pad_left}" y1="{y_pos:.1f}" x2="{width - pad_right}" y2="{y_pos:.1f}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4" />'
        grid_svg += f'<text x="{pad_left - 8}" y="{y_pos + 4:.1f}" fill="#6b7280" font-size="10" text-anchor="end" font-family="Inter, sans-serif">{format_currency_short(val)}</text>'

    # Points and X-axis labels
    dots_svg = ""
    for i, (x, y, t) in enumerate(points):
        month_label = t.month.split("-")[-1] if "-" in t.month else t.month
        dots_svg += f'<text x="{x:.1f}" y="{height - 10}" fill="#9ca3af" font-size="10" text-anchor="middle" font-family="Inter, sans-serif">{month_label}</text>'
        dots_svg += f'''
        <g class="chart-dot">
          <circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#6366f1" stroke="#fff" stroke-width="1.5" />
          <title>{t.month}: {format_currency_short(t.gmv)}</title>
        </g>'''

    svg = f'''
    <svg viewBox="0 0 {width} {height}" class="svg-chart" preserveAspectRatio="none" style="width: 100%; height: 100%;">
      <defs>
        <linearGradient id="gmvGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#6366f1" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="#6366f1" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
      {grid_svg}
      <path d="{area_d}" fill="url(#gmvGrad)" />
      <path d="{path_d}" fill="none" stroke="#6366f1" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      {dots_svg}
    </svg>
    '''
    return svg


def render_volume_bar_svg(trends: List[TrendPoint], width: int = 340, height: int = 240) -> str:
    if not trends:
        return '<svg viewBox="0 0 340 240" class="svg-chart"><text x="170" y="120" fill="#9ca3af" text-anchor="middle">No Volume Data</text></svg>'

    pad_left = 50
    pad_right = 15
    pad_top = 25
    pad_bottom = 35

    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    volumes = [t.volume for t in trends]
    max_vol = max(volumes) if max(volumes) > 0 else 1
    y_max = max_vol * 1.15

    n = len(trends)
    bar_width = max(8.0, (plot_w / max(1, n)) * 0.65)
    gap = plot_w / max(1, n)

    # Gridlines
    grid_svg = ""
    for step in range(4):
        val = int((y_max / 3) * step)
        y_pos = pad_top + plot_h - (val / y_max) * plot_h
        grid_svg += f'<line x1="{pad_left}" y1="{y_pos:.1f}" x2="{width - pad_right}" y2="{y_pos:.1f}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4" />'
        grid_svg += f'<text x="{pad_left - 6}" y="{y_pos + 4:.1f}" fill="#6b7280" font-size="10" text-anchor="end" font-family="Inter, sans-serif">{format_number_short(val)}</text>'

    bars_svg = ""
    for i, t in enumerate(trends):
        x = pad_left + i * gap + (gap - bar_width) / 2
        bar_h = (t.volume / y_max) * plot_h
        y = pad_top + plot_h - bar_h
        month_label = t.month.split("-")[-1] if "-" in t.month else t.month

        bars_svg += f'''
        <g class="chart-bar">
          <rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_h:.1f}" rx="3" fill="#3b82f6">
            <title>{t.month}: {t.volume:,} transactions</title>
          </rect>
          <text x="{x + bar_width/2:.1f}" y="{height - 10}" fill="#9ca3af" font-size="9" text-anchor="middle" font-family="Inter, sans-serif">{month_label}</text>
        </g>'''

    svg = f'''
    <svg viewBox="0 0 {width} {height}" class="svg-chart" preserveAspectRatio="none" style="width: 100%; height: 100%;">
      {grid_svg}
      {bars_svg}
    </svg>
    '''
    return svg


def render_segment_donut_svg(segments: List[SegmentDistribution], width: int = 340, height: int = 240) -> str:
    if not segments:
        return '<svg viewBox="0 0 340 240" class="svg-chart"><text x="170" y="120" fill="#9ca3af" text-anchor="middle">No Segments</text></svg>'

    total_count = sum(s.count for s in segments)
    if total_count == 0:
        total_count = 1

    color_map = {
        "High Growth": "#10b981",
        "Healthy": "#3b82f6",
        "Stable": "#8b5cf6",
        "Declining": "#f59e0b",
        "At Risk": "#ef4444"
    }

    # Donut geometry (radius = 55, circumference = 2 * pi * 55 = 345.575)
    cx = 100
    cy = 120
    r = 52
    stroke_w = 22
    circumference = 2 * 3.141592653589793 * r

    accumulated_percent = 0.0
    circles_svg = ""

    for s in segments:
        color = color_map.get(s.segment, "#6b7280")
        fraction = s.count / total_count
        dash_len = fraction * circumference
        offset = - (accumulated_percent * circumference)

        circles_svg += f'''
        <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{stroke_w}"
                stroke-dasharray="{dash_len:.2f} {circumference:.2f}" stroke-dashoffset="{offset:.2f}"
                transform="rotate(-90 {cx} {cy})">
          <title>{s.segment}: {s.count} ({s.percentage}%)</title>
        </circle>'''
        accumulated_percent += fraction

    # Center Text
    center_text = f'''
    <text x="{cx}" y="{cy - 4}" fill="#fff" font-size="18" font-weight="800" text-anchor="middle" font-family="Inter, sans-serif">{total_count}</text>
    <text x="{cx}" y="{cy + 12}" fill="#9ca3af" font-size="9" font-weight="600" text-anchor="middle" font-family="Inter, sans-serif">MERCHANTS</text>
    '''

    # Legend beside donut
    legend_svg = ""
    ly_start = 45
    for i, s in enumerate(segments):
        color = color_map.get(s.segment, "#6b7280")
        ly = ly_start + i * 32
        legend_svg += f'''
        <g transform="translate(195, {ly})">
          <rect x="0" y="0" width="10" height="10" rx="3" fill="{color}"/>
          <text x="16" y="9" fill="#f3f4f6" font-size="11" font-weight="600" font-family="Inter, sans-serif">{s.segment}</text>
          <text x="130" y="9" fill="#9ca3af" font-size="11" text-anchor="end" font-family="Inter, sans-serif">{s.count} ({s.percentage}%)</text>
        </g>'''

    svg = f'''
    <svg viewBox="0 0 {width} {height}" class="svg-chart" style="width: 100%; height: 100%;">
      <g>
        {circles_svg}
        {center_text}
      </g>
      {legend_svg}
    </svg>
    '''
    return svg


def render_merchant_history_svg(history: List[MonthlyPerformance], width: int = 680, height: int = 260) -> str:
    if not history:
        return '<svg viewBox="0 0 680 260" class="svg-chart"><text x="340" y="130" fill="#9ca3af" text-anchor="middle">No History Available</text></svg>'

    pad_left = 65
    pad_right = 25
    pad_top = 25
    pad_bottom = 35

    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom

    gmvs = [h.gmv for h in history]
    max_gmv = max(gmvs) if max(gmvs) > 0 else 1.0
    y_max = max_gmv * 1.15

    n = len(history)
    points = []
    for i, h in enumerate(history):
        x = pad_left + (i / max(1, n - 1)) * plot_w
        y = pad_top + plot_h - (h.gmv / y_max) * plot_h
        points.append((x, y, h))

    path_d = f"M {points[0][0]:.1f} {points[0][1]:.1f} "
    for x, y, _ in points[1:]:
        path_d += f"L {x:.1f} {y:.1f} "

    area_d = path_d + f"L {points[-1][0]:.1f} {pad_top + plot_h:.1f} L {points[0][0]:.1f} {pad_top + plot_h:.1f} Z"

    grid_svg = ""
    for step in range(4):
        val = (y_max / 3) * step
        y_pos = pad_top + plot_h - (val / y_max) * plot_h
        grid_svg += f'<line x1="{pad_left}" y1="{y_pos:.1f}" x2="{width - pad_right}" y2="{y_pos:.1f}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4" />'
        grid_svg += f'<text x="{pad_left - 8}" y="{y_pos + 4:.1f}" fill="#6b7280" font-size="10" text-anchor="end" font-family="Inter, sans-serif">{format_currency_short(val)}</text>'

    dots_svg = ""
    for i, (x, y, h) in enumerate(points):
        month_label = h.month.split("-")[-1] if "-" in h.month else h.month
        dots_svg += f'<text x="{x:.1f}" y="{height - 10}" fill="#9ca3af" font-size="10" text-anchor="middle" font-family="Inter, sans-serif">{month_label}</text>'
        dots_svg += f'''
        <g class="chart-dot">
          <circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#3b82f6" stroke="#fff" stroke-width="1.5" />
          <title>{h.month}: {format_currency_short(h.gmv)} ({h.transaction_count} txns)</title>
        </g>'''

    svg = f'''
    <svg viewBox="0 0 {width} {height}" class="svg-chart" preserveAspectRatio="none" style="width: 100%; height: 100%;">
      <defs>
        <linearGradient id="detailGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
      {grid_svg}
      <path d="{area_d}" fill="url(#detailGrad)" />
      <path d="{path_d}" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      {dots_svg}
    </svg>
    '''
    return svg
