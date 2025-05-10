from flask import Flask, render_template, request, jsonify, send_file
import pydicom
import os
from werkzeug.utils import secure_filename
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import glob
import io
import tempfile
import shutil
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'dcm', 'dicom'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_dicom_info(dicom_file):
    ds = pydicom.dcmread(dicom_file)
    info = {}
    
    # Get comprehensive DICOM information
    try:
        # Patient Information
        info['PatientInfo'] = {
            'PatientName': str(getattr(ds, 'PatientName', 'N/A')),
            'PatientID': str(getattr(ds, 'PatientID', 'N/A')),
            'PatientBirthDate': str(getattr(ds, 'PatientBirthDate', 'N/A')),
            'PatientSex': str(getattr(ds, 'PatientSex', 'N/A')),
            'PatientAge': str(getattr(ds, 'PatientAge', 'N/A')),
            'PatientWeight': str(getattr(ds, 'PatientWeight', 'N/A')),
            'PatientOrientation': str(getattr(ds, 'PatientOrientation', 'N/A')),
            'PatientPosition': str(getattr(ds, 'PatientPosition', 'N/A'))
        }
        
        # Study Information
        info['StudyInfo'] = {
            'StudyDate': str(getattr(ds, 'StudyDate', 'N/A')),
            'StudyTime': str(getattr(ds, 'StudyTime', 'N/A')),
            'StudyDescription': str(getattr(ds, 'StudyDescription', 'N/A')),
            'StudyInstanceUID': str(getattr(ds, 'StudyInstanceUID', 'N/A')),
            'StudyID': str(getattr(ds, 'StudyID', 'N/A')),
            'AccessionNumber': str(getattr(ds, 'AccessionNumber', 'N/A')),
            'ReferringPhysicianName': str(getattr(ds, 'ReferringPhysicianName', 'N/A')),
            'StudyPriorityID': str(getattr(ds, 'StudyPriorityID', 'N/A')),
            'StudyStatusID': str(getattr(ds, 'StudyStatusID', 'N/A'))
        }
        
        # Series Information
        info['SeriesInfo'] = {
            'SeriesDescription': str(getattr(ds, 'SeriesDescription', 'N/A')),
            'SeriesNumber': str(getattr(ds, 'SeriesNumber', 'N/A')),
            'SeriesInstanceUID': str(getattr(ds, 'SeriesInstanceUID', 'N/A')),
            'Modality': str(getattr(ds, 'Modality', 'N/A')),
            'SeriesDate': str(getattr(ds, 'SeriesDate', 'N/A')),
            'SeriesTime': str(getattr(ds, 'SeriesTime', 'N/A')),
            'ProtocolName': str(getattr(ds, 'ProtocolName', 'N/A')),
            'SeriesType': str(getattr(ds, 'SeriesType', 'N/A')),
            'SeriesModality': str(getattr(ds, 'SeriesModality', 'N/A')),
            'BodyPartExamined': str(getattr(ds, 'BodyPartExamined', 'N/A')),
            'ViewPosition': str(getattr(ds, 'ViewPosition', 'N/A'))
        }
        
        # Image Information
        info['ImageInfo'] = {
            'ImageType': str(getattr(ds, 'ImageType', 'N/A')),
            'InstanceNumber': str(getattr(ds, 'InstanceNumber', 'N/A')),
            'ImageSize': f"{ds.Rows}x{ds.Columns}",
            'PixelSpacing': str(getattr(ds, 'PixelSpacing', 'N/A')),
            'SliceThickness': str(getattr(ds, 'SliceThickness', 'N/A')),
            'SpacingBetweenSlices': str(getattr(ds, 'SpacingBetweenSlices', 'N/A')),
            'ImageOrientation': str(getattr(ds, 'ImageOrientationPatient', 'N/A')),
            'ImagePosition': str(getattr(ds, 'ImagePositionPatient', 'N/A')),
            'SamplesPerPixel': str(getattr(ds, 'SamplesPerPixel', 'N/A')),
            'PhotometricInterpretation': str(getattr(ds, 'PhotometricInterpretation', 'N/A')),
            'PlanarConfiguration': str(getattr(ds, 'PlanarConfiguration', 'N/A')),
            'PixelAspectRatio': str(getattr(ds, 'PixelAspectRatio', 'N/A')),
            'ImageFormat': str(getattr(ds, 'ImageFormat', 'N/A')),
            'LossyImageCompression': str(getattr(ds, 'LossyImageCompression', 'N/A')),
            'LossyImageCompressionRatio': str(getattr(ds, 'LossyImageCompressionRatio', 'N/A')),
            'ImageComments': str(getattr(ds, 'ImageComments', 'N/A'))
        }
        
        # Window/Level Information
        info['WindowLevelInfo'] = {
            'WindowCenter': str(getattr(ds, 'WindowCenter', 'N/A')),
            'WindowWidth': str(getattr(ds, 'WindowWidth', 'N/A')),
            'RescaleIntercept': str(getattr(ds, 'RescaleIntercept', 'N/A')),
            'RescaleSlope': str(getattr(ds, 'RescaleSlope', 'N/A')),
            'WindowCenterWidthExplanation': str(getattr(ds, 'WindowCenterWidthExplanation', 'N/A')),
            'VOILUTFunction': str(getattr(ds, 'VOILUTFunction', 'N/A')),
            'VOILUTSequence': str(getattr(ds, 'VOILUTSequence', 'N/A')),
            'PresentationLUTShape': str(getattr(ds, 'PresentationLUTShape', 'N/A'))
        }
        
        # Technical Information
        info['TechnicalInfo'] = {
            'Manufacturer': str(getattr(ds, 'Manufacturer', 'N/A')),
            'ManufacturerModelName': str(getattr(ds, 'ManufacturerModelName', 'N/A')),
            'DeviceSerialNumber': str(getattr(ds, 'DeviceSerialNumber', 'N/A')),
            'SoftwareVersions': str(getattr(ds, 'SoftwareVersions', 'N/A')),
            'KVP': str(getattr(ds, 'KVP', 'N/A')),
            'ExposureTime': str(getattr(ds, 'ExposureTime', 'N/A')),
            'XRayTubeCurrent': str(getattr(ds, 'XRayTubeCurrent', 'N/A')),
            'Exposure': str(getattr(ds, 'Exposure', 'N/A')),
            'ExposureInuAs': str(getattr(ds, 'ExposureInuAs', 'N/A')),
            'FocalSpots': str(getattr(ds, 'FocalSpots', 'N/A')),
            'FilterType': str(getattr(ds, 'FilterType', 'N/A')),
            'GeneratorPower': str(getattr(ds, 'GeneratorPower', 'N/A')),
            'CollimatorGridName': str(getattr(ds, 'CollimatorGridName', 'N/A')),
            'DistanceSourceToDetector': str(getattr(ds, 'DistanceSourceToDetector', 'N/A')),
            'DistanceSourceToPatient': str(getattr(ds, 'DistanceSourceToPatient', 'N/A')),
            'PixelRepresentation': str(getattr(ds, 'PixelRepresentation', 'N/A')),
            'BitsAllocated': str(getattr(ds, 'BitsAllocated', 'N/A')),
            'BitsStored': str(getattr(ds, 'BitsStored', 'N/A')),
            'HighBit': str(getattr(ds, 'HighBit', 'N/A')),
            'PixelPaddingValue': str(getattr(ds, 'PixelPaddingValue', 'N/A')),
            'PixelPaddingRangeLimit': str(getattr(ds, 'PixelPaddingRangeLimit', 'N/A'))
        }
        
        # Acquisition Information
        info['AcquisitionInfo'] = {
            'AcquisitionDate': str(getattr(ds, 'AcquisitionDate', 'N/A')),
            'AcquisitionTime': str(getattr(ds, 'AcquisitionTime', 'N/A')),
            'AcquisitionNumber': str(getattr(ds, 'AcquisitionNumber', 'N/A')),
            'AcquisitionDeviceProcessingDescription': str(getattr(ds, 'AcquisitionDeviceProcessingDescription', 'N/A')),
            'AcquisitionProtocol': str(getattr(ds, 'AcquisitionProtocol', 'N/A')),
            'AcquisitionType': str(getattr(ds, 'AcquisitionType', 'N/A')),
            'AcquisitionMatrix': str(getattr(ds, 'AcquisitionMatrix', 'N/A')),
            'AcquisitionDuration': str(getattr(ds, 'AcquisitionDuration', 'N/A')),
            'AcquisitionDatetime': str(getattr(ds, 'AcquisitionDatetime', 'N/A'))
        }
        
        # Image Quality Information
        info['QualityInfo'] = {
            'ImageQuality': str(getattr(ds, 'ImageQuality', 'N/A')),
            'ImageQualityIndicator': str(getattr(ds, 'ImageQualityIndicator', 'N/A')),
            'ImageQualityRating': str(getattr(ds, 'ImageQualityRating', 'N/A')),
            'ImageQualityRatingDescription': str(getattr(ds, 'ImageQualityRatingDescription', 'N/A')),
            'ImageQualityRatingValue': str(getattr(ds, 'ImageQualityRatingValue', 'N/A')),
            'ImageQualityRatingValueDescription': str(getattr(ds, 'ImageQualityRatingValueDescription', 'N/A'))
        }
        
        # Add image statistics
        try:
            pixel_array = ds.pixel_array
            info['ImageStatistics'] = {
                'MinValue': str(float(pixel_array.min())),
                'MaxValue': str(float(pixel_array.max())),
                'MeanValue': str(float(pixel_array.mean())),
                'StdDeviation': str(float(pixel_array.std())),
                'ImageHistogram': str(np.histogram(pixel_array, bins=256)[0].tolist())
            }
        except:
            info['ImageStatistics'] = 'Not available'
        
    except Exception as e:
        print(f"Error extracting DICOM info: {str(e)}")
    
    return info

