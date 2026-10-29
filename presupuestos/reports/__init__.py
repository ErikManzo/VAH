# -*- coding: utf-8 -*-
"""
D:/vah/presupuestos/reports/__init__.py
"""

# ============================================================================
# CORRECTOR ORTOGRÁFICO
# ============================================================================
from .textedit_con_corrector import (
    TextEditConCorrector,
    habilitar_corrector_para_campos,
    GestionDiccionarioDialog,
    SPELLCHECKER_AVAILABLE,
    DiccionarioPersonalizado
)

# ============================================================================
# GENERADOR PDF
# ============================================================================
try:
    from .pdf_generator import GeneradorPresupuestoPDF, generar_presupuesto_pdf
    from .pdf_models import DatosPresupuesto, PartidaPresupuesto, TotalesPresupuesto

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


    class GeneradorPresupuestoPDF:
        def __init__(self, *args, **kwargs): pass

        def generar_pdf(self, *args, **kwargs): return False


    class DatosPresupuesto:
        def __init__(self, **kwargs): pass


    class PartidaPresupuesto:
        def __init__(self, **kwargs): pass


    class TotalesPresupuesto:
        def __init__(self, **kwargs): pass


    def generar_presupuesto_pdf(*args, **kwargs):
        return False

# ============================================================================
# SERVICIO DE IMPRESIÓN
# ============================================================================
try:
    from .presupuesto_pdf_service import PresupuestoPDFService, generar_pdf_presupuesto

    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False


    class PresupuestoPDFService:
        def __init__(self, *args, **kwargs): pass

        def generar_pdf_desde_id(self, *args, **kwargs): return None


    def generar_pdf_presupuesto(*args, **kwargs):
        return None

# ============================================================================
# EXPORTACIÓN
# ============================================================================
__all__ = [
    'TextEditConCorrector',
    'habilitar_corrector_para_campos',
    'GestionDiccionarioDialog',
    'SPELLCHECKER_AVAILABLE',
    'DiccionarioPersonalizado',
    'GeneradorPresupuestoPDF',
    'generar_presupuesto_pdf',
    'DatosPresupuesto',
    'PartidaPresupuesto',
    'TotalesPresupuesto',
    'PresupuestoPDFService',
    'generar_pdf_presupuesto',
    'PDF_AVAILABLE',
    'SERVICE_AVAILABLE'
]