/**
 * Image editor: cutout, background selection, position/scale, compositing.
 * State machine: idle → cutting → cut → compositing → composited
 */

class EditorManager {
    constructor() {
        this.state = 'idle';
        this.cutoutImageId = null;
        this.compositeImageId = null;
        this.croppedImageId = null;
        this.selectedBgId = null;
        this.customBgFile = null;
        this.subjectX = 0;
        this.subjectY = 0;
        this.scale = 1.0;
        this._backgrounds = [];

        // Drag state
        this._dragging = false;
        this._dragStartX = 0;
        this._dragStartY = 0;
        this._dragOffsetX = 0;
        this._dragOffsetY = 0;
    }

    /** Initialize the editor for a cropped image. */
    init(croppedImageId) {
        this.reset();
        this.croppedImageId = croppedImageId;

        // Show crop preview
        const cropImg = document.getElementById('editor-crop-img');
        cropImg.src = `/api/image/${croppedImageId}`;
        document.getElementById('editor-crop-preview').hidden = false;
        document.getElementById('editor-checkerboard').hidden = true;
        document.getElementById('editor-composite-preview').hidden = true;

        this._bindEvents();
        this._setState('idle');
    }

    /** Reset all editor state. */
    reset() {
        this.state = 'idle';
        this.cutoutImageId = null;
        this.compositeImageId = null;
        this.croppedImageId = null;
        this.selectedBgId = null;
        this.customBgFile = null;
        this.subjectX = 0;
        this.subjectY = 0;
        this.scale = 1.0;
        this._backgrounds = [];
        this._dragging = false;

        document.getElementById('editor-bg-controls').hidden = true;
        document.getElementById('editor-undo-controls').hidden = true;
        document.getElementById('undo-cutout-btn').hidden = true;
        document.getElementById('continue-edit-btn').hidden = true;
        document.getElementById('editor-error').hidden = true;
        document.getElementById('cutout-loading').hidden = true;
        document.getElementById('cutout-btn').disabled = false;
        document.getElementById('cutout-btn').hidden = false;
        document.getElementById('skip-edit-btn').hidden = false;

        const scaleSlider = document.getElementById('scale-slider');
        scaleSlider.value = '1.0';
        document.getElementById('scale-value').textContent = '1.00';

        document.getElementById('bg-thumbnails').innerHTML = '';
    }

    /** Get the image ID to pass to the process step. */
    getImageIdForProcess() {
        if (this.compositeImageId) return this.compositeImageId;
        return this.croppedImageId;
    }

    // --- Internal state machine ---

    _setState(newState) {
        this.state = newState;
        const cutoutBtn = document.getElementById('cutout-btn');
        const bgControls = document.getElementById('editor-bg-controls');
        const undoControls = document.getElementById('editor-undo-controls');
        const undoCutoutBtn = document.getElementById('undo-cutout-btn');
        const continueBtn = document.getElementById('continue-edit-btn');
        const skipBtn = document.getElementById('skip-edit-btn');
        const cropPreview = document.getElementById('editor-crop-preview');
        const checkerboard = document.getElementById('editor-checkerboard');
        const compositePreview = document.getElementById('editor-composite-preview');

        switch (newState) {
            case 'idle':
                cutoutBtn.hidden = false;
                cutoutBtn.disabled = false;
                bgControls.hidden = true;
                undoControls.hidden = true;
                undoCutoutBtn.hidden = true;
                continueBtn.hidden = true;
                skipBtn.hidden = false;
                cropPreview.hidden = false;
                checkerboard.hidden = true;
                compositePreview.hidden = true;
                break;

            case 'cutting':
                cutoutBtn.disabled = true;
                document.getElementById('cutout-loading').hidden = false;
                break;

            case 'cut':
                cutoutBtn.hidden = true;
                document.getElementById('cutout-loading').hidden = true;
                bgControls.hidden = false;
                undoControls.hidden = true;
                undoCutoutBtn.hidden = false;
                continueBtn.hidden = true;
                skipBtn.hidden = false;
                cropPreview.hidden = true;
                checkerboard.hidden = false;
                compositePreview.hidden = true;
                this._loadBackgrounds();
                break;

            case 'composited':
                bgControls.hidden = true;
                undoControls.hidden = false;
                undoCutoutBtn.hidden = false;
                continueBtn.hidden = false;
                skipBtn.hidden = true;
                cropPreview.hidden = true;
                checkerboard.hidden = true;
                compositePreview.hidden = false;
                break;
        }
    }

    _showError(msg) {
        const el = document.getElementById('editor-error');
        el.textContent = msg;
        el.hidden = false;
    }

    _clearError() {
        document.getElementById('editor-error').hidden = true;
    }

