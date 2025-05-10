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
    """Extract relevant information from DICOM file"""
    ds = pydicom.dcmread(dicom_file)
    info = {
        'PatientName': str(ds.get('PatientName', 'N/A')),
        'PatientID': str(ds.get('PatientID', 'N/A')),
        'StudyDate': str(ds.get('StudyDate', 'N/A')),
        'Modality': str(ds.get('Modality', 'N/A')),
        'ImageType': str(ds.get('ImageType', 'N/A')),
        'Rows': str(ds.get('Rows', 'N/A')),
        'Columns': str(ds.get('Columns', 'N/A')),
        'PixelSpacing': str(ds.get('PixelSpacing', 'N/A')),
        'WindowCenter': str(ds.get('WindowCenter', 'N/A')),
        'WindowWidth': str(ds.get('WindowWidth', 'N/A')),
    }
    return info

def dicom_to_image(dicom_file, frame=0):
    """Convert DICOM file to PNG image"""
    ds = pydicom.dcmread(dicom_file)
    
    # Get pixel data
    pixel_array = ds.pixel_array
    print(f"Original pixel array shape: {pixel_array.shape}, dtype: {pixel_array.dtype}")
    
    # Handle specific case for (1, 1, N) uint8
    if pixel_array.dtype == np.uint8 and len(pixel_array.shape) == 3 and pixel_array.shape[0] == 1 and pixel_array.shape[1] == 1:
        print("Handling (1, 1, N) uint8 case")
        # Extract the 1D array and reshape it
        pixel_array = pixel_array[0, 0]  # Get the N-length array
        # Create a square image by repeating the array
        size = int(np.ceil(np.sqrt(len(pixel_array))))
        # Pad the array to make it square
        padded_array = np.pad(pixel_array, (0, size * size - len(pixel_array)))
        # Reshape to square
        pixel_array = padded_array.reshape(size, size)
    
    # Handle multi-frame images
    elif len(pixel_array.shape) > 2:
        if frame >= pixel_array.shape[0]:
            frame = 0
        pixel_array = pixel_array[frame]
    
    # Normalize the pixel data
    if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
        window_center = ds.WindowCenter
        window_width = ds.WindowWidth
        if isinstance(window_center, pydicom.multival.MultiValue):
            window_center = window_center[0]
        if isinstance(window_width, pydicom.multival.MultiValue):
            window_width = window_width[0]
        
        pixel_array = np.clip(pixel_array, 
                            window_center - window_width//2,
                            window_center + window_width//2)
    
    # Normalize to 0-255
    pixel_array = ((pixel_array - pixel_array.min()) * 255.0 / 
                  (pixel_array.max() - pixel_array.min())).astype(np.uint8)
    
    # Convert to PIL Image
    image = Image.fromarray(pixel_array)
    
    # Convert to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str

def get_dicom_image(dicom_file, window_center=None, window_width=None, rotation=0):
    try:
        print(f"Processing DICOM file: {dicom_file}")
        ds = pydicom.dcmread(dicom_file)
        
        # Get pixel data
        image = ds.pixel_array
        print(f"Original image shape: {image.shape}, dtype: {image.dtype}")
        
        # Get pixel spacing for measurements
        pixel_spacing = getattr(ds, 'PixelSpacing', [1.0, 1.0])
        if isinstance(pixel_spacing, pydicom.multival.MultiValue):
            pixel_spacing = [float(x) for x in pixel_spacing]
        else:
            pixel_spacing = [1.0, 1.0]
        
        # Handle different data types and shapes
        if len(image.shape) > 2:
            if image.shape[0] == 1:
                # For (1, height, width) shape, take first frame
                image = image[0]
            else:
                # For multi-frame images, take first frame
                image = image[0]
        
        # Convert to float for processing
        image = image.astype(float)
        
        # Get rescale slope and intercept
        rescale_slope = float(getattr(ds, 'RescaleSlope', 1.0))
        rescale_intercept = float(getattr(ds, 'RescaleIntercept', 0.0))
        
        # Apply rescale
        image = image * rescale_slope + rescale_intercept
        
        # Apply window/level if provided
        if window_center is not None and window_width is not None:
            window_min = window_center - window_width / 2
            window_max = window_center + window_width / 2
            image = np.clip(image, window_min, window_max)
            image = ((image - window_min) / (window_max - window_min) * 255.0).astype(np.uint8)
        else:
            # Default normalization
            image = ((image - image.min()) / (image.max() - image.min()) * 255.0).astype(np.uint8)
        
        print(f"Processed image shape: {image.shape}, dtype: {image.dtype}")
        print(f"Image min: {image.min()}, max: {image.max()}")
        
        # Convert to PIL Image
        pil_image = Image.fromarray(image)
        
        # Apply rotation if specified
        if rotation != 0:
            pil_image = pil_image.rotate(rotation, expand=True)
        
        # Convert to base64 for display
        buffered = BytesIO()
        pil_image.save(buffered, format="PNG", optimize=True)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Return image data and metadata
        return {
            'image': img_str,
            'metadata': {
                'pixel_spacing': pixel_spacing,
                'image_size': image.shape,
                'window_center': window_center,
                'window_width': window_width,
                'rotation': rotation,
                'rescale_slope': rescale_slope,
                'rescale_intercept': rescale_intercept,
                'min_value': float(image.min()),
                'max_value': float(image.max())
            }
        }
        
    except Exception as e:
        print(f"Error processing DICOM file: {str(e)}")
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
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        try:
            # Check if this is a DICOMDIR file
            ds = pydicom.dcmread(filename)
            is_dicomdir = False
            
            # Check if it's a DICOMDIR by looking for DirectoryRecordSequence
            if hasattr(ds, 'DirectoryRecordSequence'):
                is_dicomdir = True
                # Process DICOMDIR
                base_dir = os.path.dirname(filename)
                file_paths = []
                file_info = []
                
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
                                # Get comprehensive info for each file
                                try:
                                    ds_file = pydicom.dcmread(file_path)
                                    info = {
                                        'path': file_path,
                                        'patient_name': str(getattr(ds_file, 'PatientName', 'N/A')),
                                        'patient_id': str(getattr(ds_file, 'PatientID', 'N/A')),
                                        'study_date': str(getattr(ds_file, 'StudyDate', 'N/A')),
                                        'study_description': str(getattr(ds_file, 'StudyDescription', 'N/A')),
                                        'modality': str(getattr(ds_file, 'Modality', 'N/A')),
                                        'series_number': str(getattr(ds_file, 'SeriesNumber', 'N/A')),
                                        'series_description': str(getattr(ds_file, 'SeriesDescription', 'N/A')),
                                        'series_date': str(getattr(ds_file, 'SeriesDate', 'N/A')),
                                        'series_time': str(getattr(ds_file, 'SeriesTime', 'N/A')),
                                        'protocol_name': str(getattr(ds_file, 'ProtocolName', 'N/A')),
                                        'rows': str(getattr(ds_file, 'Rows', 'N/A')),
                                        'columns': str(getattr(ds_file, 'Columns', 'N/A')),
                                        'image_type': str(getattr(ds_file, 'ImageType', 'N/A')),
                                        'pixel_spacing': str(getattr(ds_file, 'PixelSpacing', 'N/A')),
                                        'window_center': str(getattr(ds_file, 'WindowCenter', 'N/A')),
                                        'window_width': str(getattr(ds_file, 'WindowWidth', 'N/A')),
                                        'body_part': str(getattr(ds_file, 'BodyPartExamined', 'N/A')),
                                        'view_position': str(getattr(ds_file, 'ViewPosition', 'N/A')),
                                        'manufacturer': str(getattr(ds_file, 'Manufacturer', 'N/A')),
                                        'manufacturer_model': str(getattr(ds_file, 'ManufacturerModelName', 'N/A')),
                                        'software_version': str(getattr(ds_file, 'SoftwareVersions', 'N/A')),
                                        'kvp': str(getattr(ds_file, 'KVP', 'N/A')),
                                        'exposure_time': str(getattr(ds_file, 'ExposureTime', 'N/A')),
                                        'xray_tube_current': str(getattr(ds_file, 'XRayTubeCurrent', 'N/A')),
                                        'exposure': str(getattr(ds_file, 'Exposure', 'N/A'))
                                    }
                                    file_info.append(info)
                                except Exception as e:
                                    print(f"Error getting info for {file_path}: {str(e)}")
                
                return jsonify({
                    'success': True,
                    'is_dicomdir': True,
                    'files': file_info
                })
            else:
                # Handle regular DICOM file
                info = get_dicom_info(filename)
                frame = int(request.form.get('frame', 0))
                image_data = dicom_to_image(filename, frame)
                
                # Get total number of frames
                total_frames = 1
                if hasattr(ds, 'NumberOfFrames'):
                    total_frames = ds.NumberOfFrames
                elif len(ds.pixel_array.shape) > 2:
                    total_frames = ds.pixel_array.shape[0]
                
                return jsonify({
                    'success': True,
                    'is_dicomdir': False,
                    'info': info,
                    'image': image_data,
                    'total_frames': total_frames
                })
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/get_image/<int:index>')
def get_image(index):
    try:
        # Get window/level parameters
        window_width = request.args.get('window_width', type=float, default=2000)
        window_center = request.args.get('window_center', type=float, default=1000)
        rotation = request.args.get('rotation', type=float, default=0)
        
        print(f"Requested image {index} with window_width={window_width}, window_center={window_center}, rotation={rotation}")
        
        # Get the list of uploaded files
        uploaded_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*.dcm'))
        if not uploaded_files:
            print("No files found in upload folder")
            return jsonify({'error': 'No files uploaded'}), 404
        
        # Sort files to ensure consistent order
        uploaded_files.sort()
        print(f"Found {len(uploaded_files)} files in upload folder")
        
        if index < 0 or index >= len(uploaded_files):
            print(f"Invalid index {index} for {len(uploaded_files)} files")
            return jsonify({'error': 'Invalid image index'}), 404
        
        # Get the DICOM file
        dicom_file = uploaded_files[index]
        print(f"Processing file: {dicom_file}")
        
        # Process the DICOM file
        try:
            # Get the image data and metadata
            result = get_dicom_image(dicom_file, window_center, window_width, rotation)
            
            # Return the image and metadata
            return jsonify({
                'success': True,
                'image': result['image'],
                'metadata': result['metadata']
            })
        except Exception as e:
            print(f"Error processing DICOM file: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        print(f"Error in get_image route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/info/<int:index>')
def get_info(index):
    try:
        uploaded_files = glob.glob(os.path.join(app.config['UPLOAD_FOLDER'], '*.dcm'))
        if not uploaded_files:
            return jsonify({'error': 'No files uploaded'}), 404
        
        uploaded_files.sort()
        if index < 0 or index >= len(uploaded_files):
            return jsonify({'error': 'Invalid image index'}), 404
        
        ds = pydicom.dcmread(uploaded_files[index])
        info = {}
        
        # Get comprehensive DICOM information
        try:
            # Patient Information
            info['PatientInfo'] = {
                'PatientID': str(getattr(ds, 'PatientID', 'N/A')),
                'PatientName': str(getattr(ds, 'PatientName', 'N/A')),
                'PatientBirthDate': str(getattr(ds, 'PatientBirthDate', 'N/A')),
                'PatientSex': str(getattr(ds, 'PatientSex', 'N/A')),
                'PatientAge': str(getattr(ds, 'PatientAge', 'N/A')),
                'PatientWeight': str(getattr(ds, 'PatientWeight', 'N/A'))
            }
            
            # Study Information
            info['StudyInfo'] = {
                'StudyDate': str(getattr(ds, 'StudyDate', 'N/A')),
                'StudyTime': str(getattr(ds, 'StudyTime', 'N/A')),
                'StudyDescription': str(getattr(ds, 'StudyDescription', 'N/A')),
                'StudyInstanceUID': str(getattr(ds, 'StudyInstanceUID', 'N/A')),
                'StudyID': str(getattr(ds, 'StudyID', 'N/A')),
                'AccessionNumber': str(getattr(ds, 'AccessionNumber', 'N/A')),
                'ReferringPhysicianName': str(getattr(ds, 'ReferringPhysicianName', 'N/A'))
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
                'PixelAspectRatio': str(getattr(ds, 'PixelAspectRatio', 'N/A'))
            }
            
            # Window/Level Information
            info['WindowLevelInfo'] = {
                'WindowCenter': str(getattr(ds, 'WindowCenter', 'N/A')),
                'WindowWidth': str(getattr(ds, 'WindowWidth', 'N/A')),
                'RescaleIntercept': str(getattr(ds, 'RescaleIntercept', 'N/A')),
                'RescaleSlope': str(getattr(ds, 'RescaleSlope', 'N/A')),
                'WindowCenterWidthExplanation': str(getattr(ds, 'WindowCenterWidthExplanation', 'N/A'))
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
                'Exposure': str(getattr(ds, 'Exposure', 'N/A'))
            }
            
            # Add image statistics
            try:
                pixel_array = ds.pixel_array
                info['ImageStatistics'] = {
                    'MinValue': str(float(pixel_array.min())),
                    'MaxValue': str(float(pixel_array.max())),
                    'MeanValue': str(float(pixel_array.mean())),
                    'StdDeviation': str(float(pixel_array.std()))
                }
            except:
                info['ImageStatistics'] = 'Not available'
            
        except Exception as e:
            print(f"Error extracting DICOM info: {str(e)}")
        
        return jsonify(info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/load_dicomdir_file', methods=['POST'])
def load_dicomdir_file():
    if 'dicomdir' not in request.files:
        return jsonify({'error': 'No DICOMDIR file provided'}), 400
    
    file_index = request.form.get('file_index', type=int)
    if file_index is None:
        return jsonify({'error': 'No file index provided'}), 400
    
    dicomdir = request.files['dicomdir']
    filename = os.path.join(app.config['UPLOAD_FOLDER'], dicomdir.filename)
    dicomdir.save(filename)
    
    try:
        # Read the DICOMDIR file
        ds = pydicom.dcmread(filename)
        if not hasattr(ds, 'DirectoryRecordSequence'):
            return jsonify({'error': 'Not a valid DICOMDIR file'}), 400
        
        base_dir = os.path.dirname(filename)
        file_paths = []
        
        # Process each directory record
        for record in ds.DirectoryRecordSequence:
            if record.DirectoryRecordType == "IMAGE":
                ref_file = record.ReferencedFileID
                if ref_file:
                    file_path = os.path.join(base_dir, *ref_file)
                    if os.path.exists(file_path):
                        file_paths.append(file_path)
        
        if file_index < 0 or file_index >= len(file_paths):
            return jsonify({'error': 'Invalid file index'}), 400
        
        # Get the selected file
        selected_file = file_paths[file_index]
        
        # Get DICOM information
        info = get_dicom_info(selected_file)
        
        # Get the requested frame
        frame = int(request.form.get('frame', 0))
        
        # Convert DICOM to image
        image_data = dicom_to_image(selected_file, frame)
        
        # Get total number of frames
        ds = pydicom.dcmread(selected_file)
        total_frames = 1
        if hasattr(ds, 'NumberOfFrames'):
            total_frames = ds.NumberOfFrames
        elif len(ds.pixel_array.shape) > 2:
            total_frames = ds.pixel_array.shape[0]
        
        return jsonify({
            'success': True,
            'info': info,
            'image': image_data,
            'total_frames': total_frames
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True) 