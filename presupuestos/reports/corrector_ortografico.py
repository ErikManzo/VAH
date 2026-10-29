# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/reports/corrector_ortografico.py

CORRECTOR ORTOGRÁFICO PROFESIONAL VERSIÓN 3.0
- Subraya palabras mal escritas en ROJO
- Sugerencias al hacer clic derecho mediante eventFilter
- Cache de palabras para alto rendimiento
- Throttling para evitar sobrecarga en textos largos
"""

import re
from typing import List, Optional, Dict
from PyQt6.QtCore import QObject, QEvent, Qt, QTimer
from PyQt6.QtGui import QTextCharFormat, QColor, QSyntaxHighlighter, QTextCursor, QAction
from PyQt6.QtWidgets import QTextEdit, QApplication, QMenu

# ============================================================================
# INTENTAR IMPORTAR PYSPELLCHECKER
# ============================================================================
try:
    from spellchecker import SpellChecker

    SPELLCHECKER_AVAILABLE = True
    print("[Corrector] pyspellchecker instalado correctamente")
except ImportError:
    SPELLCHECKER_AVAILABLE = False
    print("[Corrector] pyspellchecker NO instalado. Ejecute: pip install pyspellchecker")


# ============================================================================
# CLASE PARA RESALTAR PALABRAS MAL ESCRITAS
# ============================================================================
class CorrectorSyntaxHighlighter(QSyntaxHighlighter):
    """Resalta palabras mal escritas en QTextEdit."""

    PALABRA_PATRON = re.compile(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]{2,}\b')

    def __init__(self, parent: QTextEdit):
        super().__init__(parent)
        self._spell_checker: Optional[SpellChecker] = None
        self._word_cache: Dict[str, bool] = {}
        self._cargar_diccionario()

    def _cargar_diccionario(self):
        if not SPELLCHECKER_AVAILABLE:
            return
        try:
            self._spell_checker = SpellChecker(language='es', distance=1)
            print("[Corrector] Diccionario español cargado")
        except Exception as e:
            print(f"[Corrector] Error cargando diccionario: {e}")

    def _palabra_esta_correcta(self, palabra: str) -> bool:
        if not self._spell_checker:
            return True
        palabra_lower = palabra.lower()
        if palabra_lower in self._word_cache:
            return self._word_cache[palabra_lower]
        try:
            es_correcta = len(self._spell_checker.unknown([palabra_lower])) == 0
        except:
            es_correcta = True
        self._word_cache[palabra_lower] = es_correcta
        if len(self._word_cache) > 5000:
            self._word_cache.clear()
        return es_correcta

    def obtener_sugerencias(self, palabra: str) -> List[str]:
        if not self._spell_checker:
            return []
        palabra_lower = palabra.lower()
        if self._palabra_esta_correcta(palabra_lower):
            return []
        try:
            sugerencias = self._spell_checker.candidates(palabra_lower)
            if sugerencias:
                resultado = list(sugerencias)[:5]
                if palabra and palabra[0].isupper():
                    resultado = [s.capitalize() for s in resultado]
                return resultado
        except Exception as e:
            print(f"[Corrector] Error en sugerencias: {e}")
        return []

    def highlightBlock(self, text: str):
        if not self._spell_checker:
            return
        formato_error = QTextCharFormat()
        formato_error.setUnderlineColor(QColor(255, 0, 0))
        formato_error.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
        for match in self.PALABRA_PATRON.finditer(text):
            palabra = text[match.start():match.end()]
            if len(palabra) < 3 or len(palabra) > 30:
                continue
            if any(c.isdigit() for c in palabra):
                continue
            if not self._palabra_esta_correcta(palabra):
                self.setFormat(match.start(), match.end() - match.start(), formato_error)


# ============================================================================
# CLASE PRINCIPAL DEL CORRECTOR
# ============================================================================
class CorrectorOrtografico(QObject):
    """Gestor principal del corrector ortográfico."""

    def __init__(self):
        super().__init__()
        self._highlighters: Dict[QTextEdit, CorrectorSyntaxHighlighter] = {}
        self._timers: Dict[QTextEdit, QTimer] = {}
        self._filtro_instalado = False
        print("[Corrector] Inicializado")

    def habilitar_para_textedit(self, text_edit: QTextEdit) -> bool:
        if not SPELLCHECKER_AVAILABLE or not text_edit:
            return False
        if text_edit in self._highlighters:
            return True
        try:
            highlighter = CorrectorSyntaxHighlighter(text_edit)
            self._highlighters[text_edit] = highlighter

            # Timer para throttle
            timer = QTimer()
            timer.setSingleShot(True)
            self._timers[text_edit] = timer

            def on_text_changed():
                if text_edit in self._timers:
                    t = self._timers[text_edit]
                    t.stop()
                    try:
                        t.timeout.disconnect()
                    except:
                        pass
                    t.timeout.connect(lambda: highlighter.rehighlight())
                    t.start(300)

            text_edit.textChanged.connect(on_text_changed)
            highlighter.rehighlight()

            print(f"[Corrector] ✓ Habilitado: {text_edit.objectName() or 'sin nombre'}")
            return True
        except Exception as e:
            print(f"[Corrector] Error: {e}")
            return False

    def instalar_filtro(self):
        if self._filtro_instalado:
            return
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)
            self._filtro_instalado = True
            print("[Corrector] Filtro de eventos instalado")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ContextMenu:
            if isinstance(obj, QTextEdit) and obj in self._highlighters:
                self._mostrar_menu_sugerencias(obj, event)
                return True
        return super().eventFilter(obj, event)

    def _mostrar_menu_sugerencias(self, widget: QTextEdit, event):
        cursor = widget.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        palabra = cursor.selectedText().strip()

        if not palabra or len(palabra) < 3 or len(palabra) > 30:
            return

        if not all(c.isalpha() or c in "áéíóúüñÁÉÍÓÚÜÑ" for c in palabra):
            return

        highlighter = self._highlighters.get(widget)
        if not highlighter:
            return

        if highlighter._palabra_esta_correcta(palabra):
            return

        sugerencias = highlighter.obtener_sugerencias(palabra)
        if not sugerencias:
            return

        menu = QMenu(widget)
        for sug in sugerencias:
            accion = QAction(sug, widget)
            accion.triggered.connect(
                lambda checked, s=sug, w=widget, c=cursor:
                self._reemplazar_palabra(w, c, s)
            )
            menu.addAction(accion)
        menu.addSeparator()
        ignorar = QAction(f"Ignorar '{palabra}'", widget)
        ignorar.setEnabled(False)
        menu.addAction(ignorar)
        menu.exec(event.globalPos())
        event.accept()

    def _reemplazar_palabra(self, widget: QTextEdit, cursor: QTextCursor, sugerencia: str):
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.removeSelectedText()
        cursor.insertText(sugerencia)
        cursor.endEditBlock()
        if widget in self._highlighters:
            self._highlighters[widget].rehighlight()


# ============================================================================
# INSTANCIA GLOBAL
# ============================================================================
_corrector = None


def obtener_corrector():
    global _corrector
    if _corrector is None:
        _corrector = CorrectorOrtografico()
    return _corrector


def habilitar_corrector_para_campos(ventana) -> bool:
    """Habilita el corrector para los campos de texto."""
    if not SPELLCHECKER_AVAILABLE:
        print("[Corrector] pyspellchecker no instalado")
        return False

    corrector = obtener_corrector()
    habilitados = 0

    if hasattr(ventana, 'te_desc') and ventana.te_desc:
        ventana.te_desc.setObjectName("te_desc")
        if corrector.habilitar_para_textedit(ventana.te_desc):
            habilitados += 1

    if hasattr(ventana, 'le_titulo') and ventana.le_titulo:
        ventana.le_titulo.setObjectName("le_titulo")
        if corrector.habilitar_para_textedit(ventana.le_titulo):
            habilitados += 1

    if hasattr(ventana, 'le_obra') and ventana.le_obra:
        ventana.le_obra.setObjectName("le_obra")
        if corrector.habilitar_para_textedit(ventana.le_obra):
            habilitados += 1

    corrector.instalar_filtro()
    print(f"[Corrector] Habilitado en {habilitados} campos")
    return habilitados > 0


corrector = obtener_corrector()

if __name__ == "__main__":
    print("=" * 50)
    print("Corrector Ortográfico VAH v3.0")
    print(f"pyspellchecker: {'OK' if SPELLCHECKER_AVAILABLE else 'NO'}")
    print("=" * 50)