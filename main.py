import qrcode
import tempfile
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from flask import Flask, request, jsonify, make_response
from flask_restx import Api, Resource
from brother_ql.raster import BrotherQLRaster
from brother_ql.conversion import convert
from brother_ql.backends.helpers import send

app = Flask(__name__)
api = Api(app, version='1.0', title='Print API', description='A simple API for printing QR codes')

ns = api.namespace('print', description='Printing operations')


def load_font(font_path=None, font_size=10):
    try:
        if font_path:
            return ImageFont.truetype(font_path, font_size)
        else:
            return ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        return ImageFont.load_default()


def create_qr_code(data, text, box_size=10, border=10):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill='black', back_color='white').convert('RGB')
        qr_width, qr_height = qr_img.size

        font_path = None
        font_size = 100
        font = load_font(font_path, font_size)
        draw = ImageDraw.Draw(qr_img)
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        while text_width > qr_width and font_size > 10:
            font_size -= 10
            font = load_font(font_path, font_size)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

        combined_img_width = max(qr_width, text_width)
        combined_img_height = qr_height + text_height + 20
        combined_img = Image.new('RGB', (combined_img_width, combined_img_height), 'white')
        combined_img.paste(qr_img, ((combined_img_width - qr_width) // 2, 0))

        draw = ImageDraw.Draw(combined_img)
        text_x = (combined_img_width - text_width) // 2
        text_y = qr_height + 1
        draw.text((text_x, text_y), text, fill='black', font=font)

        return combined_img
    except Exception as e:
        raise RuntimeError(f"Error creating QR code: {e}")


def resize_image(image, size):
    try:
        return image.resize(size, Image.LANCZOS)
    except UnidentifiedImageError as e:
        raise RuntimeError(f"Error resizing image: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error resizing image: {e}")


def print_qr_code(printer_name, label_type, image, rotate='0'):
    qlr = BrotherQLRaster('QL-800')
    label_width = 500
    label_height = 500

    try:
        resized_image = resize_image(image, (label_width, label_height))
        expanded_height = label_height + 5
        expanded_image = Image.new('RGB', (label_width, expanded_height), (255, 255, 255))
        expanded_image.paste(resized_image, (0, 0))
    except RuntimeError as e:
        raise RuntimeError(f"Error preparing image for printing: {e}")

    try:
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            expanded_image.save(tmp.name)
            convert(qlr, [tmp.name], label_type, rotate=rotate)
            send(qlr.data, printer_name, backend_identifier='pyusb', blocking=True)
    except IOError as e:
        raise RuntimeError(f"IOError during image conversion or sending: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error printing QR code: {e}")


@ns.route('/print')
class PrintResource(Resource):
    @api.doc(params={'count': 'Number of QR codes to print'},
             responses={200: 'Print successfully completed', 400: 'Invalid input', 500: 'Error printing'})
    def post(self):
        data = request.get_json()
        guid = data.get('guid')
        name = data.get('name')
        count = int(request.args.get('count', 1))

        if not guid or not name:
            return make_response(jsonify({"error": "GUID and name are required"}), 400)

        try:
            printer_name = 'usb://04f9:209b'
            label_type = '29'

            for i in range(count):
                qr_image = create_qr_code(guid, name, box_size=10, border=10)
                print_qr_code(printer_name, label_type, qr_image, rotate='0')
                print(f"Printed number {i + 1} of {count}")

            return make_response(jsonify({"status": "Print successfully completed"}), 200)
        except RuntimeError as e:
            return make_response(jsonify({"error": str(e)}), 500)
        except Exception as e:
            return make_response(jsonify({"error": f"Unexpected error: {e}"}), 500)


@ns.route('/debug/print')
class DebugPrintResource(Resource):
    @api.doc(params={'count': 'Number of QR codes to print'},
             responses={200: 'Debug print successfully completed', 500: 'Error printing'})
    def post(self):
        fixed_string = "https://www.youtube.com/watch?v=xvFZjo5PgG0"
        fixed_text = "Hier könnte Ihre Werbung stehen!"
        count = int(request.args.get('count', 1))

        try:
            printer_name = 'usb://04f9:209b'
            label_type = '29'

            for i in range(count):
                qr_image = create_qr_code(fixed_string, fixed_text, box_size=10, border=10)
                print_qr_code(printer_name, label_type, qr_image, rotate='0')
                print(f"Printed number {i + 1} of {count}")

            return make_response(jsonify({"status": "Debug print successfully completed"}), 200)
        except RuntimeError as e:
            return make_response(jsonify({"error": str(e)}), 500)
        except Exception as e:
            return make_response(jsonify({"error": f"Unexpected error: {e}"}), 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