def get_dicom_image(dicom_file, window_center=None, window_width=None, rotation=0):
    ds = pydicom.dcmread(dicom_file)
    
    try:
        # Get pixel data
        image = ds.pixel_array
        
        # Print debug information
        print(f"Image shape: {image.shape}")
        print(f"Image dtype: {image.dtype}")
        
        # Handle different data types and shapes
        if image.dtype == np.uint8:
            if image.shape == (1, 1, 512):
                # For (1, 1, 512) shape, reshape to (512, 512)
                image = np.tile(image[0, 0], (512, 1))
            elif image.max() > 0:
                image = (image.astype(float) / image.max() * 255.0).astype(np.uint8)
        else:
            # Convert to float and normalize
            image = image.astype(float)
            
            # Apply window/level if provided
            if window_center is not None and window_width is not None:
                window_min = window_center - window_width / 2
                window_max = window_center + window_width / 2
                image = np.clip(image, window_min, window_max)
                image = ((image - window_min) / (window_max - window_min) * 255.0).astype(np.uint8)
            else:
                # Default normalization
                image = ((image - image.min()) / (image.max() - image.min()) * 255.0).astype(np.uint8)
        
        # Handle multi-frame images
        if len(image.shape) > 2:
            # Take the first frame if it's a multi-frame image
            image = image[0] if image.shape[0] == 1 else image
        
        # Ensure the image is 2D
        if len(image.shape) > 2:
            image = image.reshape(image.shape[0], -1)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image)
        
        # Apply rotation if specified
        if rotation != 0:
            pil_image = pil_image.rotate(rotation, expand=True)
        
        # Convert to base64 for display
        buffered = BytesIO()
        pil_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return img_str
        
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        print(f"Image shape: {image.shape if 'image' in locals() else 'Not available'}")
        print(f"Image dtype: {image.dtype if 'image' in locals() else 'Not available'}")
        raise Exception(f"Error processing DICOM image: {str(e)}")

