from flask import Flask, request, send_file, jsonify
from PIL import Image
import io
import pytesseract
import cv2
import numpy as np

app = Flask(__name__)

# Tesseract yolunu belirtme
pytesseract.pytesseract.tesseract_cmd = r'"""C:\Users\Hasan\OneDrive\Belgeler\Tesseract"""'

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

    filled_circles = []
    filled_circles_data = []

    # Eğer çemberler bulunduysa
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        for (x, y, r) in circles:
            # Çemberin etrafına yeşil bir daire çiz
            cv2.circle(img_np, (x, y), r, (0, 255, 0), 4)

            # Çemberin işaretlenip işaretlenmediğini kontrol et
            if is_circle_filled(x, y, r, gray):
                filled_circles.append((x, y))
                filled_circles_data.append({"circle_center": (x, y), "filled": True})
            else:
                filled_circles_data.append({"circle_center": (x, y), "filled": False})

    # OCR ile metin tanıma (optik formdaki yazılar)
    text = pytesseract.image_to_string(gray)

    # İşlenmiş görüntüyü bellek üzerinde tutma
    img_io = io.BytesIO()
    processed_img = Image.fromarray(cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB))
    processed_img.save(img_io, 'PNG')
    img_io.seek(0)

    # Görseli ve JSON verisini aynı anda döndürmek için:
    response = {
        "text": text,
        "filled_circles": filled_circles_data
    }

    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=True,
        download_name='processed_image.png'
    ), jsonify(response)

if __name__ == '__main__':
    # Flask uygulamasını başlat
    app.run(host='0.0.0.0', port=5000)
