import os
import random
import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import cv2

NUM_IMAGES = 1000
OUTPUT_DIR = "data_work/synthetic_dataset"
FONTS_DIR = "data_work/front/"
LABELS_DIR = os.path.join(OUTPUT_DIR, "labels")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LABELS_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "text_with_numbers"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "text_with_letters"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "bbox_with_numbers"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "bbox_with_letters"), exist_ok=True)

def load_font():
    return ImageFont.truetype(os.path.join(FONTS_DIR, "GOST_Bold.ttf"), 30)

font = load_font()

# Функция для создания текстур фона
def create_metal_texture(width, height, texture_type="matte"):
    base_intensity = 180
    if texture_type == "shiny":
        texture = np.random.normal(base_intensity, 50, (height, width)).astype(np.uint8)
        texture = cv2.GaussianBlur(texture, (7, 7), 0)
    elif texture_type == "scratched":
        texture = np.random.normal(base_intensity - 10, 70, (height, width)).astype(np.uint8)
        for _ in range(3):
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            cv2.line(texture, (x1, y1), (x2, y2), random.randint(100, 200), 1)
    else:
        texture = np.random.normal(base_intensity, 40, (height, width)).astype(np.uint8)
        texture = cv2.GaussianBlur(texture, (9, 9), 0)
    texture = Image.fromarray(texture).convert("RGB")
    enhancer = ImageEnhance.Contrast(texture)
    return enhancer.enhance(1.2)

# Функция для добавления бликов
def apply_glare_effect(image):
    glare_mask = np.zeros((image.size[1], image.size[0]), dtype=np.uint8)
    cv2.circle(glare_mask, (random.randint(100, 400), random.randint(100, 400)), random.randint(60, 120), 255, -1)
    glare_mask = cv2.GaussianBlur(glare_mask, (31, 31), 0)
    glare_overlay = Image.fromarray(glare_mask).convert("L")
    return Image.composite(image, Image.new("RGB", image.size, "white"), glare_overlay)

# Генерация текста с буквами или без
def generate_realistic_text(with_letters=False):
    part1 = "".join(random.choices("0123456789", k=3))
    part2 = "".join(random.choices("0123456789", k=2))
    part3 = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ" if with_letters else "0123456789", k=3))
    part4 = "".join(random.choices("0123456789", k=4))
    additional_part = "".join(random.choices("0123456789", k=4))
    return f"{part1}-{part2}-{part3} {part4}", additional_part

# Функция для добавления выгравированного текста с учетом расположения по кругу и подстрочного текста
def add_engraved_text(image, main_text, position, font, additional_text=None, arc=False):
    text_img = Image.new("RGBA", image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(text_img)
    bbox_coordinates = []

    if arc:
        radius = min(image.size) // 3
        center_x, center_y = position
        angle_step = 360 / len(main_text)  # угол между символами
        angle_offset = -len(main_text) * angle_step // 2  # начальный угол для центрирования

        for i, char in enumerate(main_text):
            char_x = center_x + radius * math.cos(math.radians(angle_offset + i * angle_step))
            char_y = center_y + radius * math.sin(math.radians(angle_offset + i * angle_step))
            draw.text((char_x, char_y), char, font=font, fill=(70, 70, 70, 255))
            bbox_coordinates.append((char_x, char_y))
    else:
        draw.text(position, main_text, font=font, fill=(70, 70, 70, 255))
        bbox_coordinates.append(position)

        if additional_text:
            position_below = (position[0], position[1] + font.getbbox(main_text)[3] + 5)
            draw.text(position_below, additional_text, font=font, fill=(70, 70, 70, 255))
            bbox_coordinates.append(position_below)

    final_image = Image.alpha_composite(image.convert("RGBA"), text_img).convert("RGB")
    return final_image, bbox_coordinates

# Функция для вычисления точного bbox на основе координат текста
def calculate_bbox(bbox_coordinates, font, main_text, additional_text=None):
    min_x = min(coord[0] for coord in bbox_coordinates)
    min_y = min(coord[1] for coord in bbox_coordinates)
    max_x = max(coord[0] + font.getbbox(main_text)[2] for coord in bbox_coordinates)
    max_y = max(coord[1] + font.getbbox(main_text)[3] for coord in bbox_coordinates)
    if additional_text:
        max_y += font.getbbox(additional_text)[3] + 5  # Дополнительное смещение для подстрочного текста
    return [min_x, min_y, max_x, max_y]

# Основная функция генерации
def generate_synthetic_image(index):
    width, height = 512, 512
    texture_type = random.choice(["matte", "shiny", "scratched"])
    texture = create_metal_texture(width, height, texture_type=texture_type)
    image = Image.fromarray(np.array(texture)).convert("RGB")
    if random.random() > 0.5:
        image = apply_glare_effect(image)

    shape_type = "rectangle" if random.random() < 0.7 else "circle"  # Приоритет на прямоугольники
    use_letters = random.random() > 0.5
    main_text, additional_text = generate_realistic_text(with_letters=use_letters)
    arc = shape_type == "circle" and random.random() < 0.5

    if shape_type == "circle":
        draw = ImageDraw.Draw(image)
        center = (width // 2, height // 2)
        radius = min(width, height) // 3
        draw.ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius], fill=(180, 180, 180))
        position = (center[0], center[1])
    elif shape_type == "rectangle":
        draw = ImageDraw.Draw(image)
        margin = 50
        rect_coords = [margin, margin, width - margin, height - margin]
        draw.rectangle(rect_coords, fill=(180, 180, 180))
        position = (rect_coords[0] + 10, (rect_coords[1] + rect_coords[3]) // 2 - 10)
    else:
        position = (width // 4, height // 3)

    # Добавляем текст и получаем изображение и координаты
    if random.random() < 0.6:  # 70% вероятности на текст в одну строку
        additional_text = None

    image, bbox_coordinates = add_engraved_text(image, main_text, position, font, additional_text=additional_text, arc=arc)
    
    # Вычисление bounding box
    bbox_coords = calculate_bbox(bbox_coordinates, font, main_text, additional_text)
    
    # Сохранение изображения и bbox
    output_subdir = "text_with_letters" if use_letters else "text_with_numbers"
    output_path = os.path.join(OUTPUT_DIR, output_subdir, f"synthetic_image_{index}.png")
    image.save(output_path)
    
    bbox_image = image.copy()
    draw_bbox = ImageDraw.Draw(bbox_image)
    draw_bbox.rectangle(bbox_coords, outline="red", width=2)
    bbox_output_path = os.path.join(OUTPUT_DIR, "bbox_with_letters" if use_letters else "bbox_with_numbers", f"synthetic_image_{index}.png")
    bbox_image.save(bbox_output_path)

    # Сохранение разметки в YOLO формате
    label_path = os.path.join(LABELS_DIR, f"synthetic_image_{index}.txt")
    with open(label_path, "w") as f:
        f.write(f"0 {((bbox_coords[0] + bbox_coords[2]) / 2) / width} {((bbox_coords[1] + bbox_coords[3]) / 2) / height} {(bbox_coords[2] - bbox_coords[0]) / width} {(bbox_coords[3] - bbox_coords[1]) / height}\n")

for i in range(NUM_IMAGES):
    generate_synthetic_image(i)

print("Генерация завершена.")