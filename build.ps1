python -m PyInstaller `
  --noconfirm `
  --onefile `
  --windowed `
  --add-data "DS-DIGIB-2.ttf;." `
  --add-data "default_settings.json;." `
  --add-data "字体库;字体库" `
  app.py
