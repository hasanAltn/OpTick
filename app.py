from flask import Flask, request, send_file
from PIL import Image
import io

app = Flask(__name__)


@app.route('/process-image', methods=['POST'])
def process_image():
    # Fotoğrafı al
    image_file = request.files['image']


    # Fotoğrafı yükle ve işleme
    img = Image.open(image_file.stream)

    # Örneğin, resmi gri tonlamaya çevir
    img = img.convert('L')

    # Fotoğrafı bellek üzerinden gönder
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # İşlenmiş fotoğrafı geri gönder
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='processed_image.png')


if __name__ == '__main__':
    # Flask uygulamasını başlat
    app.run(host='0.0.0.0', port=5000)
