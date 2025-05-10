let currentFiles = [];
let currentIndex = 0;
let totalFiles = 0;
let currentRotation = 0;
let currentZoom = 1;
let currentWindowWidth = 2000;
let currentWindowCenter = 1000;
let isLoading = false;

// Window/Level presets for different modalities
const WINDOW_PRESETS = {
    lung: { width: 1500, center: -600 },
    brain: { width: 80, center: 40 },
    bone: { width: 1500, center: 400 },
    abdomen: { width: 400, center: 40 }
};

// Initialize controls
document.addEventListener('DOMContentLoaded', function() {
    // Initialize window/level controls
    document.getElementById('windowWidth').addEventListener('input', updateWindowLevel);
    document.getElementById('windowCenter').addEventListener('input', updateWindowLevel);
    document.getElementById('imageSlider').addEventListener('input', handleSliderChange);
    
    // Initialize keyboard shortcuts
    document.addEventListener('keydown', handleKeyboardShortcuts);
});

function handleKeyboardShortcuts(e) {
    if (isLoading) return;
    
    switch(e.key) {
        case 'ArrowLeft':
            previousImage();
            break;
        case 'ArrowRight':
            nextImage();
            break;
        case '+':
            zoomIn();
            break;
        case '-':
            zoomOut();
            break;
        case 'r':
            resetZoom();
            break;
        case '[':
            rotateLeft();
            break;
        case ']':
            rotateRight();
            break;
    }
}

function showLoading(show) {
    isLoading = show;
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
    }
}

function handleSliderChange(e) {
    const newIndex = parseInt(e.target.value);
    if (newIndex !== currentIndex) {
        currentIndex = newIndex;
        updateImage();
        updateImageCounter();
    }
}

function updateImageCounter() {
    document.getElementById('imageCounter').textContent = `Image ${currentIndex + 1} of ${totalFiles}`;
    document.getElementById('imageSlider').value = currentIndex;
}

function previousImage() {
    if (currentIndex > 0 && !isLoading) {
        currentIndex--;
        updateImage();
        updateImageCounter();
    }
}

function nextImage() {
    if (currentIndex < totalFiles - 1 && !isLoading) {
        currentIndex++;
        updateImage();
        updateImageCounter();
    }
}

function applyPreset(presetName) {
    if (presetName in WINDOW_PRESETS && !isLoading) {
        const preset = WINDOW_PRESETS[presetName];
        currentWindowWidth = preset.width;
        currentWindowCenter = preset.center;
        document.getElementById('windowWidth').value = preset.width;
        document.getElementById('windowCenter').value = preset.center;
        document.getElementById('windowWidthValue').textContent = preset.width;
        document.getElementById('windowCenterValue').textContent = preset.center;
        updateImage();
    }
}

function resetWindowLevel() {
    if (isLoading) return;
    currentWindowWidth = 2000;
    currentWindowCenter = 1000;
    document.getElementById('windowWidth').value = currentWindowWidth;
    document.getElementById('windowCenter').value = currentWindowCenter;
    document.getElementById('windowWidthValue').textContent = currentWindowWidth;
    document.getElementById('windowCenterValue').textContent = currentWindowCenter;
    updateImage();
}

function updateWindowLevel() {
    if (isLoading) return;
    currentWindowWidth = parseInt(document.getElementById('windowWidth').value);
    currentWindowCenter = parseInt(document.getElementById('windowCenter').value);
    document.getElementById('windowWidthValue').textContent = currentWindowWidth;
    document.getElementById('windowCenterValue').textContent = currentWindowCenter;
    updateImage();
}

function rotateLeft() {
    if (isLoading) return;
    currentRotation = (currentRotation - 90) % 360;
    updateImageTransform();
}

function rotateRight() {
    if (isLoading) return;
    currentRotation = (currentRotation + 90) % 360;
    updateImageTransform();
}

