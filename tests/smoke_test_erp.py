import importlib
import os
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from PyQt6.QtWidgets import QApplication, QWidget

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from common.logger_config import get_logger

logger = get_logger("tests.smoke_test")

SHOW_SECONDS = 2.0
PROCESS_GRACE_SECONDS = 2.0


@dataclass
class SmokeCase:
    name: str
    module_path: str
    class_name: Optional[str] = None
    file_path: Optional[str] = None


CASES: List[SmokeCase] = [
    SmokeCase(
        name="Presupuestos",
        module_path="presupuestos.modulo_presupuestos",
        class_name="PresupuestosWindow",
        file_path=str(ROOT / "presupuestos" / "modulo_presupuestos.py"),
    ),
    SmokeCase(
        name="Clientes",
        module_path="clientes.art.pantalla_clientes",
        class_name="RegistroClientes",
        file_path=str(ROOT / "clientes" / "main.py"),
    ),
    SmokeCase(
        name="Proveedores",
        module_path="proveedores.art.pantalla_proveedores",
        class_name="PantallaProveedores",
        file_path=str(ROOT / "proveedores" / "main.py"),
    ),
    SmokeCase(
        name="CXC",
        module_path="cxc.art.pantalla_cxc",
        class_name="PantallaCxc",
        file_path=str(ROOT / "cxc" / "main.py"),
    ),
    SmokeCase(
        name="Concentrador Materiales",
        module_path="concentrador_materiales.ui.pantalla_concentrador",
        class_name="PantallaConcentrador",
        file_path=str(ROOT / "concentrador_materiales" / "ui" / "pantalla_concentrador.py"),
    ),
    SmokeCase(
        name="Materiales Aluminio",
        module_path="materiales.aluminio.pantalla_materiales_aluminio",
        class_name="PantallaMaterialesAluminio",
        file_path=str(ROOT / "materiales" / "aluminio" / "pantalla_materiales_aluminio.py"),
    ),
    SmokeCase(
        name="Materiales Herrajes",
        module_path="materiales.herrajes.pantalla_herrajes",
        class_name="PantallaHerrajes",
        file_path=str(ROOT / "materiales" / "herrajes" / "pantalla_herrajes.py"),
    ),
    SmokeCase(
        name="Materiales Herreria",
        module_path="materiales.herreria.pantalla_herreria",
        class_name="PantallaHerreria",
        file_path=str(ROOT / "materiales" / "herreria" / "pantalla_herreria.py"),
    ),
    SmokeCase(
        name="Materiales Otros",
        module_path="materiales.otros.pantalla_otros",
        class_name="PantallaOtros",
        file_path=str(ROOT / "materiales" / "otros" / "pantalla_otros.py"),
    ),
    SmokeCase(
        name="Materiales Plasticos",
        module_path="materiales.plasticos.pantalla_plasticos",
        class_name="PantallaPlasticos",
        file_path=str(ROOT / "materiales" / "plasticos" / "pantalla_plasticos.py"),
    ),
    SmokeCase(
        name="Materiales Vidrio",
        module_path="materiales.vidrio.pantalla_vidrio",
        class_name="PantallaVidrio",
        file_path=str(ROOT / "materiales" / "vidrio" / "pantalla_vidrio.py"),
    ),
    SmokeCase(
        name="Paquetes Aluminio",
        module_path="paquetes.aluminio.pantalla_paquete_aluminio",
        class_name="PaquetesAluminioUI",
        file_path=str(ROOT / "paquetes" / "aluminio" / "pantalla_paquete_aluminio.py"),
    ),
    SmokeCase(
        name="Paquetes Herrajes",
        module_path="paquetes.herrajes.pantalla_paquete_herrajes",
        class_name="PaqueteHerrajesUI",
        file_path=str(ROOT / "paquetes" / "herrajes" / "pantalla_paquete_herrajes.py"),
    ),
]


