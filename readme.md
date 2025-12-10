# Advanced Printed Text Scanner (OCR) 🧾

A **modern, intuitive, and powerful** desktop application built with **PyQt5** that extracts printed text from images and live camera feed using **Tesseract OCR**.

Perfect for assignments, document digitization, real-time scanning, and automation projects.

### Live Demo
("C:\Users\pc\Desktop\Robotics\Printed-text-ocr\OCR.png")  


---

### Features

- **Beautiful Modern GUI** (PyQt5) – clean, responsive, professional look  
- **Load Image from File** – supports JPG, PNG, BMP  
- **Live Camera Feed** – real-time preview from webcam  
- **Capture Frame** – freeze any moment from camera  
- **Region of Interest (ROI) Selection** – drag to select specific text area  
- **Smart OCR with Tesseract** – accurate printed text extraction  
- **Live Text Overlay** – green bounding boxes + detected text on image  
- **Extracted Text Display** – clean, copyable, monospaced output  
- **Save Extracted Text** – export results to `.txt` file  
- **Error Handling & User Feedback** – no crashes, clear messages  

---

### Requirements

- Python 3.7+
- Tesseract OCR installed (Windows executable)

### Installation

1. **Install Tesseract OCR**  
   Download & install from:  
   https://github.com/UB-Mannheim/tesseract/wiki  
   → Default path: `C:\Program Files\Tesseract-OCR\tesseract.exe`

2. **Install Python dependencies**
   ```bash
   pip install pyqt5 opencv-python pytesseract pillow numpy