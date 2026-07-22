#!/usr/bin/env python3
"""
Fillo Store QR Code & Onboarding Flyer Generator
Generates a premium, clean, white-background flyer for store counters.
"""
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

# --- Brand Colors ---
FILLO_DARK    = (15, 23, 42)      # #0F172A
FILLO_BLUE    = (56, 132, 255)    # #3884FF
FILLO_PURPLE  = (99, 102, 241)    # #6366F1
FILLO_INDIGO  = (79, 70, 229)     # #4F46E5
WHITE         = (255, 255, 255)
OFF_WHITE     = (248, 250, 252)   # #F8FAFC
LIGHT_GRAY    = (226, 232, 240)   # #E2E8F0
MID_GRAY      = (148, 163, 184)   # #94A3B8
DARK_GRAY     = (51, 65, 85)      # #334155
ACCENT_GREEN  = (16, 185, 129)    # #10B981

# --- Font Paths ---
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
HELV   = "/System/Library/Fonts/HelveticaNeue.ttc"


def load_font(path, index, size):
    try:
        return ImageFont.truetype(path, index=index, size=size)
    except Exception:
        return ImageFont.load_default()


def create_store_qr(target_url, output_qr_path):
    """Generate a high-resolution QR code with error correction level H."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=FILLO_DARK, back_color=WHITE).convert("RGBA")
    img.save(output_qr_path)
    print(f"QR Code saved: {output_qr_path}")
    return img


def draw_centered(draw, text, font, y, canvas_w, fill=FILLO_DARK):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((canvas_w - tw) / 2, y), text, font=font, fill=fill)


def draw_gradient_bar(draw, x0, y0, x1, y1):
    """Horizontal gradient from FILLO_BLUE to FILLO_PURPLE."""
    w = x1 - x0
    for i in range(w):
        ratio = i / max(w - 1, 1)
        r = int(FILLO_BLUE[0] + (FILLO_PURPLE[0] - FILLO_BLUE[0]) * ratio)
        g = int(FILLO_BLUE[1] + (FILLO_PURPLE[1] - FILLO_BLUE[1]) * ratio)
        b = int(FILLO_BLUE[2] + (FILLO_PURPLE[2] - FILLO_BLUE[2]) * ratio)
        draw.line([(x0 + i, y0), (x0 + i, y1)], fill=(r, g, b))


def draw_circle_number(draw, cx, cy, radius, number, font_num, bg_color=FILLO_INDIGO):
    """Draw a filled circle with a number inside."""
    draw.ellipse(
        [(cx - radius, cy - radius), (cx + radius, cy + radius)],
        fill=bg_color,
    )
    text = str(number)
    bbox = draw.textbbox((0, 0), text, font=font_num)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw / 2, cy - th / 2 - 2), text, font=font_num, fill=WHITE)


def generate_store_flyer(store_name, telegram_link, output_flyer_path):
    """
    Build a clean, white, premium A5-proportioned flyer.
    Layout (top to bottom):
      - Gradient accent bar
      - FILLO logo text
      - Tagline
      - Separator
      - QR code on white card with subtle shadow
      - "Scan to Get Started" caption
      - 3 numbered steps with circular badges
      - Free trial badge
      - Footer
    """
    W, H = 1200, 1700
    canvas = Image.new("RGBA", (W, H), WHITE)
    draw = ImageDraw.Draw(canvas)

    # Fonts
    f_logo      = load_font(AVENIR, 8, 56)   # Heavy
    f_tagline   = load_font(AVENIR, 5, 28)    # Medium
    f_heading   = load_font(AVENIR, 2, 34)    # Demi Bold
    f_step_title = load_font(AVENIR, 2, 28)   # Demi Bold
    f_step_body = load_font(AVENIR, 7, 24)    # Regular
    f_badge     = load_font(AVENIR, 0, 26)    # Bold
    f_num       = load_font(AVENIR, 0, 24)    # Bold (for circle numbers)
    f_scan      = load_font(AVENIR, 5, 24)    # Medium
    f_footer    = load_font(HELV, 7, 20)      # Light
    f_store     = load_font(AVENIR, 0, 30)    # Bold

    y = 0

    # --- Top gradient accent bar ---
    draw_gradient_bar(draw, 0, 0, W, 8)
    y = 8

    # --- Logo area ---
    y += 60
    draw_centered(draw, "FILLO", f_logo, y, W, fill=FILLO_INDIGO)
    y += 75

    # --- Tagline ---
    draw_centered(draw, "Turn Empty Slots Into Revenue", f_tagline, y, W, fill=MID_GRAY)
    y += 50

    # --- Store name ---
    draw_centered(draw, store_name, f_store, y, W, fill=FILLO_DARK)
    y += 55

    # --- Thin separator line ---
    sep_margin = 200
    draw.line([(sep_margin, y), (W - sep_margin, y)], fill=LIGHT_GRAY, width=2)
    y += 40

    # --- QR Code section ---
    qr_temp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp_qr.png")
    qr_img = create_store_qr(telegram_link, qr_temp)

    qr_size = 420
    qr_card_padding = 30
    qr_card_size = qr_size + qr_card_padding * 2
    qr_card_x = (W - qr_card_size) // 2
    qr_card_y = y

    # Shadow
    shadow_offset = 6
    draw.rounded_rectangle(
        [(qr_card_x + shadow_offset, qr_card_y + shadow_offset),
         (qr_card_x + qr_card_size + shadow_offset, qr_card_y + qr_card_size + shadow_offset)],
        radius=16, fill=(0, 0, 0, 25)
    )
    # White card
    draw.rounded_rectangle(
        [(qr_card_x, qr_card_y),
         (qr_card_x + qr_card_size, qr_card_y + qr_card_size)],
        radius=16, fill=WHITE, outline=LIGHT_GRAY, width=2
    )

    qr_resized = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    canvas.paste(qr_resized, (qr_card_x + qr_card_padding, qr_card_y + qr_card_padding), qr_resized)

    y = qr_card_y + qr_card_size + 25

    # --- Scan caption ---
    draw_centered(draw, "Scan to get started on Telegram", f_scan, y, W, fill=FILLO_BLUE)
    y += 55

    # --- Separator ---
    draw.line([(sep_margin, y), (W - sep_margin, y)], fill=LIGHT_GRAY, width=2)
    y += 45

    # --- Section heading ---
    draw_centered(draw, "HOW IT WORKS", f_heading, y, W, fill=FILLO_DARK)
    y += 60

    # --- 3 Steps ---
    steps = [
        ("Scan & Connect", "Open Telegram and tap Start to link your store."),
        ("Share Your Details", "Send your store name, location, and a photo."),
        ("Start Filling Slots", "Your free trial activates instantly. Fill empty hours."),
    ]

    left_margin = 180
    circle_r = 24
    for i, (title, desc) in enumerate(steps):
        cx = left_margin
        cy = y + circle_r + 2
        draw_circle_number(draw, cx, cy, circle_r, i + 1, f_num)
        draw.text((cx + circle_r + 22, y + 2), title, font=f_step_title, fill=FILLO_DARK)
        draw.text((cx + circle_r + 22, y + 38), desc, font=f_step_body, fill=MID_GRAY)
        y += 90

    y += 15

    # --- Free trial badge ---
    badge_text = "1 MONTH FREE TRIAL  •  NO CREDIT CARD  •  CANCEL ANYTIME"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=f_badge)
    badge_tw = badge_bbox[2] - badge_bbox[0]
    badge_h = 56
    badge_w = badge_tw + 60
    badge_x = (W - badge_w) // 2
    badge_y = y

    draw.rounded_rectangle(
        [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
        radius=badge_h // 2, fill=ACCENT_GREEN
    )
    draw.text(
        (badge_x + 30, badge_y + 13), badge_text,
        font=f_badge, fill=WHITE
    )
    y = badge_y + badge_h + 40

    # --- Footer ---
    draw_centered(draw, "fillo.app  |  Telegram: @Mounirmailsbot", f_footer, y, W, fill=MID_GRAY)
    y += 35
    draw_centered(draw, "Fill quiet hours. Recover lost revenue. Grow your business.", f_footer, y, W, fill=MID_GRAY)

    # --- Bottom gradient accent bar ---
    draw_gradient_bar(draw, 0, H - 8, W, H)

    # Save
    canvas.save(output_flyer_path)
    print(f"Store Flyer saved: {output_flyer_path}")

    if os.path.exists(qr_temp):
        os.remove(qr_temp)


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_flyer = os.path.join(base_dir, "fillo_store_flyer.png")
    output_qr = os.path.join(base_dir, "fillo_store_qr.png")

    telegram_link = "https://t.me/Mounirmailsbot?start=activate_store"

    create_store_qr(telegram_link, output_qr)
    generate_store_flyer("JK Barber FICS31", telegram_link, output_flyer)
