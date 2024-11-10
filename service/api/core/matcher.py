import pandas as pd
from .clip import CLIPEmbedder
from .ocr import OCRProcessor


class ImageMatcher:
    """Класс для сопоставления изображений со статьями"""
    
    def __init__(self):
        self.ocr_processor = OCRProcessor()
        self.clip_embedder = CLIPEmbedder()
        self.grouped = pd.read_pickle('grouped.pkl')

    def get_image_article_text(self, image):
        """Получение наиболее подходящей статьи для изображения"""
        best_text, rotated_image, box = self.ocr_processor.multi_angle_ocr(image)

        if rotated_image is not None:
            image = rotated_image
            
        embeddings = self.clip_embedder.get_embeddings(image=image, text=best_text[:77])
        image_embedding = embeddings['image_embedding']
        text_embedding = embeddings['text_embedding']

        # Вычисление сходства
        image_distances = self.grouped['embeddings_image'].apply(
            lambda x: self.clip_embedder.calculate_cosine_similarity(image_embedding, x)
        )
        text_ocr_distances = self.grouped['ocr_text_embeddings'].apply(
            lambda x: self.clip_embedder.calculate_cosine_similarity(text_embedding, x)
        )
        text_article_distances = self.grouped['embeddings_text'].apply(
            lambda x: self.clip_embedder.calculate_cosine_similarity(text_embedding, x)
        )

        # Формирование результатов
        groups = pd.DataFrame(self.grouped.index, columns=['article'])
        groups['image_distance'] = image_distances.values
        groups['text_ocr_distance'] = text_ocr_distances.values
        groups['text_article_distance'] = text_article_distances.values
        groups['score'] = (groups['image_distance']*0.5 + 
                         groups['text_ocr_distance']*0.2 + 
                         groups['text_article_distance']*0.3)
        groups.sort_values(by='score', ascending=False, inplace=True)

        return {
            'article': groups.iloc[0].article,
            'text': best_text,
            'image_distance': groups.iloc[0].image_distance,
            'text_ocr_distance': groups.iloc[0].text_ocr_distance,
            'text_article_distance': groups.iloc[0].text_article_distance,
            'score': groups.iloc[0].score,
            'bbox': box if box is not None else [0.5,0.5,0.5,0.5]
        }