# -*- coding: utf-8 -*-
"""
Parser oficial para importación de Materiales Aluminio.

Ruta sugerida:
    D:\\vah\\materiales\\aluminio\\parsers\\parse_excel.py

Reglas oficiales:
    - Solo se acepta el formato oficial de Excel.
    - Encabezados en fila 1.
    - Datos desde fila 2.
    - Solo se procesa una hoja oficial.
    - No se permiten columnas adicionales.
    - Si el formato no coincide, se detiene la importación.
    - Puede generar plantilla oficial automáticamente.
    - Detecta claves duplicadas dentro del Excel.
    - Las claves nuevas se insertan completas.
    - Las claves existentes se actualizan según ACTUALIZAR_SOLO_MAYORES.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


# =========================================================
# EXCEPCIÓN DE FORMATO / VALIDACIÓN
# =========================================================

class FormatoExcelError(Exception):
    """
    Error lanzado cuando el Excel no cumple el formato oficial
    o tiene errores de captura.
    """

    def __init__(
        self,
        mensaje: str,
        detalles: Optional[List[str]] = None,
        ruta_plantilla: Optional[Path] = None
    ) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalles = detalles or []
        self.ruta_plantilla = ruta_plantilla

    def __str__(self) -> str:
        texto = self.mensaje

        if self.detalles:
            texto += "\n\nDetalles:\n" + "\n".join(self.detalles[:20])

        if self.ruta_plantilla:
            texto += f"\n\nPlantilla oficial generada en:\n{self.ruta_plantilla}"

        return texto


# =========================================================
# CONFIGURACIÓN OFICIAL
# =========================================================

DB_NAME = "aluminio"

EXCEL_FILE = Path(__file__).resolve().parent.parent / "lista precios aluminio.xlsx"

HOJA_OFICIAL = "Table 1"

ENCABEZADOS_OFICIALES = [
    "CLAVE",
    "DESCRIPCION",
    "LARGO",
    "SA",
    "NAT",
    "BMO",
    "E-100",
    "E-200",
    "E-400",
    "BCO",
    "HUE",
    "GRIS",
    "CHO",
    "ACE",
    "MADL",
    "MADT",
    "NP",
]

PRECIOS_COLS = [
    "sa",
    "nat",
    "bmo",
    "e100",
    "e200",
    "e400",
    "bco",
    "hue",
    "gris",
    "cho",
    "ace",
    "madl",
    "madt",
    "np",
]

CAMPOS_DB = [
    "clave",
    "descripcion",
    "largo",
    *PRECIOS_COLS,
]

LARGOS_VALIDOS = {
    Decimal("3.66"),
    Decimal("4.60"),
    Decimal("5.00"),
    Decimal("5.50"),
    Decimal("5.60"),
    Decimal("6.10"),
}

DOS_DECIMALES = Decimal("0.01")

# Si está en True:
#   - Clave existente: solo actualiza precios si el precio del Excel es mayor.
# Si está en False:
#   - Clave existente: actualiza todos los precios con lo que venga del Excel.
ACTUALIZAR_SOLO_MAYORES = True

# Si está en True:
#   - También se insertan claves nuevas aunque todos sus precios vengan en 0.00.
# Si está en False:
#   - Las claves con todos los precios en 0.00 se omiten.
INCLUIR_REGISTROS_SIN_PRECIO = True

MENSAJE_FORMATO_NO_VALIDO = (
    "El archivo no corresponde al formato oficial de importación de Materiales Aluminio.\n\n"
    "Se generará un archivo Excel con los títulos oficiales para que ahí se vacíe "
    "la información y poder realizar la importación."
)


# =========================================================
# PLANTILLA OFICIAL
# =========================================================

def generar_plantilla_excel(destino: Union[Path, str]) -> Path:
    """
    Genera un Excel con los encabezados oficiales.
    No incluye registros de ejemplo para evitar importaciones accidentales.
    """
    destino = Path(destino)

    wb = Workbook()
    ws = wb.active
    ws.title = "IMPORTACION"

    header_fill = PatternFill(
        start_color="1F6FEB",
        end_color="1F6FEB",
        fill_type="solid"
    )
    header_font = Font(
        color="FFFFFF",
        bold=True
    )

    for col, titulo in enumerate(ENCABEZADOS_OFICIALES, start=1):
        cell = ws.cell(row=1, column=col, value=titulo)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

        if col == 2:
            ws.column_dimensions[get_column_letter(col)].width = 45
        else:
            ws.column_dimensions[get_column_letter(col)].width = 16

    ws.freeze_panes = "A2"

    wi = wb.create_sheet("INSTRUCCIONES")
    wi["A1"] = "Plantilla oficial para importación de Materiales Aluminio."
    wi["A2"] = "Capture los datos en la hoja IMPORTACION respetando los encabezados."
    wi["A3"] = "No agregue columnas adicionales."
    wi["A4"] = "Los precios deben capturarse como números."
    wi["A5"] = "El campo LARGO debe usar uno de los valores permitidos."
    wi["A6"] = "Largos permitidos: 3.66, 4.60, 5.00, 5.50, 5.60, 6.10."

    wb.save(destino)
    return destino


def ruta_plantilla_para(archivo_origen: Union[Path, str]) -> Path:
    """
    Genera una ruta para la plantilla junto al archivo original.
    """
    p = Path(archivo_origen)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"{p.stem}_PLANTILLA_{ts}.xlsx"

    try:
        return p.with_name(nombre)
    except Exception:
        return Path.cwd() / nombre


def _generar_plantilla_si_procede(
    archivo: Path,
    detalles: List[str]
) -> Optional[Path]:
    """
    Intenta generar la plantilla oficial.
    Si falla, agrega el error a detalles.
    """
    try:
        destino = ruta_plantilla_para(archivo)
        generar_plantilla_excel(destino)
        return destino
    except Exception as exc:
        detalles.append(f"No fue posible generar la plantilla automáticamente: {exc}")
        return None


# =========================================================
# UTILIDADES DE CONVERSIÓN
# =========================================================

def normalizar_clave(valor) -> str:
    """
    Normaliza la clave:
      - Quita espacios.
      - Convierte a mayúsculas.
      - Si es número entero, evita que quede como 1204.0.
    """
    if valor is None:
        return ""

    if isinstance(valor, bool):
        return ""

    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)

    clave = str(valor).strip().upper()

    # Si por alguna razón viene como "1204.0", se convierte a "1204".
    if re.fullmatch(r"\d+\.0", clave):
        clave = clave[:-2]

    return clave


def parsear_numero(valor, campo: str = "", fila: int = 0) -> Decimal:
    """
    Convierte valores del Excel a Decimal.

    Acepta:
        - 1234.56
        - $ 1,234.56
        - $   - 0
        - vacío
        - 0

    Reglas:
        - Vacío => 0.00
        - '-0' => 0.00
        - Negativo real => error
    """
    if valor is None:
        return Decimal("0.00")

    if isinstance(valor, bool):
        raise ValueError(
            f"Fila {fila}: el campo {campo} tiene un valor inválido: '{valor}'."
        )

    if isinstance(valor, Decimal):
        d = valor

    elif isinstance(valor, (int, float)):
        try:
            d = Decimal(str(valor))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(
                f"Fila {fila}: el campo {campo} tiene un valor numérico inválido: '{valor}'."
            ) from exc

    else:
        texto = str(valor).strip()

        if not texto:
            return Decimal("0.00")

        texto = texto.replace("$", "").replace(",", "")
        texto = re.sub(r"\s+", "", texto)

        if texto in ("", "-", "-0", "-0.00", "."):
            return Decimal("0.00")

        try:
            d = Decimal(texto)
        except InvalidOperation as exc:
            raise ValueError(
                f"Fila {fila}: el campo {campo} tiene un valor numérico inválido: '{valor}'."
            ) from exc

    try:
        d = d.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(
            f"Fila {fila}: el campo {campo} no pudo convertirse a decimal: '{valor}'."
        ) from exc

    if d == Decimal("0.00"):
        return Decimal("0.00")

    if d < Decimal("0.00"):
        raise ValueError(
            f"Fila {fila}: el campo {campo} no puede ser negativo: '{valor}'."
        )

    return d


def _dec(value) -> Decimal:
    """
    Convierte un valor de base de datos a Decimal de forma segura.
    """
    try:
        return Decimal(str(value or "0.00")).quantize(
            DOS_DECIMALES,
            rounding=ROUND_HALF_UP
        )
    except Exception:
        return Decimal("0.00")


# =========================================================
# VALIDACIÓN DE FORMATO
# =========================================================

def validar_formato_excel(
    filename: Union[Path, str],
    generar_plantilla: bool = True
):
    """
    Valida que el Excel tenga el formato oficial.

    Reglas:
      - Debe existir la hoja oficial o ser un libro con una sola hoja.
      - Los encabezados deben ser exactamente iguales.
      - No se permiten columnas adicionales.
    """
    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo: {filename}")

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as exc:
        detalles = [str(exc)]
        ruta = _generar_plantilla_si_procede(path, detalles) if generar_plantilla else None
        raise FormatoExcelError(
            MENSAJE_FORMATO_NO_VALIDO,
            detalles=detalles,
            ruta_plantilla=ruta
        ) from exc

    # Selección de hoja oficial.
    if HOJA_OFICIAL in wb.sheetnames:
        ws = wb[HOJA_OFICIAL]
    elif len(wb.worksheets) == 1:
        ws = wb.worksheets[0]
    else:
        detalles = [
            f"El libro contiene {len(wb.worksheets)} hojas y no existe la hoja oficial '{HOJA_OFICIAL}'."
        ]
        ruta = _generar_plantilla_si_procede(path, detalles) if generar_plantilla else None
        raise FormatoExcelError(
            MENSAJE_FORMATO_NO_VALIDO,
            detalles=detalles,
            ruta_plantilla=ruta
        )

    detalles: List[str] = []

    # Validar columnas oficiales.
    for i, encabezado_esperado in enumerate(ENCABEZADOS_OFICIALES, start=1):
        valor = ws.cell(row=1, column=i).value
        encabezado_encontrado = str(valor).strip().upper() if valor is not None else ""

        if encabezado_encontrado != encabezado_esperado:
            detalles.append(
                f"Columna {i}: debe decir '{encabezado_esperado}' y dice '{encabezado_encontrado}'."
            )

    # Validar columnas adicionales.
    for col in range(len(ENCABEZADOS_OFICIALES) + 1, ws.max_column + 1):
        valor = ws.cell(row=1, column=col).value
        if valor is not None and str(valor).strip():
            detalles.append(
                f"Columna adicional no permitida: '{str(valor).strip()}'."
            )

    if detalles:
        ruta = _generar_plantilla_si_procede(path, detalles) if generar_plantilla else None
        raise FormatoExcelError(
            MENSAJE_FORMATO_NO_VALIDO,
            detalles=detalles,
            ruta_plantilla=ruta
        )

    return wb, ws


# =========================================================
# PARSEO OFICIAL
# =========================================================

def parse_excel_oficial(
    filename: Union[Path, str],
    generar_plantilla: bool = True
) -> Dict[str, List]:
    """
    Lee el Excel oficial y retorna:

        {
            "registros": [...],
            "sin_precio": [...]
        }

    Si hay errores de datos, lanza FormatoExcelError.
    """
    _, ws = validar_formato_excel(filename, generar_plantilla=generar_plantilla)

    registros: List[Dict] = []
    errores: List[str] = []
    claves_vistas = set()
    sin_precio: List[str] = []

    for fila in range(2, ws.max_row + 1):
        valores = [
            ws.cell(row=fila, column=col).value
            for col in range(1, len(CAMPOS_DB) + 1)
        ]

        # Renglón completamente vacío.
        if all(v is None or str(v).strip() == "" for v in valores):
            continue

        clave = normalizar_clave(valores[0])

        # Por si dentro del archivo apareciera otra vez la fila de encabezados.
        if clave == "CLAVE":
            continue

        if not clave:
            errores.append(f"Fila {fila}: falta la CLAVE.")
            continue

        if clave in claves_vistas:
            errores.append(f"Fila {fila}: la CLAVE {clave} está duplicada en el archivo.")
            continue

        claves_vistas.add(clave)

        descripcion = str(valores[1] or "").strip()
        if not descripcion:
            errores.append(f"Fila {fila}: la CLAVE {clave} no tiene DESCRIPCION.")

        try:
            largo = parsear_numero(valores[2], "LARGO", fila)
            if largo not in LARGOS_VALIDOS:
                errores.append(
                    f"Fila {fila}: el LARGO '{valores[2]}' de la CLAVE {clave} no está permitido. "
                    "Largos válidos: 3.66, 4.60, 5.00, 5.50, 5.60, 6.10."
                )
        except ValueError as exc:
            errores.append(str(exc))
            largo = Decimal("0.00")

        registro = {
            "clave": clave,
            "descripcion": descripcion,
            "largo": largo,
        }

        for idx, campo in enumerate(PRECIOS_COLS, start=3):
            try:
                registro[campo] = parsear_numero(valores[idx], campo.upper(), fila)
            except ValueError as exc:
                errores.append(str(exc))
                registro[campo] = Decimal("0.00")

        # Si el largo fue inválido, no se incorpora.
        if largo not in LARGOS_VALIDOS:
            continue

        tiene_precio = any(registro[col] > Decimal("0.00") for col in PRECIOS_COLS)

        if tiene_precio:
            registros.append(registro)
        else:
            sin_precio.append(clave)
            if INCLUIR_REGISTROS_SIN_PRECIO:
                registros.append(registro)

    if errores:
        raise FormatoExcelError(
            "El archivo tiene errores de captura. Corrige la plantilla antes de importar.",
            detalles=errores
        )

    return {
        "registros": registros,
        "sin_precio": sin_precio,
    }


def parse_excel_profilo(
    filename: Union[Path, str],
    generar_plantilla: bool = True
) -> List[Dict]:
    """
    Función compatible con llamadas anteriores.
    Retorna solo la lista de registros.
    """
    return parse_excel_oficial(
        filename,
        generar_plantilla=generar_plantilla
    )["registros"]


# =========================================================
# SINCRONIZACIÓN CON BASE DE DATOS
# =========================================================

def importar_registros(
    db,
    registros: List[Dict],
    solo_mayores: Optional[bool] = None
) -> Tuple[Dict[str, int], List[str]]:
    """
    Integra los registros a la base de datos usando el objeto DBManager.

    Reglas:
      - Si la clave no existe: INSERT completo.
      - Si la clave existe:
          * Con solo_mayores=True:
              actualiza solo precios donde Excel > BD.
          * Con solo_mayores=False:
              actualiza todos los precios.

    Retorna estadísticas y errores.
    """
    if solo_mayores is None:
        solo_mayores = ACTUALIZAR_SOLO_MAYORES

    estadisticas = {
        "insertados": 0,
        "actualizados": 0,
        "omitidos": 0,
        "errores": 0,
    }

    errores: List[str] = []

    for reg in registros:
        clave = str(reg.get("clave", "")).strip().upper()

        try:
            if not db.existe_clave(clave):
                payload = {}

                for campo in CAMPOS_DB:
                    payload[campo] = reg.get(campo)

                db.insertar_o_actualizar(payload, use_merge=True)
                estadisticas["insertados"] += 1
                continue

            actual = db.obtener_por_clave(clave) or {}

            payload = {
                "clave": clave,
            }

            descripcion = str(reg.get("descripcion") or actual.get("descripcion") or "").strip()
            largo = reg.get("largo") or _dec(actual.get("largo"))

            payload["descripcion"] = descripcion
            payload["largo"] = largo

            cambio = False

            if descripcion != str(actual.get("descripcion", "")).strip():
                cambio = True

            if _dec(largo) != _dec(actual.get("largo")):
                cambio = True

            for col in PRECIOS_COLS:
                precio_excel = _dec(reg.get(col))
                precio_bd = _dec(actual.get(col))

                if solo_mayores:
                    if precio_excel > precio_bd:
                        payload[col] = precio_excel
                        cambio = True
                    else:
                        payload[col] = precio_bd
                else:
                    if precio_excel != precio_bd:
                        payload[col] = precio_excel
                        cambio = True
                    else:
                        payload[col] = precio_bd

            if cambio:
                db.insertar_o_actualizar(payload, use_merge=True)
                estadisticas["actualizados"] += 1
            else:
                estadisticas["omitidos"] += 1

        except Exception as exc:
            estadisticas["errores"] += 1
            errores.append(f"{clave}: {exc}")

    return estadisticas, errores


def importar_desde_excel(
    filename: Optional[Union[Path, str]] = None,
    db=None,
    generar_plantilla: bool = True,
    solo_mayores: Optional[bool] = None
) -> Dict:
    """
    Función principal de importación.

    Puede usarse desde pantalla pasando el objeto DBManager:

        from materiales.aluminio.parsers.parse_excel import importar_desde_excel
        stats = importar_desde_excel(path, db=self.db)

    También puede ejecutarse de forma independiente.
    """
    archivo = Path(filename) if filename else EXCEL_FILE

    resultado = parse_excel_oficial(
        archivo,
        generar_plantilla=generar_plantilla
    )

    if db is None:
        from materiales.aluminio.db_manager import DBManager
        db = DBManager(db_name=DB_NAME)

    stats, errores = importar_registros(
        db,
        resultado["registros"],
        solo_mayores=solo_mayores
    )

    stats["sin_precio"] = len(resultado.get("sin_precio", []))
    stats["errores_detalle"] = errores

    return stats


# =========================================================
# EJECUCIÓN INDEPENDIENTE
# =========================================================

if __name__ == "__main__":
    # Permite ejecutar este archivo directamente desde Windows o consola.
    for parent in Path(__file__).resolve().parents:
        if (parent / "materiales").is_dir():
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            break

    try:
        estadisticas = importar_desde_excel()

        print("Importación terminada.")
        for clave, valor in estadisticas.items():
            if clave != "errores_detalle":
                print(f"  {clave}: {valor}")

        if estadisticas.get("errores_detalle"):
            print("\nErrores detectados:")
            for error in estadisticas["errores_detalle"][:20]:
                print(f"  - {error}")

    except FormatoExcelError as exc:
        print(str(exc))
        sys.exit(1)

    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)