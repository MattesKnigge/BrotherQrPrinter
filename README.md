# Print API

A simple API for printing QR codes using Flask.

## Requirements

- Python 3.6+
- [qrcode](https://pypi.org/project/qrcode/)
- [django-qrcode](https://pypi.org/project/django-qrcode/)
- [Pillow](https://pypi.org/project/Pillow/)
- [Flask](https://pypi.org/project/Flask/)
- [requests](https://pypi.org/project/requests/)
- [brother_ql](https://pypi.org/project/brother_ql/)

## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Create and activate a virtual environment (optional but recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Running the App

1. Start the Flask app:
    ```sh
    python app.py
    ```

2. The app will be running on `http://localhost:5000`.

## Endpoints

### `/print`

- **Method**: POST
- **Description**: Prints QR codes.
- **Parameters**:
    - `guid`: The GUID for the QR code.
    - `name`: The name to be printed below the QR code.
    - `count`: Number of QR codes to print (default is 1).
- **Responses**:
    - `200`: Print successfully completed.
    - `400`: Invalid input.
    - `500`: Error printing.

#### Example Request

Using `curl`:
```sh
curl -X POST "http://localhost:5000/print" -H "Content-Type: application/json" -d '{"guid": "your-guid", "name": "your-name"}'
