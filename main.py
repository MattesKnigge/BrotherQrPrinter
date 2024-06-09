import qrcode
import tempfile
import requests
from PIL import Image
from flask import Flask, jsonify, make_response
from flask_restx import Api, Resource
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send

app = Flask(__name__)
api = Api(app, version='1.0', title='Print API',
          description='A simple API for printing QR codes',
          )

ns = api.namespace('print', description='Printing operations')


def create_qr_code(data, box_size=5, border=20):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    img = img.convert('RGB')
    return img


def resize_image(image, size):
    return image.resize(size, Image.Resampling.LANCZOS)  # Ensure correct usage of Resampling


def print_qr_code(printer_name, label_type, image, rotate='0'):
    qlr = BrotherQLRaster('QL-800')
    label_width = 500
    label_height = 500

    resized_image = resize_image(image, (label_width, label_height))

    expanded_height = label_height + 5
    expanded_image = Image.new('RGB', (label_width, expanded_height), (255, 255, 255))
    expanded_image.paste(resized_image, (0, 0))

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        expanded_image.save(tmp.name)
        try:
            print("Conversion started...")
            convert(qlr, [tmp.name], label_type, rotate=rotate)
            print("Conversion completed. Sending print job...")
            send(qlr.data, printer_name, backend_identifier='pyusb', blocking=True)
            print(f"Print successfully completed.")
        except Exception as e:
            print(f"Error printing: {e}")


@ns.route('/print')
class PrintResource(Resource):
    @api.doc(responses={200: 'Print successfully completed', 500: 'Error fetching the GUID or printing'})
    def post(self):
        guid_endpoint = "http://example.com/get-guid"  # Replace with actual endpoint URL
        try:
            response = requests.get(guid_endpoint)
            response.raise_for_status()
            response_data = response.json()
            fixed_guid = response_data.get('value')
            if not fixed_guid:
                return make_response(jsonify({"error": "GUID not found in response"}), 500)

            qr_image = create_qr_code(fixed_guid, box_size=5, border=20)

            printer_name = 'usb://04f9:209b'  # Replace with the actual VID and PID of your printer
            label_type = '29'  # Label size

            print_qr_code(printer_name, label_type, qr_image, rotate='0')

            return make_response(jsonify({"status": "Print successfully completed"}), 200)
        except requests.RequestException as e:
            return make_response(jsonify({"error": f"Error fetching the GUID: {e}"}), 500)


@ns.route('/debug/print')
class DebugPrintResource(Resource):
    @api.doc(responses={200: 'Debug print successfully completed', 500: 'Error printing'})
    def post(self):
        fixed_string = "https://www.youtube.com/watch?v=xvFZjo5PgG0"
        try:
            qr_image = create_qr_code(fixed_string, box_size=5, border=20)

            printer_name = 'usb://04f9:209b'  # Replace with the actual VID and PID of your printer
            label_type = '29'  # Label size

            print_qr_code(printer_name, label_type, qr_image, rotate='0')

            return make_response(jsonify({"status": "Debug print successfully completed"}), 200)
        except Exception as e:
            return make_response(jsonify({"error": f"Error printing: {e}"}), 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
