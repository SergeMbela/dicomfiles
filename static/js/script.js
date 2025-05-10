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
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

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
            currentFiles = data.files;
            totalFiles = currentFiles.length;
            currentIndex = 0;
            
            // Update UI
            document.getElementById('imageContainer').style.display = 'block';
            document.getElementById('imageSlider').max = totalFiles - 1;
            document.getElementById('imageSlider').value = 0;
            
            // Load first image
            await updateImage();
            
            // Update DICOM info
            updateDicomInfo(data.dicom_info);
            
            // Show success message
            const successMessage = document.createElement('div');
            successMessage.className = 'alert alert-success alert-dismissible fade show';
            successMessage.innerHTML = `
                Successfully loaded ${totalFiles} image${totalFiles > 1 ? 's' : ''}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.querySelector('.upload-section').appendChild(successMessage);
            
            // Auto-dismiss after 3 seconds
            setTimeout(() => {
                successMessage.remove();
            }, 3000);
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