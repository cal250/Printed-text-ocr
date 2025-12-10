import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QMessageBox, QFileDialog, QRubberBand
from PyQt5.QtCore import QTimer, Qt, QRect, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QFont
import cv2
import pytesseract
from PIL import Image
import numpy as np
import os

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class TextScanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Printed Text Scanner")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Toolbar for buttons
        toolbar = QHBoxLayout()
        self.btn_load = QPushButton("Load Image")
        self.btn_load.clicked.connect(self.load_image)
        toolbar.addWidget(self.btn_load)
        
        self.btn_start_camera = QPushButton("Start Live Camera")
        self.btn_start_camera.clicked.connect(self.start_camera)
        toolbar.addWidget(self.btn_start_camera)
        
        self.btn_stop_camera = QPushButton("Stop Camera")
        self.btn_stop_camera.clicked.connect(self.stop_camera)
        toolbar.addWidget(self.btn_stop_camera)
        
        self.btn_capture = QPushButton("Capture Frame")
        self.btn_capture.clicked.connect(self.capture_image)
        toolbar.addWidget(self.btn_capture)
        
        self.btn_clear_roi = QPushButton("Clear ROI")
        self.btn_clear_roi.clicked.connect(self.clear_roi)
        toolbar.addWidget(self.btn_clear_roi)
        
        self.btn_ocr = QPushButton("Extract Text (OCR)")
        self.btn_ocr.setStyleSheet("background-color: green; color: white;")
        self.btn_ocr.clicked.connect(self.run_ocr)
        toolbar.addWidget(self.btn_ocr)
        
        self.btn_save_text = QPushButton("Save Extracted Text")
        self.btn_save_text.clicked.connect(self.save_text)
        toolbar.addWidget(self.btn_save_text)
        
        main_layout.addLayout(toolbar)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setFixedSize(800, 600)
        self.image_label.setStyleSheet("background-color: lightgray; border: 1px solid black;")
        self.image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        
        # Text display
        text_label = QLabel("Extracted Text:")
        text_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(text_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 11))
        main_layout.addWidget(self.text_edit)
        
        # Variables
        self.video = None
        self.image = None
        self.display_image = None
        self.roi = None
        self.is_camera_running = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_camera)
        
        # ROI selection
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self.image_label)
        self.origin = QPoint()
        self.image_label.mousePressEvent = self.start_roi
        self.image_label.mouseMoveEvent = self.draw_roi
        self.image_label.mouseReleaseEvent = self.end_roi
        
    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.stop_camera()
            self.image = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
            self.show_image()

    def start_camera(self):
        if not self.is_camera_running:
            self.video = cv2.VideoCapture(0)
            if not self.video.isOpened():
                QMessageBox.warning(self, "Error", "Could not open camera.")
                return
            self.is_camera_running = True
            self.timer.start(30)  # ~33 fps

    def stop_camera(self):
        if self.is_camera_running:
            self.is_camera_running = False
            self.timer.stop()
            if self.video:
                self.video.release()
                self.video = None

    def update_camera(self):
        ret, frame = self.video.read()
        if ret:
            self.image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.show_image()

    def capture_image(self):
        if self.is_camera_running:
            self.stop_camera()
            self.show_image()

    def show_image(self):
        if self.image is None:
            return
        height, width = self.image.shape[:2]
        scale = min(800 / width, 600 / height)
        new_size = (int(width * scale), int(height * scale))
        self.display_image = cv2.resize(self.image, new_size)
        
        q_img = QImage(self.display_image.data, self.display_image.shape[1], self.display_image.shape[0], self.display_image.strides[0], QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(q_img))
        
        # Hide rubber band if clearing
        self.rubber_band.hide()

    def start_roi(self, event):
        self.origin = event.pos()
        self.rubber_band.setGeometry(QRect(self.origin, QPoint()))
        self.rubber_band.show()

    def draw_roi(self, event):
        if not self.origin.isNull():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def end_roi(self, event):
        if not self.origin.isNull():
            end = event.pos()
            # Calculate scaled ROI for original image
            disp_w, disp_h = self.display_image.shape[1], self.display_image.shape[0]
            orig_w, orig_h = self.image.shape[1], self.image.shape[0]
            scale_x = orig_w / disp_w
            scale_y = orig_h / disp_h
            
            x1 = min(self.origin.x(), end.x())
            y1 = min(self.origin.y(), end.y())
            x2 = max(self.origin.x(), end.x())
            y2 = max(self.origin.y(), end.y())
            
            self.roi = (int(x1 * scale_x), int(y1 * scale_y), int(x2 * scale_x), int(y2 * scale_y))
            self.draw_roi_overlay()  # Draw persistent ROI on image
        self.origin = QPoint()
        self.rubber_band.hide()

    def draw_roi_overlay(self):
        if self.roi and self.display_image is not None:
            x1, y1, x2, y2 = self.roi
            orig_w, orig_h = self.image.shape[1], self.image.shape[0]
            disp_w, disp_h = self.display_image.shape[1], self.display_image.shape[0]
            scale_x = disp_w / orig_w
            scale_y = disp_h / orig_h
            disp_x1, disp_y1 = int(x1 * scale_x), int(y1 * scale_y)
            disp_x2, disp_y2 = int(x2 * scale_x), int(y2 * scale_y)
            
            overlay = self.display_image.copy()
            cv2.rectangle(overlay, (disp_x1, disp_y1), (disp_x2, disp_y2), (255, 0, 0), 2)
            
            q_img = QImage(overlay.data, overlay.shape[1], overlay.shape[0], overlay.strides[0], QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(q_img))

    def clear_roi(self):
        self.roi = None
        self.show_image()

    def run_ocr(self):
        if self.image is None:
            QMessageBox.warning(self, "Error", "No image loaded or captured.")
            return
        
        try:
            img_ocr = self.image.copy()
            if self.roi:
                x1, y1, x2, y2 = self.roi
                img_ocr = img_ocr[y1:y2, x1:x2]
                if img_ocr.size == 0:
                    QMessageBox.warning(self, "Error", "Invalid ROI selection.")
                    return
            
            pil_img = Image.fromarray(img_ocr)
            text = pytesseract.image_to_string(pil_img, lang='eng')
            
            self.text_edit.setPlainText(text)
            
            # Overlay
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            overlay = img_ocr.copy()
            n_boxes = len(data['level'])
            for i in range(n_boxes):
                conf = int(float(data['conf'][i]))
                if conf > 60:
                    (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                    cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(overlay, data['text'][i], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            if self.roi:
                x1, y1, x2, y2 = self.roi
                self.image[y1:y2, x1:x2] = overlay
            else:
                self.image = overlay
            
            self.show_image()
            self.draw_roi_overlay()  # Redraw ROI if present
        except Exception as e:
            QMessageBox.critical(self, "OCR Error", f"An error occurred during OCR: {str(e)}")

    def save_text(self):
        if self.text_edit.toPlainText():
            path, _ = QFileDialog.getSaveFileName(self, "Save Text", "", "Text Files (*.txt)")
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(self.text_edit.toPlainText())
                QMessageBox.information(self, "Success", "Text saved successfully.")
        else:
            QMessageBox.warning(self, "Error", "No text to save.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TextScanner()
    window.show()
    sys.exit(app.exec_())