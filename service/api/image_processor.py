from PIL import Image
import io
import numpy as np
from core.matcher import ImageMatcher
from integration_1c import OneCIntegration


class ImageProcessor:
    """Основной класс для обработки изображений"""
    
    def __init__(self, onec_url: str = "http://localhost:8080/api/v1", onec_token: str = ""):
        self.matcher = ImageMatcher()
        self.onec = OneCIntegration(onec_url, onec_token)

    async def process(self, image_stream: io.BytesIO) -> dict:
        """Обработка входящего изображения"""
        try:
            image = np.array(Image.open(image_stream))
            result = self.matcher.get_image_article_text(image)
            
            text_ocr_distance = result['text_ocr_distance']
            number = result['text'].split(' ')[1] if len(result['text'].split(' ')) > 1 else None
            
            # Получаем информацию о товаре из 1С
            article_info = {}
            if result['article']:
                try:
                    article_info = self.onec.get_article_info(result['article'])
                except Exception as e:
                    print(f"Failed to get 1C data: {e}")
            
            json_data = {
                "article": result['article'],
                "number": number if text_ocr_distance > 0.99 else None,
                "status": "success",
                "product_info": article_info
            }
            print(json_data)
            return json_data
            
        except Exception as e:
            raise Exception(f"Error processing image: {str(e)}")