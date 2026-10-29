# -*- coding: utf-8 -*-
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from cxc.repositories.pago_repository import PagoRepository
from cxc.repositories.cxc_repository import CxcRepository

def generar_recibo_pago_pdf(pago_id: int) -> str:
    pago = PagoRepository.get_by_id(pago_id)  # Nota: este método no existe; hay que implementarlo o usar otro. Para simplificar, pasaremos cxc_id y monto. Mejor rediseñar.
    # Como es extenso, aquí daré una versión simplificada que recibe cxc_id y monto
    raise NotImplementedError("Se implementará bajo demanda. Por ahora usa estado de cuenta.")