async function updateImage() {
    if (currentFiles.length === 0 || isLoading) return;
    
    showLoading(true);
    
    try {
        const response = await fetch(`/get_image/${currentIndex}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                window_width: currentWindowWidth,
                window_center: currentWindowCenter,
                rotation: currentRotation
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to load image');
        }
        
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        const dicomImage = document.getElementById('dicomImage');
        dicomImage.onload = () => {
            updateImageTransform();
            showLoading(false);
        };
        dicomImage.src = imageUrl;
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error updating image: ' + error.message);
        showLoading(false);
    }
}

function updateImageTransform() {
    const image = document.getElementById('dicomImage');
    image.style.transform = `scale(${currentZoom}) rotate(${currentRotation}deg)`;
}

function zoomIn() {
    if (isLoading) return;
    currentZoom *= 1.2;
    updateImageTransform();
}

function zoomOut() {
    if (isLoading) return;
    currentZoom /= 1.2;
    updateImageTransform();
}

function resetZoom() {
    if (isLoading) return;
    currentZoom = 1;
    updateImageTransform();
}

document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    if (isLoading) return;
    
    const fileInput = document.getElementById('dicomFile');
    const files = fileInput.files;
    
    if (files.length === 0) {
        alert('Please select at least one DICOM file');
        return;
    }

    showLoading(true);
    
    const formData = new FormData();
    formData.append('file', files[0]);  // Send one file at a time

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();
        if (data.success) {
            if (data.is_dicomdir) {
                // Handle DICOMDIR
                currentFiles = data.files;
                totalFiles = currentFiles.length;
                currentIndex = 0;
                
                // Update UI for DICOMDIR
                document.getElementById('imageContainer').style.display = 'block';
                document.getElementById('fileList').style.display = 'block';
                document.getElementById('imageSlider').max = totalFiles - 1;
                document.getElementById('imageSlider').value = 0;
                
                // Display file list
                const fileList = document.getElementById('fileList');
                fileList.innerHTML = '<h4>DICOMDIR Contents</h4>';
                const list = document.createElement('ul');
                list.className = 'list-group';
                
                currentFiles.forEach((file, index) => {
                    const item = document.createElement('li');
                    item.className = 'list-group-item';
                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${file.info.PatientName || 'Unknown'}</strong>
                                <br>
                                <small>${file.info.Modality || 'Unknown'} - ${file.info.StudyDate || 'Unknown'}</small>
                            </div>
                            <button class="btn btn-primary btn-sm" onclick="loadDicomDirFile(${index})">View</button>
                        </div>
                    `;
                    list.appendChild(item);
                });
                
                fileList.appendChild(list);
                
                // Show success message
                const successMessage = document.createElement('div');
                successMessage.className = 'alert alert-success alert-dismissible fade show';
                successMessage.innerHTML = `
                    Successfully loaded DICOMDIR with ${totalFiles} images
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.querySelector('.upload-section').appendChild(successMessage);
                
                // Auto-dismiss after 3 seconds
                setTimeout(() => {
                    successMessage.remove();
                }, 3000);
            } else {
                // Handle single DICOM file
                currentFiles = [data];
                totalFiles = 1;
                currentIndex = 0;
                
                // Update UI
                document.getElementById('imageContainer').style.display = 'block';
                document.getElementById('fileList').style.display = 'none';
                document.getElementById('imageSlider').max = 0;
                document.getElementById('imageSlider').value = 0;
                
                // Load first image
                await updateImage();
                
                // Update DICOM info
                updateDicomInfo(data.info);
                
                // Show success message
                const successMessage = document.createElement('div');
                successMessage.className = 'alert alert-success alert-dismissible fade show';
                successMessage.innerHTML = `
                    Successfully loaded DICOM file
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.querySelector('.upload-section').appendChild(successMessage);
                
                // Auto-dismiss after 3 seconds
                setTimeout(() => {
                    successMessage.remove();
                }, 3000);
            }
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error uploading files: ' + error.message);
    } finally {
        showLoading(false);
    }
});

