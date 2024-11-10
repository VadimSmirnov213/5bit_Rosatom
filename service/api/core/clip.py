from transformers import CLIPProcessor, CLIPModel
import numpy as np
import cv2
import torch
from PIL import Image


class CLIPEmbedder:
    """Класс для работы с CLIP embeddings"""
    
    def __init__(self):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = self.model.to(self.device)
        self.model.eval()

    def get_embeddings(self, image=None, text=None):
        """Получение эмбеддингов для изображения и/или текста"""
        result = {}
        
        with torch.no_grad():
            if image is not None:
                if isinstance(image, np.ndarray):
                    image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                if isinstance(image, str):
                    image = Image.open(image)
                    
                inputs = self.processor(images=image, return_tensors="pt").to(self.device)
                image_features = self.model.get_image_features(**inputs)
                result['image_embedding'] = image_features.cpu().numpy()
            
            if text is not None and isinstance(text, str):
                inputs = self.processor(text=text, return_tensors="pt", padding=True).to(self.device)
                text_features = self.model.get_text_features(**inputs)
                result['text_embedding'] = text_features.cpu().numpy()
        
        return result

    @staticmethod
    def calculate_cosine_similarity(embedding1, embedding2):
        """Вычисление косинусного сходства между эмбеддингами"""
        embedding1 = embedding1.flatten()
        embedding2 = embedding2.flatten()
        
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        return dot_product / (norm1 * norm2)