import sys
from pathlib import Path
from PySide6.QtCore import QObject,QThread,Signal,Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication,QWidget,QHBoxLayout,QVBoxLayout,QLabel,QPushButton,QFileDialog,QProgressBar,QFrame,QCheckBox
from scanner import scan

EXTS={".mp4",".mov",".mkv",".avi",".m4v",".webm"}

class Worker(QObject):
    progress=Signal(int,str); finished=Signal(str); failed=Signal(str)
    def __init__(self,paths,timecode=True): super().__init__(); self.paths=paths; self.timecode=timecode
    def run(self):
        try:
            outs=[]; total=len(self.paths)
            for n,path in enumerate(self.paths,1):
                def cb(p,msg,n=n,path=path):
                    self.progress.emit(int(((n-1)+p/100)/total*100),f"{n}/{total}  {Path(path).name}  {msg}")
                outs.append(str(scan(path,cb,timecode=self.timecode)))
            self.finished.emit("\n".join(outs))
        except Exception as e: self.failed.emit(str(e))

class Window(QWidget):
    def __init__(self):
        super().__init__(); self.videos=[]; self.setWindowTitle("VIDZ SCAN FAST"); self.resize(980,620); self.setAcceptDrops(True)
        self.setStyleSheet("""
        QWidget{background:white;color:#111;font-family:Menlo,monospace}
        QFrame#rail{background:white;border-right:3px solid #111}
        QPushButton{background:white;color:#111;border:2px solid #111;padding:14px 10px;font-weight:900;text-align:left}
        QPushButton:hover{background:#111;color:white}
        QPushButton:disabled{color:#aaa;border-color:#aaa}
        QLabel#count{font-size:46px;font-weight:900}
        QLabel#drop{font-size:28px;font-weight:900}
        QProgressBar{border:2px solid #111;height:26px;text-align:center;background:white}
        QProgressBar::chunk{background:#111}
        """)
        root=QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        rail=QFrame(); rail.setObjectName("rail"); rail.setFixedWidth(235); left=QVBoxLayout(rail); left.setContentsMargins(20,22,20,22); left.setSpacing(14)
        logo=QLabel(); base=Path(getattr(sys,"_MEIPASS",Path(__file__).parent)); pix=QPixmap(str(base/"logo.png")); logo.setPixmap(pix.scaled(180,180,Qt.KeepAspectRatio,Qt.SmoothTransformation)); logo.setAlignment(Qt.AlignCenter); left.addWidget(logo)
        choose=QPushButton("＋  VIDEOS"); choose.clicked.connect(self.choose); folder=QPushButton("▣  FOLDER"); folder.clicked.connect(self.choose_folder)
        self.tc=QCheckBox("TIME CODE"); self.tc.setChecked(True); left.addWidget(self.tc)
        self.scan_btn=QPushButton("▶  SCAN BATCH"); self.scan_btn.clicked.connect(self.start_scan); self.scan_btn.setEnabled(False)
        clear=QPushButton("×  CLEAR"); clear.clicked.connect(self.clear)
        left.addWidget(choose); left.addWidget(folder); left.addWidget(self.scan_btn); left.addWidget(clear); left.addStretch()
        self.count=QLabel("00"); self.count.setObjectName("count"); left.addWidget(self.count)
        left.addWidget(QLabel("VIDEOS LOADED"))
        root.addWidget(rail)

        stage=QWidget(); right=QVBoxLayout(stage); right.setContentsMargins(48,42,48,36); right.setSpacing(18)
        kicker=QLabel("VIDEO → SCAN → UNDERSTAND → MAP"); kicker.setStyleSheet("font-size:12px;letter-spacing:2px")
        self.drop_label=QLabel("DROP\nVIDEOS\nHERE"); self.drop_label.setObjectName("drop"); self.drop_label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.drop_label.setStyleSheet("font-size:58px;font-weight:900;border:3px dashed #111;padding:35px")
        right.addWidget(kicker); right.addWidget(self.drop_label,1)
        self.status=QLabel("READY"); self.status.setWordWrap(True); self.status.setStyleSheet("font-size:14px;font-weight:800")
        self.bar=QProgressBar(); self.bar.setRange(0,100); self.bar.setValue(0)
        right.addWidget(self.status); right.addWidget(self.bar)
        root.addWidget(stage,1)

    def collect(self,paths):
        found=[]
        for p in paths:
            q=Path(p)
            if q.is_dir(): found += [str(x) for x in sorted(q.iterdir()) if x.suffix.lower() in EXTS]
            elif q.suffix.lower() in EXTS: found.append(str(q))
        self.videos=list(dict.fromkeys(found)); n=len(self.videos); self.count.setText(f"{n:02d}"); self.scan_btn.setEnabled(bool(n))
        self.drop_label.setText("\n".join(Path(x).name for x in self.videos[:7]) + (f"\n+ {n-7} MORE" if n>7 else "") if n else "DROP\nVIDEOS\nHERE")
        self.status.setText(f"BATCH READY · {n} VIDEO{'S' if n!=1 else ''}" if n else "READY")
    def choose(self):
        p,_=QFileDialog.getOpenFileNames(self,"Choose videos","","Video files (*.mp4 *.mov *.mkv *.avi *.m4v *.webm)")
        if p:self.collect(p)
    def choose_folder(self):
        p=QFileDialog.getExistingDirectory(self,"Choose folder")
        if p:self.collect([p])
    def clear(self): self.videos=[]; self.count.setText("00"); self.drop_label.setText("DROP\nVIDEOS\nHERE"); self.status.setText("READY"); self.bar.setValue(0); self.scan_btn.setEnabled(False)
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls():e.acceptProposedAction()
    def dropEvent(self,e): self.collect([u.toLocalFile() for u in e.mimeData().urls()])
    def start_scan(self):
        if not self.videos:return
        QApplication.beep(); self.scan_btn.setEnabled(False); self.thread=QThread(); self.worker=Worker(self.videos,self.tc.isChecked()); self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run); self.worker.progress.connect(self.on_progress); self.worker.finished.connect(self.on_finished); self.worker.failed.connect(self.on_failed); self.worker.finished.connect(self.thread.quit); self.worker.failed.connect(self.thread.quit); self.thread.start()
    def on_progress(self,v,t): self.bar.setValue(v); self.status.setText(t)
    def on_finished(self,o): self.scan_btn.setEnabled(True); self.bar.setValue(100); self.status.setText(f"DONE · {len(self.videos)} VIDEOS SCANNED"); QApplication.beep(); QApplication.beep()
    def on_failed(self,e): self.scan_btn.setEnabled(True); self.status.setText(f"ERROR → {e}")

if __name__=="__main__":
    app=QApplication(sys.argv); win=Window(); win.show(); sys.exit(app.exec())
