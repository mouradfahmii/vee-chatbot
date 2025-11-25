#!/usr/bin/env python3
"""Generate a test meal image for testing image analysis."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Create a simple meal image
width, height = 800, 600
img = Image.new("RGB", (width, height), color=(245, 245, 240))
draw = ImageDraw.Draw(img)

# Draw a plate
plate_center = (width // 2, height // 2)
plate_radius = 200
draw.ellipse(
    [
        plate_center[0] - plate_radius,
        plate_center[1] - plate_radius,
        plate_center[0] + plate_radius,
        plate_center[1] + plate_radius,
    ],
    fill=(255, 255, 255),
    outline=(200, 200, 200),
    width=3,
)

# Draw food items (simplified representation)
# Chicken (brown rectangle)
chicken_x = plate_center[0] - 80
chicken_y = plate_center[1] - 40
draw.rectangle(
    [chicken_x, chicken_y, chicken_x + 80, chicken_y + 60],
    fill=(139, 90, 43),
    outline=(100, 60, 30),
)

# Rice (white blob)
rice_x = plate_center[0] - 100
rice_y = plate_center[1] + 20
for i in range(5):
    for j in range(3):
        draw.ellipse(
            [
                rice_x + i * 20 - 5,
                rice_y + j * 15 - 5,
                rice_x + i * 20 + 5,
                rice_y + j * 15 + 5,
            ],
            fill=(255, 248, 220),
        )

# Vegetables (green circles)
veg_x = plate_center[0] + 40
veg_y = plate_center[1] - 20
for i in range(3):
    draw.ellipse(
        [
            veg_x + i * 30 - 15,
            veg_y - 15,
            veg_x + i * 30 + 15,
            veg_y + 15,
        ],
        fill=(34, 139, 34),
    )

# Add text label
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
except:
    font = ImageFont.load_default()

text = "Test Meal: Chicken, Rice & Vegetables"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_x = (width - text_width) // 2
draw.text(
    (text_x, 50),
    text,
    fill=(50, 50, 50),
    font=font,
)

# Save image
output_path = Path(__file__).parent.parent / "test_images" / "test_meal.jpg"
output_path.parent.mkdir(exist_ok=True)
img.save(output_path, "JPEG", quality=95)

print(f"Test meal image generated: {output_path}")
print(f"Image size: {width}x{height}")

