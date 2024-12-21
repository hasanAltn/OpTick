from flask import Flask, request, jsonify
from PIL import Image
import io
import cv2
import numpy as np
import os
import base64

TEMP_IMG_PATH = os.path.join(os.getcwd(), "processed_image.png")
app = Flask(__name__)

# Çemberin işaretlenip işaretlenmediğini kontrol etme fonksiyonu
def is_circle_filled(x, y, r, image):
    # Çemberin içindeki pikselleri kontrol et
    circle_region = image[y - r:y + r, x - r:x + r]
    non_white_pixels = np.sum(circle_region < 200)  # Beyaz olmayan piksel sayısını say
    if non_white_pixels > (np.pi * r * r) * 0.5:  # Yüzde 50'den fazla işaretlenmişse
        return True
    return False

@app.route('/process-image', methods=['POST'])
def process_image():
    # Fotoğrafı al
    image_file = request.files['image']
    img = Image.open(image_file.stream)

    # Resmi NumPy array'e çevir
    img_np = np.array(img)

    # Gri tonlamaya çevir
    gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)

    # Kenar algılama
    edges = cv2.Canny(gray, 50, 150)

    # Çemberleri tespit et (Hough Transform)
    circles = cv2.HoughCircles(
        edges,
        cv2.HOUGH_GRADIENT, dp=1.2, minDist=20, param1=50, param2=30, minRadius=10, maxRadius=20
    )
    results = {}  # Sonuçları saklamak için bir sözlük oluşturuyoruz

    # Eğer çemberler bulunduysa
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        sorted_circles = sorted(circles, key=lambda c: (c[1], c[0]))  # Y eksenine göre sıralama

        # 5 şıklı sorular için çemberleri kontrol et
        choice_labels = ['A', 'B', 'C', 'D', 'E']
        question_num = 1
        for i in range(0, len(sorted_circles), 5):
            question_choices = sorted_circles[i:i + 5]
            correct_choice = None

            # 5 şıkkı kontrol et ve işaretlenen şıkkı bul
            for idx, (x, y, r) in enumerate(question_choices):
                # Çemberin etrafına yeşil bir daire çiz
                cv2.circle(img_np, (x, y), r, (0, 255, 0), 4)

                # Çemberin işaretlenip işaretlenmediğini kontrol et
                if is_circle_filled(x, y, r, gray):
                    cv2.circle(img_np, (x, y), r, (0, 0, 255), 4)
                    # İşaretlenen şık doğru cevap olarak kabul edilir
                    correct_choice = choice_labels[idx]
                    results[f"Question {question_num}"] = f"Answer: {correct_choice}"
                    question_num += 1
    else:
        results["message"] = "Çemberler bulunamadı."


    # İşlenmiş görüntüyü kaydet
    processed_image_path = TEMP_IMG_PATH
    cv2.imwrite(processed_image_path, cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR))

    # Görseli Base64'e dönüştürme
    with open(processed_image_path, "rb") as image_file:
        img_bytes = image_file.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")  # Base64 kodunu elde et

    return jsonify({
        'results': results,
        'processed_image': img_base64  # Base64 kodunu JSON ile gönder
    }), 200

if __name__ == '__main__':
    # Flask uygulamasını başlat
    app.run(host='0.0.0.0', port=5000)
