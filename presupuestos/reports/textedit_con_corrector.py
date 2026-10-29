# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/reports/textedit_con_corrector.py

CORRECTOR ORTOGRÁFICO - VERSIÓN 7.2 DEFINITIVA
- CORREGIDO: Manejo correcto de mayúsculas
- CORREGIDO: Palabras en MAYÚSCULAS ya no se marcan todas como error
"""

import re
import os
import json
from typing import List, Optional, Set, Tuple
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QTextCharFormat, QColor, QSyntaxHighlighter, QTextCursor, QAction
from PyQt6.QtWidgets import QTextEdit, QMenu, QMessageBox, QApplication

# ============================================================================
# LANGUAGE TOOL
# ============================================================================
LANGUAGETOOL_AVAILABLE = False
try:
    import language_tool_python

    LANGUAGETOOL_AVAILABLE = True
    print("[Corrector] language_tool_python instalado")
except ImportError:
    print("[Corrector] language_tool_python NO instalado")

SPELLCHECKER_AVAILABLE = False
try:
    from spellchecker import SpellChecker

    SPELLCHECKER_AVAILABLE = True
    print("[Corrector] pyspellchecker disponible")
except ImportError:
    pass


# ============================================================================
# DICCIONARIO PERSONALIZADO
# ============================================================================
class DiccionarioPersonalizado:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializar()
        return cls._instancia

    def _inicializar(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._ruta = os.path.join(base_dir, "data", "diccionario_personal.json")
        os.makedirs(os.path.dirname(self._ruta), exist_ok=True)
        self._palabras: Set[str] = set()
        self._cargar()

    def _cargar(self):
        if os.path.exists(self._ruta):
            try:
                with open(self._ruta, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._palabras = set(data.get("palabras", []))
                print(f"[Diccionario] Cargadas {len(self._palabras)} palabras")
            except:
                pass

    def guardar(self):
        try:
            with open(self._ruta, 'w', encoding='utf-8') as f:
                json.dump({"palabras": list(self._palabras)}, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False

    def agregar(self, palabra: str) -> bool:
        palabra = palabra.strip().lower()
        if not palabra or len(palabra) < 2:
            return False
        if palabra in self._palabras:
            return False
        self._palabras.add(palabra)
        self.guardar()
        return True

    def contiene(self, palabra: str) -> bool:
        return palabra.strip().lower() in self._palabras

    def listar(self) -> List[str]:
        return sorted(list(self._palabras))


# ============================================================================
# HIGHLIGHTER
# ============================================================================
class CorrectorHighlighter(QSyntaxHighlighter):
    PALABRA_PATRON = re.compile(r'\b[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]{3,}\b')

    def __init__(self, parent: QTextEdit):
        super().__init__(parent)
        self._tool = None
        self._spell = None
        self._cache = {}
        self._dic = DiccionarioPersonalizado()
        self._inicializar()

    def _inicializar(self):
        if LANGUAGETOOL_AVAILABLE:
            try:
                self._tool = language_tool_python.LanguageTool('es')
                print("[Corrector] LanguageTool cargado")
                return
            except Exception as e:
                print(f"[Corrector] Error LanguageTool: {e}")

        if SPELLCHECKER_AVAILABLE:
            try:
                self._spell = SpellChecker(language='es', distance=1)
                print("[Corrector] SpellChecker cargado")
            except:
                pass

    def _es_correcta(self, palabra: str) -> bool:
        """
        Verifica si una palabra está correctamente escrita.
        Normaliza a minúsculas para la verificación.
        """
        # Normalizar a minúsculas para la verificación
        palabra_normalizada = palabra.lower()

        if palabra_normalizada in self._cache:
            return self._cache[palabra_normalizada]

        if self._dic.contiene(palabra_normalizada):
            self._cache[palabra_normalizada] = True
            return True

        if self._tool:
            try:
                # Verificar con la palabra normalizada
                matches = self._tool.check(palabra_normalizada)
                tiene_error = len(matches) > 0

                # Si no hay error, la palabra es correcta
                if not tiene_error:
                    self._cache[palabra_normalizada] = True
                    return True
                else:
                    # Verificar si el error es solo por mayúsculas
                    # Probar con la palabra original
                    matches_upper = self._tool.check(palabra)
                    if len(matches_upper) == 0:
                        self._cache[palabra_normalizada] = True
                        return True
                    self._cache[palabra_normalizada] = False
                    return False
            except:
                pass

        if self._spell:
            try:
                es_correcta = len(self._spell.unknown([palabra_normalizada])) == 0
                self._cache[palabra_normalizada] = es_correcta
                return es_correcta
            except:
                pass

        self._cache[palabra_normalizada] = True
        return True

    def obtener_sugerencias(self, palabra: str) -> List[str]:
        palabra_normalizada = palabra.lower()

        if self._dic.contiene(palabra_normalizada):
            return []

        if self._tool:
            try:
                matches = self._tool.check(palabra_normalizada)
                for match in matches:
                    if hasattr(match, 'replacements') and match.replacements:
                        resultado = match.replacements[:5]
                        # Respetar el formato de mayúsculas de la palabra original
                        if palabra and palabra[0].isupper():
                            resultado = [r.capitalize() for r in resultado]
                        elif palabra and palabra.isupper():
                            resultado = [r.upper() for r in resultado]
                        return resultado
            except:
                pass

        if self._spell:
            try:
                if len(self._spell.unknown([palabra_normalizada])) > 0:
                    sugerencias = self._spell.candidates(palabra_normalizada)
                    if sugerencias:
                        resultado = list(sugerencias)[:5]
                        if palabra and palabra[0].isupper():
                            resultado = [s.capitalize() for s in resultado]
                        elif palabra and palabra.isupper():
                            resultado = [s.upper() for s in resultado]
                        return resultado
            except:
                pass

        return []

    def highlightBlock(self, text: str):
        if not (self._tool or self._spell):
            return

        formato = QTextCharFormat()
        formato.setUnderlineColor(QColor(255, 0, 0))
        formato.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)

        for match in self.PALABRA_PATRON.finditer(text):
            palabra = text[match.start():match.end()]
            if any(c.isdigit() for c in palabra):
                continue
            if not self._es_correcta(palabra):
                self.setFormat(match.start(), match.end() - match.start(), formato)


# ============================================================================
# TEXTEDIT CON CORRECTOR
# ============================================================================
class TextEditConCorrector(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._highlighter = None
        self._dic = DiccionarioPersonalizado()
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._rehighlight)

        if LANGUAGETOOL_AVAILABLE or SPELLCHECKER_AVAILABLE:
            self._highlighter = CorrectorHighlighter(self)
            self.textChanged.connect(self._on_text_changed)
            print(f"[Corrector] TextEditConCorrector creado")

    # Compatibilidad con QLineEdit
    def text(self) -> str:
        return self.toPlainText()

    def setText(self, texto: str):
        self.setPlainText(texto)

    def _on_text_changed(self):
        if self._timer.isActive():
            self._timer.stop()
        self._timer.start(300)

    def _rehighlight(self):
        if self._highlighter:
            self._highlighter.rehighlight()

    def _obtener_palabra_bajo_cursor(self) -> Tuple[str, QTextCursor]:
        cursor = self.textCursor()
        pos_original = cursor.position()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        palabra = cursor.selectedText().strip()
        cursor.setPosition(pos_original)
        self.setTextCursor(cursor)
        return palabra, cursor

    def _mostrar_menu(self, pos: QPoint):
        palabra, cursor = self._obtener_palabra_bajo_cursor()

        print(f"[Corrector] Menú contextual - palabra: '{palabra}', largo: {len(palabra)}")

        menu = self.createStandardContextMenu()

        if len(palabra) >= 3 and self._highlighter:
            if not self._highlighter._es_correcta(palabra):
                sugerencias = self._highlighter.obtener_sugerencias(palabra)
                print(f"[Corrector] Sugerencias: {sugerencias}")

                if sugerencias:
                    menu.addSeparator()
                    titulo = QAction("📝 Sugerencias:", self)
                    titulo.setEnabled(False)
                    menu.addAction(titulo)

                    for sug in sugerencias:
                        accion = QAction(f"  → {sug}", self)
                        accion.triggered.connect(lambda checked, s=sug: self._reemplazar_palabra(s))
                        menu.addAction(accion)

                    menu.addSeparator()

                agregar = QAction(f"➕ Agregar '{palabra}' al diccionario", self)
                agregar.triggered.connect(lambda checked, p=palabra: self._agregar_al_diccionario(p))
                menu.addAction(agregar)
                menu.addSeparator()

        menu.exec(self.viewport().mapToGlobal(pos))

    def contextMenuEvent(self, event):
        self._mostrar_menu(event.pos())
        event.accept()

    def _reemplazar_palabra(self, sugerencia: str):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        palabra_original = cursor.selectedText().strip()

        # Determinar el formato de mayúsculas de la palabra original
        if palabra_original.isupper():
            sugerencia = sugerencia.upper()
        elif palabra_original.istitle():
            sugerencia = sugerencia.capitalize()

        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(sugerencia)
        cursor.endEditBlock()

        if self._highlighter:
            self._highlighter.rehighlight()

    def _agregar_al_diccionario(self, palabra: str):
        if self._dic.agregar(palabra):
            QMessageBox.information(self, "Agregada",
                                    f"Palabra '{palabra}' agregada al diccionario.\n\nYa no será marcada como error.")
            if self._highlighter:
                self._highlighter._cache.clear()
                self._highlighter.rehighlight()
        else:
            QMessageBox.information(self, "Ya existe", f"La palabra '{palabra}' ya está en el diccionario.")


# ============================================================================
# DIÁLOGO DE GESTIÓN
# ============================================================================
class GestionDiccionarioDialog(QMessageBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diccionario Personalizado")
        self.setIcon(QMessageBox.Icon.Information)

        dic = DiccionarioPersonalizado()
        palabras = dic.listar()

        if palabras:
            texto = f"<b>Palabras en diccionario personalizado ({len(palabras)}):</b><br><br>"
            for i, p in enumerate(palabras):
                texto += p
                if (i + 1) % 6 != 0:
                    texto += " &nbsp; • &nbsp; "
                else:
                    texto += "<br>"
        else:
            texto = "<b>Diccionario personalizado vacío.</b><br><br>Haga clic derecho sobre una palabra subrayada y seleccione 'Agregar al diccionario'."

        self.setText(texto)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================
def habilitar_corrector_para_campos(ventana) -> bool:
    if not (LANGUAGETOOL_AVAILABLE or SPELLCHECKER_AVAILABLE):
        print("[Corrector] No hay corrector disponible")
        return False

    habilitados = 0

    if hasattr(ventana, 'te_desc') and ventana.te_desc:
        if isinstance(ventana.te_desc, TextEditConCorrector):
            habilitados += 1
            print("[Corrector] ✓ te_desc es TextEditConCorrector")

    if hasattr(ventana, 'le_titulo') and ventana.le_titulo:
        if isinstance(ventana.le_titulo, TextEditConCorrector):
            habilitados += 1
            print("[Corrector] ✓ le_titulo es TextEditConCorrector")

    if hasattr(ventana, 'le_obra') and ventana.le_obra:
        if isinstance(ventana.le_obra, TextEditConCorrector):
            habilitados += 1
            print("[Corrector] ✓ le_obra es TextEditConCorrector")

    print(f"[Corrector] Correctores activos: {habilitados}")
    return habilitados > 0