async function loadDicomDirFile(index) {
    if (isLoading) return;
    showLoading(true);
    
    const formData = new FormData();
    formData.append('dicomdir', currentFiles[0].path);
    formData.append('file_index', index);
    
    try {
        const response = await fetch('/load_dicomdir_file', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Failed to load file');
        }
        
        const data = await response.json();
        if (data.success) {
            currentIndex = index;
            document.getElementById('imageSlider').value = index;
            await updateImage();
            updateDicomInfo(data.info);
        } else {
            throw new Error(data.error || 'Failed to load file');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error loading file: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function updateDicomInfo(info) {
    const dicomInfo = document.getElementById('dicomInfo');
    if (!info || Object.keys(info).length === 0) {
        dicomInfo.innerHTML = '<p class="text-muted">No DICOM information available</p>';
        return;
    }

    let html = '<table class="table table-sm">';
    for (const [key, value] of Object.entries(info)) {
        html += `<tr><th>${key}</th><td>${value}</td></tr>`;
    }
    html += '</table>';
    dicomInfo.innerHTML = html;
}

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const dicomFile = document.getElementById('dicomFile');
const dicomInfo = document.getElementById('dicomInfo');
const imageContainer = document.getElementById('imageContainer');
const fileList = document.getElementById('fileList');
const dicomImage = document.getElementById('dicomImage');
const windowWidth = document.getElementById('windowWidth');
const windowCenter = document.getElementById('windowCenter');
const windowWidthValue = document.getElementById('windowWidthValue');
const windowCenterValue = document.getElementById('windowCenterValue');
const imageSlider = document.getElementById('imageSlider');
const imageCounter = document.getElementById('imageCounter');
const loadingOverlay = document.getElementById('loadingOverlay');
const prevFrameBtn = document.getElementById('prevFrame');
const nextFrameBtn = document.getElementById('nextFrame');
const playPauseBtn = document.getElementById('playPause');
const frameRateSelect = document.getElementById('frameRate');

// State variables
let currentFrame = 0;
let totalFrames = 1;
let currentFile = null;
let currentDicomDir = null;
let dicomDirFiles = [];
let currentRotation = 0;
let currentZoom = 1;
let isPlaying = false;
let playInterval = null;
let currentFrameRate = 1000; // Default to 1 fps

// Event Listeners
uploadForm.addEventListener('submit', (e) => {
    e.preventDefault();
    if (dicomFile.files.length > 0) {
        handleFile(dicomFile.files[0]);
    }
});

windowWidth.addEventListener('input', () => {
    windowWidthValue.textContent = windowWidth.value;
    updateImage();
});

windowCenter.addEventListener('input', () => {
    windowCenterValue.textContent = windowCenter.value;
    updateImage();
});

imageSlider.addEventListener('input', () => {
    currentFrame = parseInt(imageSlider.value);
    updateImage();
});

// Frame navigation
prevFrameBtn.addEventListener('click', () => {
    if (currentFrame > 0) {
        currentFrame--;
        updateFrame();
    }
});

nextFrameBtn.addEventListener('click', () => {
    if (currentFrame < totalFrames - 1) {
        currentFrame++;
        updateFrame();
    }
});

// Play/Pause functionality
playPauseBtn.addEventListener('click', () => {
    isPlaying = !isPlaying;
    if (isPlaying) {
        playPauseBtn.innerHTML = '<i class="bi bi-pause-fill"></i>';
        playPauseBtn.classList.add('active');
        startPlayback();
    } else {
        playPauseBtn.innerHTML = '<i class="bi bi-play-fill"></i>';
        playPauseBtn.classList.remove('active');
        stopPlayback();
    }
});

// Frame rate control
frameRateSelect.addEventListener('change', () => {
    currentFrameRate = parseInt(frameRateSelect.value);
    if (isPlaying) {
        stopPlayback();
        startPlayback();
    }
});

function startPlayback() {
    stopPlayback(); // Clear any existing interval
    playInterval = setInterval(() => {
        if (currentFrame < totalFrames - 1) {
            currentFrame++;
        } else {
            currentFrame = 0; // Loop back to start
        }
        updateFrame();
    }, currentFrameRate);
}

function stopPlayback() {
    if (playInterval) {
        clearInterval(playInterval);
        playInterval = null;
    }
}

function updateFrame() {
    if (!currentFile) return;

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('frame', currentFrame);

    showLoading(true);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.error) {
                displayError(data.error);
            } else {
                // Display image
                imageContainer.innerHTML = `<img src="data:image/png;base64,${data.image}" class="dicom-image" alt="DICOM Image">`;
                frameControls.style.display = 'flex';
                imageCounter.textContent = `Frame ${currentFrame + 1} of ${totalFrames}`;
                
                // Update slider
                imageSlider.value = currentFrame;
                
                // Update button states
                prevFrameBtn.disabled = currentFrame === 0;
                nextFrameBtn.disabled = currentFrame === totalFrames - 1;
            }
        } else {
            throw new Error(data.error || 'Failed to process DICOM file');
        }
    })
    .catch(error => {
        displayError(error.message);
    })
    .finally(() => {
        showLoading(false);
    });
}

