import os
import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileDataset
from pydicom.sequence import Sequence
from datetime import datetime
import uuid

def create_sample_dicom_file(output_dir, patient_name, study_date, study_description, modality, series_number, image_size=(256, 256)):
    """Create a sample DICOM file with the given parameters."""
    # Create the basic file dataset
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = str(uuid.uuid4())
    file_meta.ImplementationClassUID = '1.2.3.4'

    # Create the dataset
    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    
    # Add the data elements
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.StudyInstanceUID = str(uuid.uuid4())
    ds.SeriesInstanceUID = str(uuid.uuid4())
    
    # Add patient information
    ds.PatientName = patient_name
    ds.PatientID = str(uuid.uuid4())
    ds.PatientBirthDate = '19700101'
    
    # Add study information
    ds.StudyDate = study_date
    ds.StudyTime = datetime.now().strftime('%H%M%S.%f')
    ds.StudyDescription = study_description
    ds.Modality = modality
    ds.SeriesNumber = series_number
    
    # Add image information
    ds.Rows, ds.Columns = image_size
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    
    # Create a simple gradient image
    image = np.linspace(0, 65535, image_size[0] * image_size[1], dtype=np.uint16)
    image = image.reshape(image_size)
    ds.PixelData = image.tobytes()
    
    # Save the file
    filename = f"{patient_name.replace(' ', '_')}_{study_date}_{modality}_{series_number}.dcm"
    filepath = os.path.join(output_dir, filename)
    ds.save_as(filepath)
    return filepath

def create_dicomdir(output_dir, dicom_files):
    """Create a DICOMDIR file from a list of DICOM files."""
    # Create the basic file dataset
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.1.3.10'  # Media Storage Directory Storage
    file_meta.MediaStorageSOPInstanceUID = str(uuid.uuid4())
    file_meta.ImplementationClassUID = '1.2.3.4'

    # Create the dataset
    ds = FileDataset(None, {}, file_meta=file_meta, preamble=b"\0" * 128)
    
    # Add the data elements
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.DirectoryRecordSequence = Sequence()
    
    # Add each DICOM file to the directory
    for filepath in dicom_files:
        dcm = pydicom.dcmread(filepath)
        
        # Create a directory record
        record = Dataset()
        record.DirectoryRecordType = "IMAGE"
        record.ReferencedFileID = os.path.basename(filepath)
        record.ReferencedSOPClassUIDInFile = dcm.SOPClassUID
        record.ReferencedSOPInstanceUIDInFile = dcm.SOPInstanceUID
        
        # Add patient information
        record.PatientName = dcm.PatientName
        record.PatientID = dcm.PatientID
        
        # Add study information
        record.StudyDate = dcm.StudyDate
        record.StudyDescription = dcm.StudyDescription
        record.Modality = dcm.Modality
        record.SeriesNumber = dcm.SeriesNumber
        
        ds.DirectoryRecordSequence.append(record)
    
    # Save the DICOMDIR file
    dicomdir_path = os.path.join(output_dir, 'DICOMDIR')
    ds.save_as(dicomdir_path)
    return dicomdir_path

def main():
    # Create output directory
    output_dir = 'sample_dicom'
    os.makedirs(output_dir, exist_ok=True)
    
    # Create sample DICOM files
    dicom_files = []
    
    # Create CT images
    for i in range(3):
        filepath = create_sample_dicom_file(
            output_dir,
            patient_name='John Doe',
            study_date='20240315',
            study_description='CT Chest',
            modality='CT',
            series_number=i+1
        )
        dicom_files.append(filepath)
    
    # Create MR images
    for i in range(2):
        filepath = create_sample_dicom_file(
            output_dir,
            patient_name='Jane Smith',
            study_date='20240316',
            study_description='MR Brain',
            modality='MR',
            series_number=i+1
        )
        dicom_files.append(filepath)
    
    # Create X-ray images
    for i in range(2):
        filepath = create_sample_dicom_file(
            output_dir,
            patient_name='Bob Wilson',
            study_date='20240317',
            study_description='Chest X-ray',
            modality='DX',
            series_number=i+1
        )
        dicom_files.append(filepath)
    
    # Create DICOMDIR
    dicomdir_path = create_dicomdir(output_dir, dicom_files)
    print(f"Created DICOMDIR at: {dicomdir_path}")
    print(f"Created {len(dicom_files)} sample DICOM files in: {output_dir}")

if __name__ == '__main__':
    main() 