def process_events(app: QApplication, seconds: float) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.05)


def close_all_top_level_widgets(app: QApplication) -> None:
    for widget in list(app.topLevelWidgets()):
        try:
            widget.close()
        except Exception:
            logger.debug("No se pudo cerrar widget residual", exc_info=True)
    app.processEvents()


def run_import_case(case: SmokeCase, app: QApplication) -> str:
    logger.info("Probando %s por import directo: %s.%s", case.name, case.module_path, case.class_name)
    module = importlib.import_module(case.module_path)
    if not case.class_name:
        raise RuntimeError(f"{case.name} no tiene class_name configurado")
    window_class = getattr(module, case.class_name)
    window = window_class()
    if not isinstance(window, QWidget):
        raise TypeError(f"{case.name} no devolvio un QWidget: {type(window)!r}")

    try:
        window.show()
        app.processEvents()
        process_events(app, SHOW_SECONDS)
        window.close()
        app.processEvents()
        process_events(app, 0.2)
        logger.info("%s OK por import directo", case.name)
        return "OK (import)"
    finally:
        close_all_top_level_widgets(app)


def terminate_process(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=PROCESS_GRACE_SECONDS)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=PROCESS_GRACE_SECONDS)


def run_subprocess_case(case: SmokeCase) -> str:
    if not case.file_path:
        raise RuntimeError(f"{case.name} no tiene file_path configurado para fallback")

    logger.info("Probando %s por subprocess: %s", case.name, case.file_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    proc = subprocess.Popen(
        [sys.executable, case.file_path],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    try:
        time.sleep(SHOW_SECONDS)
        rc = proc.poll()
        if rc is None:
            logger.info("%s OK por subprocess (permanece abierto tras %ss)", case.name, SHOW_SECONDS)
            return "OK (subprocess)"

        stdout, stderr = proc.communicate(timeout=1)
        detail = (stdout or "") + ("\n" if stdout and stderr else "") + (stderr or "")
        if rc == 0:
            logger.info("%s OK por subprocess (termino antes del timeout, rc=0)", case.name)
            return "OK (subprocess rc=0)"
        raise RuntimeError(f"Subprocess termino con rc={rc}. Salida:\n{detail.strip()}")
    finally:
        terminate_process(proc)


def test_case(case: SmokeCase, app: QApplication) -> dict:
    logger.info("=== Inicio smoke test: %s ===", case.name)
    try:
        if case.class_name:
            try:
                status = run_import_case(case, app)
                return {"name": case.name, "passed": True, "status": status}
            except Exception as import_error:
                logger.exception("%s fallo por import directo", case.name)
                if not case.file_path:
                    raise import_error
                logger.info("%s intentara fallback por subprocess", case.name)
                status = run_subprocess_case(case)
                return {"name": case.name, "passed": True, "status": status}

        status = run_subprocess_case(case)
        return {"name": case.name, "passed": True, "status": status}
    except Exception as exc:
        logger.exception("%s FALLO en smoke test", case.name)
        return {
            "name": case.name,
            "passed": False,
            "status": f"FALLO: {exc}",
            "traceback": traceback.format_exc(),
        }
    finally:
        logger.info("=== Fin smoke test: %s ===", case.name)


def main() -> int:
    os.chdir(ROOT)
    logger.info("Iniciando smoke test ERP desde %s", ROOT)

    app = QApplication.instance() or QApplication([])
    results = []
    for case in CASES:
        results.append(test_case(case, app))

    passed = sum(1 for item in results if item["passed"])
    total = len(results)

    print("")
    print("Resumen Smoke Test ERP")
    print("=" * 60)
    for item in results:
        print(f"- {item['name']}: {item['status']}")
    print("=" * 60)
    print(f"{passed} de {total} modulos pasaron el smoke test")

    logger.info("Smoke test finalizado: %s de %s modulos OK", passed, total)
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
