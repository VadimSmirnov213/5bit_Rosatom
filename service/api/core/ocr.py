from paddleocr import PaddleOCR
import numpy as np
import cv2

# Настройка логирования
import logging
logging.getLogger("ppocr").setLevel(logging.ERROR)

class OCRProcessor:
    """Класс для обработки OCR с помощью PaddleOCR"""
    
    def __init__(self):
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang='en', 
            ocr_version='PP-OCRv4',
            use_space_char=True,
            use_gpu=True,
            enable_mkldnn=True,
            use_tensorrt=True,
            enable_fp16=True
        )

    def preprocess_for_rotation_invariance(self, image):
        """Предобработка изображения для инвариантности к повороту"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        coords = np.column_stack(np.where(binary > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated

    def multi_angle_ocr(self, image, angles=[0, 45, 90, 135, 180, 225, 270, 315]):
        """Сканирование текста под разными углами"""
        best_text = ""
        max_confidence = 0
        best_rotated = None
        best_box = None

        if image is None:
            return best_text, best_rotated, best_box

        # Масштабирование изображения
        height, width = image.shape[:2]
        max_dim = max(height, width)
        if max_dim > 640:
            scale = 640.0 / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))
        
        height, width = image.shape[:2]
        center = (width // 2, height // 2)

        for angle in angles:
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, rotation_matrix, (int(width), int(height)))
            result = self.ocr.ocr(rotated)
            
            if result[0]:
                confidence = sum(line[1][1] for line in result[0])
                if confidence > max_confidence:
                    max_confidence = confidence
                    best_text = " ".join([line[1][0] for line in result[0]])
                    best_rotated = rotated
                    
                    # Вычисление общего ограничивающего прямоугольника
                    boxes = np.array([line[0] for line in result[0]])
                    min_x = np.min(boxes[:, :, 0])
                    min_y = np.min(boxes[:, :, 1])
                    max_x = np.max(boxes[:, :, 0])
                    max_y = np.max(boxes[:, :, 1])
                    
                    width_box = max_x - min_x
                    height_box = max_y - min_y
                    center_x = min_x + width_box/2
                    center_y = min_y + height_box/2
                    
                    width_box *= 1.2
                    height_box *= 1.2
                    
                    rel_center_x = center_x / width
                    rel_center_y = center_y / height
                    rel_width = width_box / width
                    rel_height = height_box / height
                    
                    best_box = [rel_center_x, rel_center_y, rel_width, rel_height]
        
        return best_text, best_rotated, best_box