def process_dicomdir(dicomdir_path):
    """Process a DICOMDIR file and return a list of DICOM file paths."""
    try:
        # Read the DICOMDIR file
        ds = pydicom.dcmread(dicomdir_path)
        base_dir = os.path.dirname(dicomdir_path)
        file_paths = []
        
        # Process each directory record
        for record in ds.DirectoryRecordSequence:
            if record.DirectoryRecordType == "IMAGE":
                # Get the referenced file path
                ref_file = record.ReferencedFileID
                if ref_file:
                    # Convert the referenced file path to a proper path
                    file_path = os.path.join(base_dir, *ref_file)
                    if os.path.exists(file_path):
                        file_paths.append(file_path)
        
        return file_paths
    except Exception as e:
        print(f"Error processing DICOMDIR: {str(e)}")
        return []

def process_dicom_file(file_path, window_width=2000, window_center=1000):
    """Process a DICOM file and return image data and metadata."""
    try:
        ds = pydicom.dcmread(file_path)
        
        # Get pixel data
        pixel_array = ds.pixel_array
        print(f"Original pixel array shape: {pixel_array.shape}, dtype: {pixel_array.dtype}")
        
        # Handle multi-frame images
        if len(pixel_array.shape) > 2:
            # For multi-frame images, take the first frame
            if pixel_array.shape[0] == 1:
                pixel_array = pixel_array[0]
            else:
                # If it's a true multi-frame image, take the first frame
                pixel_array = pixel_array[0]
        
        # Handle specific case for (1, 1, 512) uint8
        if pixel_array.dtype == np.uint8 and pixel_array.shape == (1, 1, 512):
            print("Handling (1, 1, 512) uint8 case")
            # Extract the 1D array and reshape it
            pixel_array = pixel_array[0, 0]  # Get the 512-length array
            pixel_array = np.tile(pixel_array, (512, 1))  # Create a 512x512 image
        
        # Ensure we have a 2D array
        if len(pixel_array.shape) > 2:
            # Take the first slice if we still have a 3D array
            pixel_array = pixel_array[0]
        
        print(f"Final pixel array shape: {pixel_array.shape}, dtype: {pixel_array.dtype}")
        
        # Convert to float for window/level operations
        pixel_array = pixel_array.astype(float)
        
        # Apply window/level
        min_value = window_center - window_width // 2
        max_value = window_center + window_width // 2
        
        # Clip values to window range
        pixel_array = np.clip(pixel_array, min_value, max_value)
        
        # Normalize to 0-255
        pixel_array = ((pixel_array - min_value) / (max_value - min_value) * 255).astype(np.uint8)
        
        # Convert to PIL Image
        image = Image.fromarray(pixel_array)
        
        # Convert to PNG
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        # Get comprehensive DICOM metadata
        metadata = get_dicom_info(file_path)
        
        return img_byte_arr, metadata
    except Exception as e:
        print(f"Error processing DICOM file: {str(e)}")
        print(f"File path: {file_path}")
        if 'pixel_array' in locals():
            print(f"Pixel array shape: {pixel_array.shape}")
            print(f"Pixel array dtype: {pixel_array.dtype}")
        return None, None

