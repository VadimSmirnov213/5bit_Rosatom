import os
import cv2
import pandas as pd
from PIL import Image, ImageStat
import numpy as np

# Пути к папкам
train_path = "train Росатом/train"  # Укажите путь к папке train
imgs_path = os.path.join(train_path, "imgs")
labels_path = os.path.join(train_path, "labels")
labels_with_text_path = os.path.join(train_path, "labels_with_text")
grounded_true_path = os.path.join(train_path, "/Users/daniil/Хакатоны/Межнар/train Росатом/grounded true train.csv")
details_plan_path = "ДеталиПоПлануДляРазрешенныхЗаказов.xlsx"  # Путь к новому файлу

# Функция для анализа изображений
def analyze_images(imgs_path):
    image_data = []
    for img_name in os.listdir(imgs_path):
        img_path = os.path.join(imgs_path, img_name)
        with Image.open(img_path) as img:
            width, height = img.size
            aspect_ratio = width / height
            sharpness = cv2.Laplacian(cv2.imread(img_path), cv2.CV_64F).var()
            brightness = ImageStat.Stat(img).mean[0]
            contrast = ImageStat.Stat(img).stddev[0]
            
            # Анализ бликов
            glare = False
            image_np = np.array(img.convert('L'))
            _, thresholded = cv2.threshold(image_np, 240, 255, cv2.THRESH_BINARY)
            if np.sum(thresholded) > 0.01 * image_np.size:
                glare = True
            
            image_data.append({
                "filename": img_name,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "sharpness": sharpness,
                "brightness": brightness,
                "contrast": contrast,
                "glare": glare
            })

    image_df = pd.DataFrame(image_data)
    image_df.to_csv("data_work/itog/image_summary.csv", index=False)
    return image_df

