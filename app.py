import logging
logging.basicConfig(level=logging.DEBUG)
logging.debug("Application starting")

import os
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

app = Flask(__name__)

# Ensure the upload folder exists and create it if it doesn't
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def remove_branding(input_pdf_path, output_pdf_path):
    with open(input_pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            mediabox = page.mediabox
            width = mediabox.width
            height = mediabox.height

            # Create a white rectangle to cover the bottom 10%
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=(width, height))
            can.setFillColorRGB(1, 1, 1)  # Set fill color to white
            can.rect(0, 0, width, height * 0.1, fill=1, stroke=0)
            can.save()

            # Create a new PDF with the white rectangle
            white_rect = PyPDF2.PdfReader(packet).pages[0]

            # Merge the original page with the white rectangle
            page.merge_page(white_rect)

            writer.add_page(page)

        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
            file.save(input_path)
            remove_branding(input_path, output_path)
            return send_file(output_path, as_attachment=True)
    return '''
    <!doctype html>
    <html>
    <head>
        <title>PDF Branding Remover</title>
    </head>
    <body>
        <h1>Upload PDF to Remove Branding</h1>
        <form method=post enctype=multipart/form-data>
            <input type=file name=file accept=".pdf">
            <input type=submit value=Upload>
        </form>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)