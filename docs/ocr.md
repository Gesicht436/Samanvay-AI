# Document OCR and Ingest

`OCR/` is the byte-oriented document extraction boundary used by
`POST /v1/ingest/document`. The backend does not write uploaded files to a
temporary path.

- PDFs use per-page hybrid routing: pages with native text stay on PyMuPDF;
  pages without a text layer are rasterized and sent to OCR.
- OCR pages are rendered at 300 DPI, then denoised, deskewed, and contrast
  normalized before recognition.
- PaddleOCR is the primary engine. Empty or failed PaddleOCR results fall back
  to EasyOCR; the response records the engine and raster DPI per OCR page.
- OCR text is normalized before the full MTC parser and chemistry/mechanical
  property extraction run. Manufacturer and TPI/inspection-agency values are
  returned both as engineering attributes and as UI-ready lists.
- Document responses include the OCR profile and page-level routing metadata.
  The dashboard reports the configured policy and whether both optional OCR
  engines are installed.

Install OCR support with `pip install -e ".[ml]"`. The base installation
continues to support native-text PDF extraction without the OCR dependencies.