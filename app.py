import logging
import sys
import os
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# Set up logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.debug("Application starting")

app = Flask(__name__)

# Ensure the upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def remove_branding(input_pdf_path, output_pdf_path):
    logging.debug(f"Processing PDF: {input_pdf_path}")
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

        logging.debug(f"Writing processed PDF to: {output_pdf_path}")
        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)

@app.route('/')
def hello():
    logging.debug("Hello route accessed")
    return "Hello, World! PDF Branding Remover is running."

@app.route('/health')
def health_check():
    logging.debug("Health check route accessed")
    return 'OK', 200

@app.route('/remove-branding', methods=['POST'])
def upload_file():
    logging.debug("Remove branding route accessed")
    if 'file' not in request.files:
        logging.error("No file part in the request")
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        logging.error("No selected file")
        return 'No selected file', 400
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
        file.save(input_path)
        logging.debug(f"File saved to {input_path}")
        try:
            remove_branding(input_path, output_path)
            logging.debug(f"Branding removed, processed file at {output_path}")
            return send_file(output_path, as_attachment=True)
        except Exception as e:
            logging.error(f"Error processing PDF: {str(e)}")
            return f'Error processing PDF: {str(e)}', 500
    else:
        logging.error("Invalid file type")
        return 'Invalid file type. Please upload a PDF.', 400

if __name__ == "__main__":
    logging.debug("Starting Flask application")
    app.run(host='0.0.0.0', port=8000)