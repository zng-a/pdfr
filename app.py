import os
import logging
import sys
from flask import Flask, request, send_file, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

# Set up logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.debug("Application starting")

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a real secret key

# Ensure the upload folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

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

def cleanup_files(*file_paths):
    for file_path in file_paths:
        try:
            os.remove(file_path)
            logging.debug(f"Deleted file: {file_path}")
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    logging.debug("Upload route accessed")
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    if file and file.filename.lower().endswith('.pdf'):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'BYAZ_' + filename)
        file.save(input_path)
        logging.debug(f"File saved to {input_path}")
        try:
            remove_branding(input_path, output_path)
            logging.debug(f"Branding removed, processed file at {output_path}")
            
            # Send the file
            return_value = send_file(output_path, as_attachment=True, download_name='byaz_' + filename)
            
            # Clean up files after sending
            cleanup_files(input_path, output_path)
            
            return return_value
        except Exception as e:
            logging.error(f"Error processing PDF: {str(e)}")
            cleanup_files(input_path)  # Clean up input file if processing fails
            flash(f'Error processing PDF: {str(e)}')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload a PDF.')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    logging.debug("Health check route accessed")
    return 'OK', 200

if __name__ == "__main__":
    logging.debug("Starting Flask application")
    app.run(host='0.0.0.0', port=8000, debug=True)