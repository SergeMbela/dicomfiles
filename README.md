# DICOM Viewer

A web-based DICOM viewer built with Flask that allows users to upload and view DICOM files with window/level adjustments and image navigation.

## Features

- Upload and view DICOM files
- Adjust window width and center for better image contrast
- Rotate images
- Navigate between multiple images
- Support for both single-frame and multi-frame DICOM files

## Requirements

- Python 3.11+
- Flask
- PyDICOM
- NumPy
- Pillow

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dicom-viewer
```

2. Create and activate a virtual environment:
```bash
conda create -n dicom_viewer python=3.11
conda activate dicom_viewer
```

3. Install dependencies:
```bash
pip install flask pydicom numpy pillow
```

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5002
```

3. Use the interface to:
   - Upload DICOM files
   - Adjust window width and center
   - Rotate images
   - Navigate between multiple images

## License

MIT License 