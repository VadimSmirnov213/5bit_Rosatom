import requests


class OneCIntegration:
    """Эмуляция класса для интеграции с 1С"""
    
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.headers = {'Authorization': f'Bearer {auth_token}'}
        
    def get_article_info(self, article: str) -> dict:
        """Получение информации о товаре по артикулу из 1С"""
        try:
            response = requests.get(
                f"{self.base_url}/products/{article}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Error getting data from 1C: {str(e)}")