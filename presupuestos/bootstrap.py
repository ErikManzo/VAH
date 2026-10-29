# -*- coding: utf-8 -*-
"""
Bootstrap del modulo Presupuestos.

Centraliza:
- configuracion inicial del entorno y sys.path
- inicializacion del modulo core
- logger del modulo
- deteccion y carga segura de dependencias opcionales
"""

from __future__ import annotations

import os
import sys
import warnings
from typing import Final

from common.logger_config import get_logger as _base_get_logger, setup_logger as _setup_logger

warnings.filterwarnings("ignore", category=RuntimeWarning)

CURRENT_DIR: Final[str] = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR: Final[str] = os.path.dirname(CURRENT_DIR)
REPORTS_DIR: Final[str] = os.path.join(CURRENT_DIR, "reports")


def _ensure_sys_path() -> None:
    if PARENT_DIR not in sys.path:
        sys.path.insert(0, PARENT_DIR)
    if REPORTS_DIR not in sys.path:
        sys.path.insert(0, REPORTS_DIR)


def get_logger(name: str):
    """Obtiene un logger asegurando que tenga handlers configurados."""
    return _setup_logger(name)


BOOTSTRAP_LOGGER = get_logger("presupuestos.bootstrap")


def _initialize_core_module() -> None:
    try:
        from presupuestos.core.utils import initialize_module
    except ImportError:
        try:
            from core.utils import initialize_module
        except ImportError:
            BOOTSTRAP_LOGGER.exception("No se pudo importar initialize_module")
            return

    try:
        initialize_module()
    except Exception:
        BOOTSTRAP_LOGGER.exception("Fallo initialize_module() durante el bootstrap")


_ensure_sys_path()
_initialize_core_module()

from presupuestos.core.fallbacks import (  # noqa: E402
    FallbackEspecificacionesCtx,
    FallbackGestionDiccionarioDialog,
    FallbackMessageManager,
    FallbackPresupuestoPDFService,
    FallbackService,
    FallbackTextEditConCorrector,
    fallback_dispatch_calculo,
    fallback_guard_before_add,
    fallback_habilitar_corrector_para_campos,
)

SERVICE_AVAILABLE = False
MESSAGE_MANAGER_AVAILABLE = False
PDF_GENERATOR_AVAILABLE = False
CORRECTOR_AVAILABLE = False
SPELLCHECKER_AVAILABLE = False

Service = FallbackService
EspecificacionesCtx = FallbackEspecificacionesCtx
dispatch_calculo = fallback_dispatch_calculo
guard_before_add = fallback_guard_before_add
MessageManager = FallbackMessageManager
PresupuestoPDFService = FallbackPresupuestoPDFService
TextEditConCorrector = FallbackTextEditConCorrector
habilitar_corrector_para_campos = fallback_habilitar_corrector_para_campos
GestionDiccionarioDialog = FallbackGestionDiccionarioDialog

try:
    from presupuestos.service import Service as _Service
    from presupuestos.calculators import EspecificacionesCtx as _EspecificacionesCtx, dispatch_calculo as _dispatch_calculo
    from presupuestos.rules_zero_price import guard_before_add as _guard_before_add

    Service = _Service
    EspecificacionesCtx = _EspecificacionesCtx
    dispatch_calculo = _dispatch_calculo
    guard_before_add = _guard_before_add
    SERVICE_AVAILABLE = True
    BOOTSTRAP_LOGGER.debug("Service y calculadores principales importados correctamente")
except Exception:
    BOOTSTRAP_LOGGER.exception("Error importando Service/calculadores principales; se usaran fallbacks")

try:
    from presupuestos.ui.message_manager import MessageManager as _MessageManager

    MessageManager = _MessageManager
    MESSAGE_MANAGER_AVAILABLE = True
    BOOTSTRAP_LOGGER.debug("MessageManager importado correctamente")
except Exception:
    BOOTSTRAP_LOGGER.exception("Error importando MessageManager; se usara fallback")

try:
    from presupuestos.reports.presupuesto_pdf_service import PresupuestoPDFService as _PresupuestoPDFService

    PresupuestoPDFService = _PresupuestoPDFService
    PDF_GENERATOR_AVAILABLE = True
    BOOTSTRAP_LOGGER.debug("PresupuestoPDFService importado correctamente")
except Exception:
    BOOTSTRAP_LOGGER.exception("Error importando PresupuestoPDFService; se usara fallback")

try:
    from presupuestos.reports.textedit_con_corrector import (
        GestionDiccionarioDialog as _GestionDiccionarioDialog,
        SPELLCHECKER_AVAILABLE as _SPELLCHECKER_AVAILABLE,
        TextEditConCorrector as _TextEditConCorrector,
        habilitar_corrector_para_campos as _habilitar_corrector_para_campos,
    )

    TextEditConCorrector = _TextEditConCorrector
    habilitar_corrector_para_campos = _habilitar_corrector_para_campos
    GestionDiccionarioDialog = _GestionDiccionarioDialog
    SPELLCHECKER_AVAILABLE = _SPELLCHECKER_AVAILABLE
    CORRECTOR_AVAILABLE = True
    BOOTSTRAP_LOGGER.debug("Corrector ortografico profesional importado correctamente")
    if not SPELLCHECKER_AVAILABLE:
        BOOTSTRAP_LOGGER.warning("pyspellchecker no instalado. El corrector no funcionara.")
except Exception:
    BOOTSTRAP_LOGGER.exception("Error importando corrector ortografico; se usaran fallbacks")


def setup_environment() -> None:
    """Prepara el entorno del modulo de forma idempotente."""
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    _ensure_sys_path()
    _initialize_core_module()


def is_service_available() -> bool:
    return SERVICE_AVAILABLE


def is_message_manager_available() -> bool:
    return MESSAGE_MANAGER_AVAILABLE


def is_pdf_generator_available() -> bool:
    return PDF_GENERATOR_AVAILABLE


def is_corrector_available() -> bool:
    return CORRECTOR_AVAILABLE


def is_spellchecker_available() -> bool:
    return SPELLCHECKER_AVAILABLE
