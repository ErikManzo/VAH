# D:\vah\convertir_py_a_pdf.py
"""
Convierte archivos .py seleccionados en archivos PDF.
Cada archivo .py genera un PDF independiente con el mismo nombre.
El usuario selecciona los .py y la carpeta destino.
"""

import os
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm

def convertir_py_a_pdf(archivos: list[str], carpeta_destino: str):
    """Convierte una lista de archivos .py en PDF independientes."""
    for archivo in archivos:
        try:
            nombre = os.path.basename(archivo)
            nombre_sin_ext = os.path.splitext(nombre)[0]
            salida = os.path.join(carpeta_destino, f"{nombre_sin_ext}.pdf")

            # Crear PDF
            c = canvas.Canvas(salida, pagesize=letter)
            width, height = letter
            margen_izq, margen_sup = 20 * mm, 20 * mm
            y = height - margen_sup

            c.setFont("Courier", 9)  # fuente monoespaciada

            with open(archivo, "r", encoding="utf-8") as f:
                for num_linea, linea in enumerate(f, start=1):
                    linea = linea.rstrip("\n")
                    texto = f"{num_linea:04d}: {linea}"

                    if y < 20 * mm:  # salto de página
                        c.showPage()
                        c.setFont("Courier", 9)
                        y = height - margen_sup

                    c.drawString(margen_izq, y, texto)
                    y -= 10  # espacio entre líneas

            c.save()
            print(f"✅ {archivo} convertido a {salida}")

        except Exception as e:
            print(f"❌ Error convirtiendo {archivo}: {e}")

def main():
    app = QApplication([])

    # Seleccionar archivos .py
    archivos, _ = QFileDialog.getOpenFileNames(
        None,
        "Seleccionar archivos .py",
        "",
        "Python Files (*.py)"
    )
    if not archivos:
        QMessageBox.information(None, "Convertir", "No se seleccionaron archivos.")
        return

    # Seleccionar carpeta destino
    carpeta_destino = QFileDialog.getExistingDirectory(
        None,
        "Seleccionar carpeta destino"
    )
    if not carpeta_destino:
        QMessageBox.information(None, "Convertir", "No se seleccionó carpeta destino.")
        return

    # Convertir
    convertir_py_a_pdf(archivos, carpeta_destino)

    QMessageBox.information(
        None,
        "Convertir",
        f"✅ Conversión completada.\nArchivos guardados en:\n{carpeta_destino}"
    )

if __name__ == "__main__":
    main()
