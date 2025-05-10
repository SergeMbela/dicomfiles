# DICOM Viewer Web Application

A web-based DICOM viewer built with Flask that allows users to upload, view, and manipulate DICOM medical images.

## Features

- Upload and view DICOM files
- Interactive image manipulation:
  - Window/Level adjustment
  - Zoom controls
  - Image navigation (previous/next)
- Real-time image processing
- User-friendly web interface

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone <your-repository-url>
cd <repository-name>
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Dependencies

- Flask==2.0.1
- pydicom==2.3.0
- numpy==1.21.2
- Pillow==8.3.2
- werkzeug==2.0.1

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

3. Use the web interface to:
   - Upload DICOM files
   - View and navigate through images
   - Adjust window/level settings
   - Zoom in/out of images

## Project Structure

```
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── static/            # Static files (CSS, JS, images)
├── templates/         # HTML templates
└── uploads/          # Temporary storage for uploaded files
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask web framework
- pydicom library for DICOM file handling
- Pillow for image processing 
