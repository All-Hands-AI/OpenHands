#!/usr/bin/env python3
"""
Create an ASCII art splash screen image for OpenHands CLI PyInstaller executable.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_splash_screen():
    """Create an ASCII art splash screen image for the OpenHands CLI."""
    
    # Image dimensions
    width, height = 800, 500
    
    # Colors (dark theme)
    bg_color = (20, 20, 20)  # Very dark gray
    text_color = (0, 255, 0)  # Green (classic terminal color)
    accent_color = (0, 200, 255)  # Cyan
    
    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a monospace font for ASCII art
    try:
        ascii_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 16)
        loading_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
    except OSError:
        # Fallback to default font
        ascii_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
        loading_font = ImageFont.load_default()
    
    # ASCII art for OpenHands logo/title
    ascii_art = [
        "   ___                   _   _                 _      ",
        "  / _ \\ _ __   ___ _ __ | | | | __ _ _ __   __| |___  ",
        " | | | | '_ \\ / _ \\ '_ \\| |_| |/ _` | '_ \\ / _` / __| ",
        " | |_| | |_) |  __/ | | |  _  | (_| | | | | (_| \\__ \\ ",
        "  \\___/| .__/ \\___|_| |_|_| |_|\\__,_|_| |_|\\__,_|___/ ",
        "       |_|                                           ",
        "",
        "                      _____ _     _____ ",
        "                     /  ___| |   |_   _|",
        "                     \\ `--.| |     | |  ",
        "                      `--. \\ |     | |  ",
        "                     /\\__/ / |_____| |_ ",
        "                     \\____/\\_____/\\___/ ",
    ]
    
    # Calculate starting position for ASCII art
    line_height = 20
    total_height = len(ascii_art) * line_height
    start_y = (height - total_height) // 2 - 50
    
    # Draw ASCII art
    for i, line in enumerate(ascii_art):
        # Center each line
        line_bbox = draw.textbbox((0, 0), line, font=ascii_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (width - line_width) // 2
        line_y = start_y + i * line_height
        
        # Use accent color for the main logo, text color for CLI
        color = accent_color if i < 6 else text_color
        draw.text((line_x, line_y), line, fill=color, font=ascii_font)
    
    # Draw subtitle
    subtitle_text = "AI-Powered Software Development Assistant"
    subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=loading_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = start_y + len(ascii_art) * line_height + 30
    draw.text((subtitle_x, subtitle_y), subtitle_text, fill=text_color, font=loading_font)
    
    # Draw loading indicator with ASCII style
    loading_text = ">>> Initializing..."
    loading_bbox = draw.textbbox((0, 0), loading_text, font=loading_font)
    loading_width = loading_bbox[2] - loading_bbox[0]
    loading_x = (width - loading_width) // 2
    loading_y = height - 60
    draw.text((loading_x, loading_y), loading_text, fill=accent_color, font=loading_font)
    
    # Draw ASCII progress bar
    progress_bar = "[" + "=" * 20 + ">" + " " * 10 + "]"
    progress_bbox = draw.textbbox((0, 0), progress_bar, font=ascii_font)
    progress_width = progress_bbox[2] - progress_bbox[0]
    progress_x = (width - progress_width) // 2
    progress_y = loading_y + 25
    draw.text((progress_x, progress_y), progress_bar, fill=text_color, font=ascii_font)
    
    # Draw terminal-style border
    border_chars = "+" + "-" * ((width // 8) - 2) + "+"
    draw.text((10, 10), border_chars, fill=accent_color, font=ascii_font)
    draw.text((10, height - 30), border_chars, fill=accent_color, font=ascii_font)
    
    # Save the image
    img.save('splash.png', 'PNG')
    print("✅ ASCII art splash screen created: splash.png")
    
    return 'splash.png'

if __name__ == "__main__":
    create_splash_screen()