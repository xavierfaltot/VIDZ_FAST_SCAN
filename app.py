import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QProgressBar, QFrame
)

from scanner import scan


class Worker(QObject):
    progress = Signal(int, str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            out = scan(self.path, self.progress.emit)
            self.finished.emit(str(out))
        except Exception as e:
            self.failed.emit(str(e))


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.video = None
        self.setWindowTitle("VIDZ SCAN FAST")
        self.resize(760, 520)
        self.setAcceptDrops(True)

        self.setStyleSheet("""
            QWidget { background:#f4f1e8; color:#111; font-family: Menlo, monospace; }
            QLabel#title { font-size:38px; font-weight:900; letter-spacing:-2px; }
            QLabel#sub { font-size:13px; }
            QFrame#drop { border:2px dashed #111; border-radius:12px; }
            QPushButton { background:#111; color:#f4f1e8; border:0; padding:16px 22px; font-weight:800; }
            QPushButton:disabled { background:#999; }
            QProgressBar { border:1px solid #111; height:22px; text-align:center; }
            QProgressBar::chunk { background:#111; }
        """)

        root = QVBoxLayout(self)
        title = QLabel("VIDZ SCAN FAST")
        title.setObjectName("title")
        sub = QLabel("VIDEO → SCAN → UNDERSTAND → MAP")
        sub.setObjectName("sub")
        root.addWidget(title)
        root.addWidget(sub)

        self.drop = QFrame()
        self.drop.setObjectName("drop")
        dl = QVBoxLayout(self.drop)
        self.file_label = QLabel("DROP VIDEO HERE")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet("font-size:22px;font-weight:800;")
        choose = QPushButton("CHOOSE VIDEO")
        choose.clicked.connect(self.choose)
        dl.addStretch()
        dl.addWidget(self.file_label)
        dl.addWidget(choose, alignment=Qt.AlignCenter)
        dl.addStretch()
        root.addWidget(self.drop, 1)

        row = QHBoxLayout()
        self.scan_btn = QPushButton("SCAN")
        self.scan_btn.setEnabled(False)
        self.scan_btn.clicked.connect(self.start_scan)
        self.status = QLabel("READY")
        row.addWidget(self.scan_btn)
        row.addWidget(self.status, 1)
        root.addLayout(row)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        root.addWidget(self.bar)

    def choose(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose video", "",
            "Video files (*.mp4 *.mov *.mkv *.avi *.m4v *.webm)"
        )
        if path:
            self.set_video(path)

    def set_video(self, path):
        self.video = path
        self.file_label.setText(Path(path).name)
        self.scan_btn.setEnabled(True)
        self.status.setText("VIDEO LOADED")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            self.set_video(urls[0].toLocalFile())

    def start_scan(self):
        if not self.video:
            return
        self.scan_btn.setEnabled(False)
        self.thread = QThread()
        self.worker = Worker(self.video)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.start()

    def on_progress(self, value, text):
        self.bar.setValue(value)
        self.status.setText(text)

    def on_finished(self, output):
        self.scan_btn.setEnabled(True)
        self.status.setText(f"DONE → {output}")

    def on_failed(self, error):
        self.scan_btn.setEnabled(True)
        self.status.setText(f"ERROR → {error}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec())
