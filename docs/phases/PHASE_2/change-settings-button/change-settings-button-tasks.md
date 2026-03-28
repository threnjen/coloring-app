# Change Settings Button — Tasks

## Stage 1: Add "Change Settings" Button

- [x] Add `<button id="change-settings-btn" class="btn btn-secondary">Change Settings</button>` to `.actions` div in `static/index.html` (between Download PDF and Start Over)
- [x] Add DOM reference `changeSettingsBtn` in `static/js/app.js`
- [x] Add click handler: `changeSettingsBtn.addEventListener('click', () => showStep(stepProcess))`
- [ ] Manual test: upload → crop → set options → generate → click "Change Settings" → verify step 3 shown with settings preserved
- [ ] Manual test: change settings → re-generate → verify new mosaic renders correctly
- [ ] Manual test: verify "Start Over" still works as before
