import sys
from pathlib import Path
from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QFileDialog,QProgressBar,QFrame
from scanner import scan
EXTS={".mp4",".mov",".mkv",".avi",".m4v",".webm"}
class Worker(QObject):
    progress=Signal(int,str); finished=Signal(str); failed=Signal(str)
    def __init__(self,paths): super().__init__(); self.paths=paths
    def run(self):
        try:
            outputs=[]; total=len(self.paths)
            for n,path in enumerate(self.paths,1):
                def cb(p,msg,n=n,path=path):
                    overall=int(((n-1)+p/100)/total*100)
                    self.progress.emit(overall,f"{n}/{total} · {Path(path).name} · {msg}")
                outputs.append(str(scan(path,cb)))
            self.finished.emit("\n".join(outputs))
        except Exception as e: self.failed.emit(str(e))
class Window(QWidget):
    def __init__(self):
        super().__init__(); self.videos=[]; self.setWindowTitle("VIDZ SCAN FAST"); self.resize(760,520); self.setAcceptDrops(True)
        self.setStyleSheet("""QWidget{background:#f4f1e8;color:#111;font-family:Menlo,monospace} QLabel#title{font-size:38px;font-weight:900;letter-spacing:-2px} QLabel#sub{font-size:13px} QFrame#drop{border:2px dashed #111;border-radius:12px} QPushButton{background:#111;color:#f4f1e8;border:0;padding:16px 22px;font-weight:800} QPushButton:disabled{background:#999} QProgressBar{border:1px solid #111;height:22px;text-align:center} QProgressBar::chunk{background:#111}""")
        root=QVBoxLayout(self); title=QLabel("VIDZ SCAN FAST"); title.setObjectName("title"); sub=QLabel("VIDEO / FOLDER → BATCH SCAN → UNDERSTAND → MAP"); sub.setObjectName("sub"); root.addWidget(title); root.addWidget(sub)
        self.drop=QFrame(); self.drop.setObjectName("drop"); dl=QVBoxLayout(self.drop); self.file_label=QLabel("DROP VIDEOS OR FOLDER HERE"); self.file_label.setAlignment(Qt.AlignCenter); self.file_label.setStyleSheet("font-size:22px;font-weight:800;")
        buttons=QHBoxLayout(); choose=QPushButton("CHOOSE VIDEOS"); folder=QPushButton("CHOOSE FOLDER"); choose.clicked.connect(self.choose); folder.clicked.connect(self.choose_folder); buttons.addWidget(choose); buttons.addWidget(folder)
        dl.addStretch(); dl.addWidget(self.file_label); dl.addLayout(buttons); dl.addStretch(); root.addWidget(self.drop,1)
        row=QHBoxLayout(); self.scan_btn=QPushButton("SCAN BATCH"); self.scan_btn.setEnabled(False); self.scan_btn.clicked.connect(self.start_scan); self.status=QLabel("READY"); row.addWidget(self.scan_btn); row.addWidget(self.status,1); root.addLayout(row)
        self.bar=QProgressBar(); root.addWidget(self.bar)
    def collect(self,paths):
        found=[]
        for p in paths:
            q=Path(p)
            if q.is_dir(): found += [str(x) for x in sorted(q.iterdir()) if x.suffix.lower() in EXTS]
            elif q.suffix.lower() in EXTS: found.append(str(q))
        self.videos=list(dict.fromkeys(found)); n=len(self.videos); self.file_label.setText(f"{n} VIDEO{'S' if n!=1 else ''} READY" if n else "NO VIDEO FOUND"); self.scan_btn.setEnabled(bool(n)); self.status.setText(f"BATCH READY · {n} FILES" if n else "READY")
    def choose(self):
        paths,_=QFileDialog.getOpenFileNames(self,"Choose videos","","Video files (*.mp4 *.mov *.mkv *.avi *.m4v *.webm)")
        if paths:self.collect(paths)
    def choose_folder(self):
        path=QFileDialog.getExistingDirectory(self,"Choose folder")
        if path:self.collect([path])
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls():e.acceptProposedAction()
    def dropEvent(self,e): self.collect([u.toLocalFile() for u in e.mimeData().urls()])
    def start_scan(self):
        if not self.videos:return
        self.scan_btn.setEnabled(False); self.thread=QThread(); self.worker=Worker(self.videos); self.worker.moveToThread(self.thread); self.thread.started.connect(self.worker.run); self.worker.progress.connect(self.on_progress); self.worker.finished.connect(self.on_finished); self.worker.failed.connect(self.on_failed); self.worker.finished.connect(self.thread.quit); self.worker.failed.connect(self.thread.quit); self.thread.start()
    def on_progress(self,v,t): self.bar.setValue(v); self.status.setText(t)
    def on_finished(self,o): self.scan_btn.setEnabled(True); self.bar.setValue(100); self.status.setText(f"DONE · {len(self.videos)} VIDEOS SCANNED")
    def on_failed(self,e): self.scan_btn.setEnabled(True); self.status.setText(f"ERROR → {e}")
if __name__=="__main__":
    app=QApplication(sys.argv); win=Window(); win.show(); sys.exit(app.exec())
