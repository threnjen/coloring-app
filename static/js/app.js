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
const toggleOriginal = document.getElementById('toggle-original');

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
        toggleOriginal.checked = false;

        // Display palette (interactive)
        paletteDisplay.innerHTML = '';
        const warningArea = document.getElementById('palette-warnings');
        if (warningArea) warningArea.textContent = '';
        data.palette.forEach((c, idx) => {
            const swatch = document.createElement('div');
            swatch.className = 'palette-swatch palette-swatch--editable';

            const colorInput = document.createElement('input');
            colorInput.type = 'color';
            colorInput.value = c.hex;
            colorInput.className = 'palette-color-input';
            colorInput.dataset.confirmed = c.hex;

            const swatchSpan = document.createElement('span');
            swatchSpan.className = 'swatch';
            swatchSpan.style.background = c.hex;

            const labelSpan = document.createElement('span');
            labelSpan.textContent = c.label;

            swatch.appendChild(colorInput);
            swatch.appendChild(swatchSpan);
            swatch.appendChild(labelSpan);

            // Click swatch to open picker
            swatchSpan.addEventListener('click', () => colorInput.click());

            // Debounced color change
            let debounceTimer = null;
            colorInput.addEventListener('input', () => {
                swatchSpan.style.background = colorInput.value;
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    _editPaletteColor(data.mosaic_id, idx, colorInput.value);
                }, 500);
            });
            colorInput.addEventListener('change', () => {
                clearTimeout(debounceTimer);
                _editPaletteColor(data.mosaic_id, idx, colorInput.value);
            });

            paletteDisplay.appendChild(swatch);
        });

        showStep(stepPreview);
    } catch (err) {
        showError('Processing failed: ' + err.message);
    } finally {
        processBtn.disabled = false;
        processLoading.hidden = true;
    }
});

// --- Before/after toggle ---
toggleOriginal.addEventListener('change', () => {
    if (!state.mosaicId) return;
    previewImage.src = toggleOriginal.checked
        ? `/api/preview/${state.mosaicId}/original`
        : `/api/preview/${state.mosaicId}`;
});

// --- Palette edit ---
async function _editPaletteColor(mosaicId, colorIndex, hexColor) {
    // Find the swatch elements for this index so we can revert on failure
    const swatches = paletteDisplay.querySelectorAll('.palette-swatch--editable');
    const swatchEl = swatches[colorIndex];
    const swatchSpan = swatchEl ? swatchEl.querySelector('.swatch') : null;
    const colorInput = swatchEl ? swatchEl.querySelector('.palette-color-input') : null;
    const previousColor = colorInput ? colorInput.dataset.confirmed || colorInput.value : hexColor;

    try {
        const res = await fetch('/api/palette/edit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mosaic_id: mosaicId,
                color_index: colorIndex,
                new_color: hexColor,
            }),
        });
        if (!res.ok) {
            // Revert optimistic UI update
            if (swatchSpan) swatchSpan.style.background = previousColor;
            if (colorInput) colorInput.value = previousColor;
            return;
        }
        const data = await res.json();

        // Store confirmed color for future rollback
        if (colorInput) colorInput.dataset.confirmed = hexColor;

        // Refresh preview with cache-bust
        previewImage.src = `/api/preview/${mosaicId}?t=${Date.now()}`;

        // Show warnings
        const warningArea = document.getElementById('palette-warnings');
        if (warningArea) {
            warningArea.textContent = data.warnings.length > 0
                ? data.warnings.join(' | ')
                : '';
        }
    } catch (err) {
        // Revert optimistic UI update on network error
        if (swatchSpan) swatchSpan.style.background = previousColor;
        if (colorInput) colorInput.value = previousColor;
    }
}

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
    toggleOriginal.checked = false;
    clearError();
    showStep(stepUpload);
});