function displayDicomDirContents(files) {
    // Group files by study
    const studies = {};
    files.forEach(file => {
        const studyKey = `${file.study_date}_${file.study_description}`;
        if (!studies[studyKey]) {
            studies[studyKey] = {
                date: file.study_date,
                description: file.study_description,
                patientName: file.patient_name,
                patientId: file.patient_id,
                patientBirthDate: file.patient_birth_date,
                patientSex: file.patient_sex,
                accessionNumber: file.accession_number,
                referringPhysician: file.referring_physician_name,
                files: []
            };
        }
        studies[studyKey].files.push(file);
    });

    // Create accordion for each study
    let html = '<div class="accordion" id="studiesAccordion">';
    Object.entries(studies).forEach(([key, study], index) => {
        const accordionId = `study${index}`;
        html += `
            <div class="accordion-item">
                <h2 class="accordion-header" id="heading${accordionId}">
                    <button class="accordion-button ${index === 0 ? '' : 'collapsed'}" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#collapse${accordionId}">
                        <div class="w-100">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${study.patientName}</strong>
                                    <br>
                                    <small>ID: ${study.patientId} | DOB: ${study.patientBirthDate || 'N/A'} | Sex: ${study.patientSex || 'N/A'}</small>
                                </div>
                                <div class="text-end">
                                    <div>${study.description}</div>
                                    <small>Date: ${study.date} | Accession: ${study.accessionNumber || 'N/A'}</small>
                                </div>
                            </div>
                        </div>
                    </button>
                </h2>
                <div id="collapse${accordionId}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}"
                     data-bs-parent="#studiesAccordion">
                    <div class="accordion-body">
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <h6>Patient Information</h6>
                                <table class="table table-sm">
                                    <tr>
                                        <th>Name:</th>
                                        <td>${study.patientName}</td>
                                    </tr>
                                    <tr>
                                        <th>ID:</th>
                                        <td>${study.patientId}</td>
                                    </tr>
                                    <tr>
                                        <th>Birth Date:</th>
                                        <td>${study.patientBirthDate || 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Sex:</th>
                                        <td>${study.patientSex || 'N/A'}</td>
                                    </tr>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <h6>Study Information</h6>
                                <table class="table table-sm">
                                    <tr>
                                        <th>Study Date:</th>
                                        <td>${study.date}</td>
                                    </tr>
                                    <tr>
                                        <th>Description:</th>
                                        <td>${study.description}</td>
                                    </tr>
                                    <tr>
                                        <th>Accession Number:</th>
                                        <td>${study.accessionNumber || 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Referring Physician:</th>
                                        <td>${study.referringPhysician || 'N/A'}</td>
                                    </tr>
                                </table>
                            </div>
                        </div>

                        <div class="table-responsive">
                            <table class="table table-sm table-hover">
                                <thead class="table-light">
                                    <tr>
                                        <th>Modality</th>
                                        <th>Series</th>
                                        <th>Description</th>
                                        <th>Date/Time</th>
                                        <th>Size</th>
                                        <th>Body Part</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
        `;

        study.files.forEach((file, fileIndex) => {
            const imageSize = file.rows && file.columns ? 
                `${file.rows}x${file.columns}` : 'N/A';
            
            html += `
                <tr>
                    <td>
                        <span class="badge bg-primary">${file.modality || 'N/A'}</span>
                    </td>
                    <td>${file.series_number || 'N/A'}</td>
                    <td>
                        <div>${file.series_description || 'N/A'}</div>
                        <small class="text-muted">${file.protocol_name || ''}</small>
                    </td>
                    <td>
                        <div>${file.series_date || 'N/A'}</div>
                        <small class="text-muted">${file.series_time || ''}</small>
                    </td>
                    <td>${imageSize}</td>
                    <td>${file.body_part || 'N/A'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="loadDicomDirFile(${fileIndex})">
                            <i class="bi bi-eye"></i> View
                        </button>
                    </td>
                </tr>
            `;
        });

        html += `
                                </tbody>
                            </table>
                        </div>

                        <div class="row mt-4">
                            <div class="col-md-6">
                                <h6>Technical Information</h6>
                                <table class="table table-sm">
                                    <tr>
                                        <th>Manufacturer:</th>
                                        <td>${study.files[0].manufacturer || 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Model:</th>
                                        <td>${study.files[0].manufacturer_model || 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Software Version:</th>
                                        <td>${study.files[0].software_version || 'N/A'}</td>
                                    </tr>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <h6>Acquisition Parameters</h6>
                                <table class="table table-sm">
                                    <tr>
                                        <th>KVP:</th>
                                        <td>${study.files[0].kvp || 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Exposure Time:</th>
                                        <td>${study.files[0].exposure_time || 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Tube Current:</th>
                                        <td>${study.files[0].xray_tube_current || 'N/A'}</td>
                                    </tr>
                                </table>
                            </div>
                        </div>

                        <div class="mt-3">
                            <h6>Study Summary</h6>
                            <div class="row">
                                <div class="col-md-6">
                                    <table class="table table-sm">
                                        <tr>
                                            <th>Total Images:</th>
                                            <td>${study.files.length}</td>
                                        </tr>
                                        <tr>
                                            <th>Modalities:</th>
                                            <td>${[...new Set(study.files.map(f => f.modality))].join(', ')}</td>
                                        </tr>
                                    </table>
                                </div>
                                <div class="col-md-6">
                                    <table class="table table-sm">
                                        <tr>
                                            <th>Body Parts:</th>
                                            <td>${[...new Set(study.files.map(f => f.body_part))].filter(Boolean).join(', ') || 'N/A'}</td>
                                        </tr>
                                        <tr>
                                            <th>View Positions:</th>
                                            <td>${[...new Set(study.files.map(f => f.view_position))].filter(Boolean).join(', ') || 'N/A'}</td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';

    // Update the UI
    fileList.innerHTML = html;
    fileList.style.display = 'block';
    imageContainer.style.display = 'none';

    // Show success message
    const successMessage = document.createElement('div');
    successMessage.className = 'alert alert-success alert-dismissible fade show mt-3';
    successMessage.innerHTML = `
        Successfully loaded DICOMDIR with ${files.length} images
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    fileList.parentElement.insertBefore(successMessage, fileList);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        successMessage.remove();
    }, 5000);
} 