from fastapi import APIRouter, UploadFile, File, HTTPException
from image_processor import ImageProcessor
from typing import List
import io

router = APIRouter()
image_processor = ImageProcessor()

@router.post("/process_image")
async def process_image(file: UploadFile = File(...)):
    """
    Роутер для получения изображения и возвращения результата
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, detail="File must be an image")
    
    try:
        # Read image content
        contents = await file.read()
        image_stream = io.BytesIO(contents)
        
        # Process image
        processed_image = await image_processor.process(image_stream)
        
        return processed_image
    except Exception as e:
        raise HTTPException(500, detail=str(e))