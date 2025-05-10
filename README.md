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

## Supported Image Formats

- DICOM files (`.dcm`, `.dicom`)
- Single-frame DICOM images
- Multi-frame DICOM series
- Grayscale medical images
- 8-bit and 16-bit depth images

## Image Processing Features

- Automatic window/level optimization
- Image normalization
- Real-time contrast adjustment
- Support for various DICOM transfer syntaxes
- Metadata display and extraction
- Image measurements and annotations

## Advanced Image Visualization

### Window/Level Controls
- Dynamic window width and center adjustment
- Preset window/level values for common modalities
- Real-time preview of adjustments
- Automatic window/level calculation based on image statistics

### Image Navigation
- Slice-by-slice navigation for 3D volumes
- Series navigation for multi-frame studies
- Thumbnail preview of adjacent slices
- Quick jump to specific slice numbers

### Image Manipulation
- Pan and zoom functionality
- Image rotation (90°, 180°, 270°)
- Flip horizontal/vertical
- Reset view to original state
- Magnifying glass tool for detailed inspection

### Measurement Tools
- Distance measurement
- Area calculation
- Angle measurement
- ROI (Region of Interest) selection
- Pixel value analysis

### Image Enhancement
- Contrast enhancement
- Brightness adjustment
- Sharpness control
- Noise reduction options
- Edge enhancement

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
   - View DICOM metadata
   - Export processed images
   - Use measurement tools
   - Apply image enhancements

## Image Handling

The application processes DICOM images with the following capabilities:
- Automatic detection of image orientation
- Support for various pixel representations
- Handling of different photometric interpretations
- Proper scaling of pixel values
- Support for both signed and unsigned pixel data
- Automatic handling of modality-specific window/level presets

### Image Export Options
- Save as PNG/JPG
- Export with measurements and annotations
- Save window/level settings
- Export metadata in various formats
- Batch export for multiple images

### Performance Optimization
- Efficient memory management for large datasets
- Progressive loading for multi-frame studies
- Caching of processed images
- Optimized rendering for smooth interaction
- Background processing for heavy operations

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