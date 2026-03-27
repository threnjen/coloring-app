/**
 * Main application logic: API calls and step navigation.
 */

const state = {
    imageId: null,
    croppedImageId: null,
    mosaicId: null,
    originalFile: null,
};

const cropManager = new CropManager();

// --- DOM references ---
const fileInput = document.getElementById('file-input');
const uploadError = document.getElementById('upload-error');
const stepUpload = document.getElementById('step-upload');
const stepCrop = document.getElementById('step-crop');
const stepProcess = document.getElementById('step-process');
const stepPreview = document.getElementById('step-preview');
const cropBtn = document.getElementById('crop-btn');
const colorCount = document.getElementById('color-count');
const colorValue = document.getElementById('color-value');
const sizeSelect = document.getElementById('size-select');
const modeRadios = document.querySelectorAll('input[name="mosaic-mode"]');
const processBtn = document.getElementById('process-btn');
const processLoading = document.getElementById('process-loading');
const previewImage = document.getElementById('preview-image');
const paletteDisplay = document.getElementById('palette-display');
const downloadBtn = document.getElementById('download-btn');
const restartBtn = document.getElementById('restart-btn');

// --- Step navigation ---
function showStep(stepEl) {
    [stepUpload, stepCrop, stepProcess, stepPreview].forEach(s => s.hidden = true);
    stepEl.hidden = false;
}

function showError(msg) {
    uploadError.textContent = msg;
    uploadError.hidden = false;
}

function clearError() {
    uploadError.hidden = true;
}

// --- Upload ---
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    clearError();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        if (!res.ok) {
            const err = await res.json();
            showError(err.detail || 'Upload failed');
            return;
        }
        const data = await res.json();
        state.imageId = data.image_id;
        state.originalFile = file;

        // Show crop step with the stored (possibly resized) image
        cropManager.init(`/api/image/${data.image_id}`);
        showStep(stepCrop);
    } catch (err) {
        showError('Upload failed: ' + err.message);
    }
});

// --- Crop ---
cropBtn.addEventListener('click', async () => {
    const cropData = cropManager.getCropData();
    if (!cropData) return;

    cropBtn.disabled = true;
    try {
        const res = await fetch('/api/crop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_id: state.imageId,
                ...cropData,
            }),
        });
        if (!res.ok) {
            const err = await res.json();
            showError(err.detail || 'Crop failed');
            showStep(stepUpload);
            return;
        }
        const data = await res.json();
        state.croppedImageId = data.cropped_image_id;
        cropManager.destroy();
        showStep(stepProcess);
    } catch (err) {
        showError('Crop failed: ' + err.message);
    } finally {
        cropBtn.disabled = false;
    }
});

// --- Color slider ---
colorCount.addEventListener('input', () => {
    colorValue.textContent = colorCount.value;
});

// --- Size labels per mode ---
const SIZE_LABELS = {
    square:  { 3: '3mm (60×80)',  4: '4mm (50×65)',  5: '5mm (40×52)' },
    circle:  { 3: '3mm (60×80)',  4: '4mm (50×65)',  5: '5mm (40×52)' },
    hexagon: { 3: '3mm (60×93)',  4: '4mm (45×70)',  5: '5mm (36×56)' },
};

function updateSizeLabels() {
    const mode = document.querySelector('input[name="mosaic-mode"]:checked').value;
    const labels = SIZE_LABELS[mode];
    for (const option of sizeSelect.options) {
        const size = parseInt(option.value, 10);
        if (labels[size]) {
            option.textContent = labels[size];
        }
    }
}

modeRadios.forEach(radio => radio.addEventListener('change', updateSizeLabels));

// --- Process ---
processBtn.addEventListener('click', async () => {
    processBtn.disabled = true;
    processLoading.hidden = false;

    try {
        const res = await fetch('/api/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cropped_image_id: state.croppedImageId,
                num_colors: parseInt(colorCount.value, 10),
                size: parseInt(sizeSelect.value, 10),
                mode: document.querySelector('input[name="mosaic-mode"]:checked').value,
            }),
        });
        if (!res.ok) {
            const err = await res.json();
            showError(err.detail || 'Processing failed');
            showStep(stepUpload);
            return;
        }
        const data = await res.json();
        state.mosaicId = data.mosaic_id;

        // Display preview
        previewImage.src = `/api/preview/${data.mosaic_id}`;

        // Display palette
        paletteDisplay.innerHTML = '';
        for (const c of data.palette) {
            const swatch = document.createElement('div');
            swatch.className = 'palette-swatch';
            swatch.innerHTML = `
                <span class="swatch" style="background:${c.hex}"></span>
                <span>${c.label}</span>
            `;
            paletteDisplay.appendChild(swatch);
        }

        showStep(stepPreview);
    } catch (err) {
        showError('Processing failed: ' + err.message);
    } finally {
        processBtn.disabled = false;
        processLoading.hidden = true;
    }
});

// --- Download PDF ---
downloadBtn.addEventListener('click', () => {
    if (state.mosaicId) {
        window.location.href = `/api/pdf/${state.mosaicId}`;
    }
});

// --- Restart ---
restartBtn.addEventListener('click', () => {
    state.imageId = null;
    state.croppedImageId = null;
    state.mosaicId = null;
    state.originalFile = null;
    fileInput.value = '';
    clearError();
    showStep(stepUpload);
});
