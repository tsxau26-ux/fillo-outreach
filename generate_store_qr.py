#!/usr/bin/env python3
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont

def create_store_qr(target_url, output_qr_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=15,
        border=3,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGBA")
    img.save(output_qr_path)
    print(f"Generated QR Code at: {output_qr_path}")
    return img

def draw_text_centered(draw, text, font, y_pos, width, fill="#FFFFFF"):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text(((width - text_w) / 2, y_pos), text, font=font, fill=fill)

def generate_store_flyer(store_name, telegram_link, output_flyer_path):
    width, height = 1200, 1600
    canvas = Image.new("RGBA", (width, height), (15, 23, 42, 255)) # Dark navy background
    draw = ImageDraw.Draw(canvas)

    # Decorative header box
    draw.rectangle([(80, 80), (1120, 200)], fill=(30, 41, 59, 255), outline=(99, 102, 241, 255), width=3)
    
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", index=0, size=52)
        font_subtitle = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", index=0, size=36)
        font_body = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", index=0, size=32)
        font_bold = ImageFont.truetype("/System/Library/Fonts/HelveticaNeue.ttc", index=1, size=40)
    except Exception:
        font_title = font_subtitle = font_body = font_bold = ImageFont.load_default()

    # Draw Header Text
    draw_text_centered(draw, "⚡ FILLO PARTNER ONBOARDING", font_title, 115, width, fill="#818CF8")

    # Main Headline
    draw_text_centered(draw, f"Welcome, {store_name}!", font_bold, 240, width, fill="#FFFFFF")
    draw_text_centered(draw, "Fill Quiet Hours & Claim Last-Minute Bookings", font_subtitle, 300, width, fill="#94A3B8")

    # Generate QR Code
    qr_temp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_qr.png")
    qr_img = create_store_qr(telegram_link, qr_temp_path)
    
    # White background container for QR code
    qr_box_size = 500
    qr_x = (width - qr_box_size) // 2
    qr_y = 380
    
    draw.rounded_rectangle([(qr_x - 30, qr_y - 30), (qr_x + qr_box_size + 30, qr_y + qr_box_size + 30)], radius=20, fill=(255, 255, 255, 255))
    qr_resized = qr_img.resize((qr_box_size, qr_box_size), Image.Resampling.LANCZOS)
    canvas.paste(qr_resized, (qr_x, qr_y), qr_resized)

    # Instructions box
    instructions_y = 970
    draw.rounded_rectangle([(100, instructions_y), (1100, 1480)], radius=15, fill=(30, 41, 59, 255), outline=(51, 65, 85, 255), width=2)
    
    draw_text_centered(draw, "📱 3 EASY STEPS TO ACTIVATE YOUR STORE:", font_bold, instructions_y + 40, width, fill="#38BDF8")

    steps = [
        "1. Scan the QR code above to open Fillo on Telegram.",
        "2. Send us a quick photo of your store counter + business details.",
        "3. Your 1-Month Free Trial activates instantly — start filling slots!"
    ]

    step_y = instructions_y + 120
    for step in steps:
        draw.text((150, step_y), step, font=font_body, fill="#E2E8F0")
        step_y += 70

    # Footer
    draw_text_centered(draw, "Need help? Contact Fillo Support on Telegram: @Mounirmailsbot", font_body, 1510, width, fill="#64748B")

    canvas.save(output_flyer_path)
    print(f"Generated Store Flyer at: {output_flyer_path}")
    
    if os.path.exists(qr_temp_path):
        os.remove(qr_temp_path)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_flyer = os.path.join(base_dir, "fillo_store_flyer.png")
    output_qr = os.path.join(base_dir, "fillo_store_qr.png")
    
    telegram_link = "https://t.me/Mounirmailsbot?start=activate_store"
    
    create_store_qr(telegram_link, output_qr)
    generate_store_flyer("JK Barber & Partner Stores", telegram_link, output_flyer)