# Функция для анализа меток (bounding boxes)
def analyze_labels(labels_path):
    label_data = []
    for label_file in os.listdir(labels_path):
        label_path = os.path.join(labels_path, label_file)
        with open(label_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split()
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
                aspect_ratio = width / height
                area = width * height
                
                label_data.append({
                    "filename": label_file,
                    "class_id": class_id,
                    "bbox_width": width,
                    "bbox_height": height,
                    "bbox_area": area,
                    "aspect_ratio": aspect_ratio
                })

    label_df = pd.DataFrame(label_data)
    if not label_df.empty:
        class_distribution = label_df['class_id'].value_counts().reset_index()
        class_distribution.columns = ['class_id', 'count']
        class_distribution.to_csv("data_work/itog/class_distribution.csv", index=False)
        print("Class distribution saved to 'class_distribution.csv':")
        print(class_distribution)
    else:
        print("Warning: label_df пуст, метки не были найдены или прочитаны неправильно.")
    
    label_df.to_csv("data_work/itog/label_summary.csv", index=False)
    return label_df

# Функция для анализа меток с текстом
def analyze_labels_with_text(labels_with_text_path):
    label_with_text_data = []
    for label_file in os.listdir(labels_with_text_path):
        label_path = os.path.join(labels_with_text_path, label_file)
        with open(label_path, "r") as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split()
                
                # Поддержка текстового `class_id`
                class_id = parts[0]  # Оставляем `class_id` как текст
                
                # Проверка наличия координат и текста
                if len(parts) < 5:
                    print(f"Warning: Неверное количество элементов в строке {line} файла {label_file}")
                    continue
                
                try:
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    width = float(parts[3])
                    height = float(parts[4])
                except ValueError:
                    print(f"Warning: Неверные координаты в файле {label_file}: {parts[1:5]}")
                    continue

                # Обработка текста, если он присутствует
                text = " ".join(parts[5:]) if len(parts) > 5 else ""
                aspect_ratio = width / height if height != 0 else 0
                area = width * height
                special_symbols = any(c in text for c in "#%@")
                
                label_with_text_data.append({
                    "filename": label_file,
                    "class_id": class_id,  # Сохраняем class_id как текст
                    "bbox_width": width,
                    "bbox_height": height,
                    "bbox_area": area,
                    "aspect_ratio": aspect_ratio,
                    "text": text,
                    "text_length": len(text),
                    "special_symbols": special_symbols
                })

    label_with_text_df = pd.DataFrame(label_with_text_data)
    
    if not label_with_text_df.empty and "text" in label_with_text_df.columns:
        symbol_counts = pd.Series("".join(label_with_text_df["text"])).value_counts()
        symbol_counts.to_csv("data_work/itog/symbol_counts.csv", index=True, header=["frequency"])
    else:
        print("Warning: label_with_text_df пуст или не содержит столбца 'text', пропускаем анализ символов.")
    
    label_with_text_df.to_csv("data_work/itog/label_with_text_summary.csv", index=False)
    return label_with_text_df

# Функция для сравнения с grounded true train.csv и деталями по плану
def compare_with_grounded_true_and_details(label_with_text_df, grounded_true_path, details_plan_path):
    # Загрузка данных
    grounded_true_df = pd.read_csv(grounded_true_path)
    details_plan_df = pd.read_excel(details_plan_path)
    
    # Проверка на наличие данных и нужных столбцов в label_with_text_df
    if not label_with_text_df.empty and 'filename' in label_with_text_df.columns:
        # Сравнение с grounded_true
        comparison_grounded = label_with_text_df.merge(grounded_true_df, on="filename", how="outer", suffixes=('_detected', '_grounded'))
        comparison_grounded['text_match'] = comparison_grounded.apply(lambda x: x['text_detected'] == x['text_grounded'], axis=1)
        comparison_grounded.to_csv("data_work/itog/comparison_with_grounded_true.csv", index=False)
    else:
        print("Warning: label_with_text_df пуст или не содержит столбца 'filename', пропускаем сравнение с grounded true.")
        comparison_grounded = pd.DataFrame()  # Пустой DataFrame, если данных нет
    
    # Проверка на наличие столбца для сравнения текста с плановой маркировкой
    if not label_with_text_df.empty and 'text' in label_with_text_df.columns:
        # Сравнение с деталями по плану
        comparison_details = label_with_text_df.merge(details_plan_df, left_on="text", right_on="Плановая_Маркировка", how="outer", suffixes=('_detected', '_plan'))
        comparison_details['match_found'] = comparison_details.apply(lambda x: pd.notnull(x['Плановая_Маркировка']), axis=1)
        comparison_details.to_csv("data_work/itog/comparison_with_details_plan.csv", index=False)
    else:
        print("Warning: label_with_text_df пуст или не содержит столбца 'text', пропускаем сравнение с деталями по плану.")
        comparison_details = pd.DataFrame()  # Пустой DataFrame, если данных нет
    
    return comparison_grounded, comparison_details

# Функция для объединения всех сводок
def combine_summaries(image_df, label_df, label_with_text_df):
    # Сводка по меткам
    label_stats = label_df.groupby("filename").agg(
        num_bboxes=("class_id", "count"),
        avg_bbox_width=("bbox_width", "mean"),
        avg_bbox_height=("bbox_height", "mean"),
        avg_bbox_area=("bbox_area", "mean")
    ).reset_index()
    
    # Проверка на наличие столбца 'filename' в label_with_text_df
    if not label_with_text_df.empty and 'filename' in label_with_text_df.columns:
        label_with_text_stats = label_with_text_df.groupby("filename").agg(
            num_text_boxes=("class_id", "count"),
            avg_text_length=("text_length", "mean"),
            special_symbols_mean=("special_symbols", "mean")
        ).reset_index()
        
        # Объединение сводок изображений, меток и меток с текстом
        dataset_summary = image_df.merge(label_stats, on="filename", how="left")
        dataset_summary = dataset_summary.merge(label_with_text_stats, on="filename", how="left")
    else:
        print("Warning: label_with_text_df пуст или не содержит столбца 'filename', пропускаем объединение данных меток с текстом.")
        
        # Объединение только сводок изображений и меток
        dataset_summary = image_df.merge(label_stats, on="filename", how="left")
    
    # Сохранение итоговой таблицы
    dataset_summary.to_csv("data_work/itog/dataset_summary.csv", index=False)
    return dataset_summary

# Основная функция для запуска анализа
def main():
    print("Анализ изображений...")
    image_df = analyze_images(imgs_path)
    
    print("Анализ меток (bounding boxes)...")
    label_df = analyze_labels(labels_path)
    
    print("Анализ меток с текстом...")
    label_with_text_df = analyze_labels_with_text(labels_with_text_path)
    
    print("Сравнение с grounded true train.csv и деталями по плану...")
    compare_with_grounded_true_and_details(label_with_text_df, grounded_true_path, details_plan_path)
    
    print("Объединение и создание итоговой сводной таблицы...")
    dataset_summary = combine_summaries(image_df, label_df, label_with_text_df)
    
    print("Анализ завершен. Итоговые таблицы сохранены.")

# Запуск основного скрипта
if __name__ == "__main__":
    main()