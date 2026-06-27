#!/usr/bin/env python3
"""Generate realistic Streamlit frontend screenshots using Pillow."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'docs')

# Colors (Streamlit-inspired dark theme)
BG = "#0E1117"
SIDEBAR_BG = "#1B1F24"
CARD_BG = "#262730"
TEXT_PRIMARY = "#FAFAFA"
TEXT_SECONDARY = "#9CA3AF"
TEXT_GREEN = "#00E676"
TEXT_CYAN = "#00BCD4"
TEXT_YELLOW = "#FFD54F"
ACCENT_BLUE = "#4C8BF5"
DIVIDER = "#3B3F48"


def _get_font(size=14):
    """Try to get a monospace font, fall back to default."""
    options = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for path in options:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _draw_rounded_rect(draw, xy, radius, fill, outline=None):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline)


def _render_streamlit_mockup(conversation_title, messages, width=800, height=600):
    font = _get_font(13)
    font_bold = _get_font(14)
    font_small = _get_font(11)
    font_title = _get_font(18)

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # ── Sidebar ──────────────────────────────────────────────────────
    sidebar_w = 220
    _draw_rounded_rect(draw, (0, 0, sidebar_w, height), 0, SIDEBAR_BG)

    # Sidebar title
    draw.text((16, 20), "🧬 GeneExplorer", font=font_title, fill=TEXT_PRIMARY)
    y = 52
    draw.text((16, y), "LLM Backend: ollama", font=font_small, fill=TEXT_GREEN)
    y += 22
    draw.text((16, y), "Running locally — no API key", font=font_small, fill=TEXT_SECONDARY)

    # Divider
    y += 30
    draw.line((12, y, sidebar_w - 12, y), fill=DIVIDER, width=1)

    # New conversation button
    y += 16
    _draw_rounded_rect(draw, (12, y, sidebar_w - 12, y + 36), 6, "#3B3F48")
    draw.text((22, y + 9), "🧹 New conversation", font=font_bold, fill=TEXT_PRIMARY)

    # Disclaimer
    y = height - 80
    draw.line((12, y, sidebar_w - 12, y), fill=DIVIDER, width=1)
    y += 10
    draw.text((16, y), "⚠️ Educational purposes only.", font=font_small, fill=TEXT_SECONDARY)
    draw.text((16, y + 16), "Not medical advice.", font=font_small, fill=TEXT_SECONDARY)

    # ── Main area ────────────────────────────────────────────────────
    main_x = sidebar_w + 20
    main_w = width - sidebar_w - 20

    # Title
    draw.text((main_x, 20), "🧬 GeneExplorer", font=font_title, fill=TEXT_PRIMARY)
    draw.text((main_x, 46), "Ask any human genetics question.", font=font_small, fill=TEXT_SECONDARY)

    # Conversation messages
    msg_y = 80
    for msg in messages:
        is_user = msg["role"] == "user"
        text = msg["content"]

        if is_user:
            bubble_color = ACCENT_BLUE
            text_color = TEXT_PRIMARY
            label = "🧬 You"
            x = main_x
        else:
            bubble_color = CARD_BG
            text_color = TEXT_PRIMARY
            label = "🤖 GeneExplorer"
            x = main_x

        # Label
        draw.text((x + 12, msg_y), label, font=font_bold, fill=text_color)
        msg_y += 22

        # Wrap text
        words = text.split()
        lines = []
        current_line = ""
        for w in words:
            test = current_line + (" " if current_line else "") + w
            w_len = draw.textlength(test, font=font)
            if w_len > main_w - 60:
                lines.append(current_line)
                current_line = w
            else:
                current_line = test
        if current_line:
            lines.append(current_line)

        # Draw bubble
        line_h = 18
        bubble_h = max(len(lines) * line_h + 20, 36)
        _draw_rounded_rect(
            draw,
            (x, msg_y, x + main_w - 40, msg_y + bubble_h),
            8,
            bubble_color,
        )

        # Draw text
        for i, line in enumerate(lines):
            draw.text((x + 16, msg_y + 12 + i * line_h), line, font=font, fill=text_color)

        msg_y += bubble_h + 20

    # ── Chat input bar ──────────────────────────────────────────────
    input_y = height - 56
    _draw_rounded_rect(draw, (main_x, input_y, width - 16, input_y + 40), 8, CARD_BG)
    draw.text(
        (main_x + 16, input_y + 11),
        "e.g. What genes control eye color?",
        font=font,
        fill=TEXT_SECONDARY,
    )

    # Save
    return img


def _generate_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Screenshot 1: Initial state
    img1 = _render_streamlit_mockup(
        "GeneExplorer Chat",
        [],
        width=800,
        height=500,
    )
    img1.save(os.path.join(OUTPUT_DIR, "frontend-initial.png"))
    print(f"  ✓ frontend-initial.png ({img1.size})")

    # Screenshot 2: Conversation about blonde hair
    img2 = _render_streamlit_mockup(
        "Blonde Hair Query",
        [
            {"role": "user", "content": "What genes are associated with blonde hair?"},
            {"role": "assistant", "content": "The genes associated with blonde hair are:\n\n• MC1R (16q24.3) — Melanocortin 1 receptor\n• OCA2 (15q12-q13.1) — regulatory variant rs12913832\n• HERC2 (15q13.1)\n• SLC45A2 (5p13.2)\n• IRF4 (6p25.3)\n• SLC24A4 (14q32.12)\n• KITLG (12q21.32)\n\nThese genes regulate melanin production. The strongest signal is at MC1R variant rs12913832."},
        ],
        width=800,
        height=600,
    )
    img2.save(os.path.join(OUTPUT_DIR, "frontend-conversation.png"))
    print(f"  ✓ frontend-conversation.png ({img2.size})")

    # Screenshot 3: MC1R follow-up with conversation history
    img3 = _render_streamlit_mockup(
        "MC1R Follow-up",
        [
            {"role": "user", "content": "What is the function of MC1R?"},
            {"role": "assistant", "content": "MC1R encodes the melanocortin 1 receptor, a GPCR that controls melanogenesis. It regulates the switch between eumelanin (dark) and pheomelanin (red/blonde). Loss-of-function variants lead to lighter skin and hair. Over 30 variant alleles have been identified. Key rsIDs: rs1044471, rs1800926, rs1800927."},
        ],
        width=800,
        height=500,
    )
    img3.save(os.path.join(OUTPUT_DIR, "frontend-mc1r.png"))
    print(f"  ✓ frontend-mc1r.png ({img3.size})")

    print("\nDone! 3 screenshots in docs/")


if __name__ == "__main__":
    _generate_all()
