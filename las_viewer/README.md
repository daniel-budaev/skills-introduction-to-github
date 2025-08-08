# LAS Viewer & Editor

A simple Streamlit app to view, edit, plot, and export LAS (Log ASCII Standard) files using `lasio`.

## Features
- Load `.las` from upload or file path
- View overview, curves metadata, well/params metadata
- Edit curves order/units/descriptions and data values
- Plot selected curves vs depth (with reversed depth axis)
- Export the edited LAS (choose LAS 2.0/3.0, WRAP YES/NO)

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run
```bash
streamlit run app.py
```

Then open the provided local/remote URL in your browser.

## Notes
- Editing is in-memory until you export. Use the Export tab to download a `.las`.
- Large files: use the depth range slider in Data tab to limit rows for editing.
- Requires Python 3.9+.