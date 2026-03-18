/**
 * Cropper.js integration for image cropping.
 */

class CropManager {
    constructor() {
        this._cropper = null;
        this._imageEl = document.getElementById('crop-image');
    }

    /**
     * Initialize the cropper on the given image URL.
     * @param {string} imageUrl - Object URL or data URL of the uploaded image.
     */
    init(imageUrl) {
        this.destroy();
        this._imageEl.src = imageUrl;
        this._cropper = new Cropper(this._imageEl, {
            viewMode: 1,
            aspectRatio: 60 / 80,
            autoCropArea: 0.8,
            responsive: true,
            guides: true,
        });
    }

    /**
     * Get the crop coordinates (integers, relative to the displayed image).
     * @returns {{ x: number, y: number, width: number, height: number }}
     */
    getCropData() {
        if (!this._cropper) return null;
        const data = this._cropper.getData(true);
        return {
            x: Math.round(data.x),
            y: Math.round(data.y),
            width: Math.round(data.width),
            height: Math.round(data.height),
        };
    }

    /**
     * Destroy the cropper instance.
     */
    destroy() {
        if (this._cropper) {
            this._cropper.destroy();
            this._cropper = null;
        }
    }
}