    _bindEvents() {
        // Cutout button
        const cutoutBtn = document.getElementById('cutout-btn');
        cutoutBtn.onclick = () => this._doCutout();

        // Background file upload
        const bgInput = document.getElementById('bg-file-input');
        bgInput.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                this.customBgFile = file;
                this.selectedBgId = null;
                // Deselect preset thumbnails
                document.querySelectorAll('.bg-thumb').forEach(t => t.classList.remove('selected'));
            }
        };

        // Scale slider
        const scaleSlider = document.getElementById('scale-slider');
        scaleSlider.oninput = () => {
            this.scale = parseFloat(scaleSlider.value);
            document.getElementById('scale-value').textContent = this.scale.toFixed(2);
        };

        // Apply composite
        document.getElementById('apply-composite-btn').onclick = () => this._doComposite();

        // Undo composite
        document.getElementById('undo-composite-btn').onclick = () => this._undoComposite();

        // Undo cutout
        document.getElementById('undo-cutout-btn').onclick = () => this._undoCutout();

        // Skip
        document.getElementById('skip-edit-btn').onclick = () => this._skip();

        // Continue
        document.getElementById('continue-edit-btn').onclick = () => this._continue();

        // Drag to position
        this._setupDrag();
    }

    _setupDrag() {
        const checkerboard = document.getElementById('editor-checkerboard');
        const cutoutImg = document.getElementById('editor-cutout-img');

        checkerboard.addEventListener('pointerdown', (e) => {
            if (this.state !== 'cut') return;
            this._dragging = true;
            this._dragStartX = e.clientX;
            this._dragStartY = e.clientY;
            this._dragOffsetX = this.subjectX;
            this._dragOffsetY = this.subjectY;
            checkerboard.setPointerCapture(e.pointerId);
            e.preventDefault();
        });

        checkerboard.addEventListener('pointermove', (e) => {
            if (!this._dragging) return;
            const dx = e.clientX - this._dragStartX;
            const dy = e.clientY - this._dragStartY;
            this.subjectX = this._dragOffsetX + dx;
            this.subjectY = this._dragOffsetY + dy;
            cutoutImg.style.transform = `translate(${this.subjectX}px, ${this.subjectY}px)`;
            e.preventDefault();
        });

        checkerboard.addEventListener('pointerup', (e) => {
            this._dragging = false;
            e.preventDefault();
        });

        checkerboard.addEventListener('pointercancel', () => {
            this._dragging = false;
        });
    }

    async _doCutout() {
        this._clearError();
        this._setState('cutting');

        try {
            const res = await fetch('/api/cutout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_id: this.croppedImageId }),
            });
            if (!res.ok) {
                const err = await res.json();
                this._showError(err.detail || 'Cutout failed');
                this._setState('idle');
                return;
            }
            const data = await res.json();
            this.cutoutImageId = data.cutout_image_id;

            const cutoutImg = document.getElementById('editor-cutout-img');
            cutoutImg.src = `/api/cutout/${data.cutout_image_id}/image`;
            cutoutImg.style.transform = 'translate(0px, 0px)';
            this.subjectX = 0;
            this.subjectY = 0;

            this._setState('cut');
        } catch (err) {
            this._showError('Cutout failed: ' + err.message);
            this._setState('idle');
        }
    }

    async _loadBackgrounds() {
        try {
            const res = await fetch('/api/backgrounds');
            if (!res.ok) return;
            const data = await res.json();
            this._backgrounds = data.backgrounds;
            this._renderBackgroundThumbnails();
        } catch (_) { /* ignore */ }
    }

    _renderBackgroundThumbnails() {
        const container = document.getElementById('bg-thumbnails');
        container.innerHTML = '';

        for (const bg of this._backgrounds) {
            const thumb = document.createElement('button');
            thumb.className = 'bg-thumb';
            thumb.title = bg.name;
            thumb.dataset.bgId = bg.id;

            // Simple color preview for programmatic backgrounds
            if (bg.type === 'programmatic') {
                thumb.style.background = bg.id.includes('gradient')
                    ? 'linear-gradient(to bottom, #aaa, #fff)'
                    : '';
            }
            thumb.textContent = bg.name;

            thumb.addEventListener('click', () => {
                document.querySelectorAll('.bg-thumb').forEach(t => t.classList.remove('selected'));
                thumb.classList.add('selected');
                this.selectedBgId = bg.id;
                this.customBgFile = null;
                document.getElementById('bg-file-input').value = '';
            });

            container.appendChild(thumb);
        }
    }

    async _doComposite() {
        this._clearError();

        if (!this.selectedBgId && !this.customBgFile) {
            this._showError('Please select a background first.');
            return;
        }

        const applyBtn = document.getElementById('apply-composite-btn');
        applyBtn.disabled = true;

        try {
            let res;
            if (this.customBgFile) {
                const formData = new FormData();
                formData.append('cutout_image_id', this.cutoutImageId);
                formData.append('x', String(this.subjectX));
                formData.append('y', String(this.subjectY));
                formData.append('scale', String(this.scale));
                formData.append('background_file', this.customBgFile);
                res = await fetch('/api/composite', { method: 'POST', body: formData });
            } else {
                res = await fetch('/api/composite', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        cutout_image_id: this.cutoutImageId,
                        background_id: this.selectedBgId,
                        x: this.subjectX,
                        y: this.subjectY,
                        scale: this.scale,
                    }),
                });
            }

            if (!res.ok) {
                const err = await res.json();
                this._showError(err.detail || 'Composite failed');
                return;
            }

            const data = await res.json();
            this.compositeImageId = data.composite_image_id;

            const compositeImg = document.getElementById('editor-composite-img');
            compositeImg.src = `/api/image/${data.composite_image_id}`;

            this._setState('composited');
        } catch (err) {
            this._showError('Composite failed: ' + err.message);
        } finally {
            applyBtn.disabled = false;
        }
    }

    _undoComposite() {
        this.compositeImageId = null;
        this._setState('cut');
    }

    _undoCutout() {
        this.cutoutImageId = null;
        this.compositeImageId = null;
        this.subjectX = 0;
        this.subjectY = 0;
        this.scale = 1.0;
        document.getElementById('scale-slider').value = '1.0';
        document.getElementById('scale-value').textContent = '1.00';
        document.getElementById('editor-cutout-img').style.transform = '';
        this._setState('idle');
    }

    _skip() {
        // Proceed with cropped image directly
        if (typeof window._editorContinueCallback === 'function') {
            window._editorContinueCallback(this.croppedImageId);
        }
    }

    _continue() {
        const imageId = this.getImageIdForProcess();
        if (typeof window._editorContinueCallback === 'function') {
            window._editorContinueCallback(imageId);
        }
    }
}
