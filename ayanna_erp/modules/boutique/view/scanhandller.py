from PyQt6.QtCore import QObject, QEvent, Qt, QTimer
import time
import re


class BarcodeScannerHandler(QObject):
    """
    Handler fiable pour scanner code-barres USB (mode clavier).
    - Capture uniquement les rafales rapides
    - Ignore l'auto-repeat
    - Stoppe la propagation Qt
    - Nettoie le buffer correctement
    """

    def __init__(self, parent, on_scan_callback, timeout_ms=80):
        super().__init__(parent)
        self.on_scan_callback = on_scan_callback
        self.timeout_ms = timeout_ms

        self.buffer = ""
        self.last_key_time = 0.0

        self.reset_timer = QTimer()
        self.reset_timer.setSingleShot(True)
        self.reset_timer.timeout.connect(self.reset_buffer)

    def reset_buffer(self):
        self.buffer = ""

    def eventFilter(self, obj, event):
        print(f"Event: {event.type()}")

        if event.type() != QEvent.KeyPress:
            return False

        # 🔒 Ignore auto-repeat (CRITIQUE)
        if event.isAutoRepeat():
            return True

        key = event.key()
        text = event.text()

        now = time.time()
        delta = now - self.last_key_time
        self.last_key_time = now

        # 🧹 Si trop lent → ce n’est PAS un scanner
        if delta > 0.15:
            self.buffer = ""

        # ✅ FIN DE SCAN
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.reset_timer.stop()

            # Extraire un EAN-13 valide depuis le buffer
            codes = re.findall(r'\d{13}', self.buffer)

            if codes:
                self.on_scan_callback(codes[0])

            self.reset_buffer()
            return True  # ⛔ STOP propagation

        # ❌ ignorer touches non imprimables
        if not text or not text.isdigit():
            return True

        self.buffer += text
        self.reset_timer.start(self.timeout_ms)

        return True  # ⛔ STOP propagation