def apply_window_level(pixel_array, window_width, window_center):
    """Apply window/level to the pixel array."""
    # Convert to float for calculations
    pixel_array = pixel_array.astype(float)
    
    min_value = window_center - window_width // 2
    max_value = window_center + window_width // 2
    
    # Clip values to window range
    pixel_array = np.clip(pixel_array, min_value, max_value)
    
    # Normalize to 0-255
    pixel_array = ((pixel_array - min_value) / (max_value - min_value) * 255).astype(np.uint8)
    
    return pixel_array

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        print("No files part in request")
        return jsonify({'success': False, 'error': 'No file part'})
    
    files = request.files.getlist('files')
    if not files:
        print("No files selected")
        return jsonify({'success': False, 'error': 'No selected file'})
    
    try:
        # Create a temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            processed_files = []
            all_metadata = {}
            
            for file in files:
                if file.filename:
                    print(f"Processing file: {file.filename}")
                    # Save the uploaded file
                    file_path = os.path.join(temp_dir, file.filename)
                    file.save(file_path)
                    print(f"Saved file to: {file_path}")
                    
                    # Check if it's a DICOMDIR file
                    if file.filename.upper() == 'DICOMDIR' or file.filename.lower().endswith('.dicomdir'):
                        print("Processing DICOMDIR file")
                        # Process DICOMDIR
                        dicom_files = process_dicomdir(file_path)
                        print(f"Found {len(dicom_files)} files in DICOMDIR")
                        for dicom_file in dicom_files:
                            processed_files.append(dicom_file)
                    else:
                        # Process single DICOM file
                        try:
                            ds = pydicom.dcmread(file_path)
                            print(f"Successfully read DICOM file: {file.filename}")
                            processed_files.append(file_path)
                        except Exception as e:
                            print(f"Error reading DICOM file {file.filename}: {str(e)}")
                            continue
            
            # Sort files by name to maintain order
            processed_files.sort()
            print(f"Total processed files: {len(processed_files)}")
            
            # Process the first file to get initial image and metadata
            if processed_files:
                first_file = processed_files[0]
                print(f"Processing first file: {first_file}")
                img_data, metadata = process_dicom_file(first_file)
                
                if img_data and metadata:
                    # Save the processed files to the upload folder
                    for i, file_path in enumerate(processed_files):
                        new_path = os.path.join(app.config['UPLOAD_FOLDER'], f'file_{i}.dcm')
                        shutil.copy2(file_path, new_path)
                        print(f"Copied file to: {new_path}")
                    
                    return jsonify({
                        'success': True,
                        'files': [f'file_{i}.dcm' for i in range(len(processed_files))],
                        'dicom_info': metadata
                    })
            
            print("No valid DICOM files found after processing")
            return jsonify({'success': False, 'error': 'No valid DICOM files found'})
            
    except Exception as e:
        print(f"Error in upload_file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_image/<int:index>')
def get_image(index):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'file_{index}.dcm')
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        img_data, _ = process_dicom_file(file_path)
        if img_data:
            return send_file(img_data, mimetype='image/png')
        else:
            return jsonify({'success': False, 'error': 'Error processing image'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update_window_level', methods=['POST'])
def update_window_level():
    try:
        data = request.json
        index = data.get('index')
        window_width = data.get('window_width', 2000)
        window_center = data.get('window_center', 1000)
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'file_{index}.dcm')
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        img_data, _ = process_dicom_file(file_path, window_width, window_center)
        if img_data:
            return send_file(img_data, mimetype='image/png')
        else:
            return jsonify({'success': False, 'error': 'Error processing image'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/info/<int:index>')
def show_info(index):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'file_{index}.dcm')
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Get DICOM information
        dicom_info = get_dicom_info(file_path)
        
        return render_template('info.html', dicom_info=dicom_info)
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5002) 