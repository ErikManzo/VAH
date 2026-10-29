# -*- coding: utf-8 -*-
import json
import os
from typing import Dict, Any, Optional
from common.app_paths import get_app_root
from common.logger_config import get_logger

CONFIG_PATH = os.path.join(get_app_root(), "config.json")
logger = get_logger("presupuestos.services.config_service")

DEFAULT_CORREO_REMITENTE = "ventanasdealuminioyherreria@hotmail.com"
DEFAULT_SERVIDOR_SMTP = "smtp.office365.com"
DEFAULT_PUERTO_SMTP = 587

class ConfigService:
    def __init__(self, db_service):
        self.db = db_service

    def _leer_config_json(self) -> Dict[str, Any]:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _guardar_config_json(self, config: Dict[str, Any]) -> None:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def obtener_clave_admin(self) -> Optional[str]:
        """Obtiene la clave de administrador desde config.json"""
        try:
            config = self._leer_config_json()
            clave = (config.get("clave_admin") or "").strip()
            if not clave:
                logger.warning("No hay clave_admin configurada en config.json")
                return None
            return clave
        except Exception as e:
            logger.warning("Error leyendo clave_admin desde config.json: %s", e)
        return None

    def cambiar_clave_admin(self, nueva_clave: str) -> bool:
        """Cambia la clave de administrador en config.json"""
        try:
            nueva_clave = (nueva_clave or "").strip()
            if not nueva_clave:
                logger.warning("Se intento guardar una clave_admin vacia")
                return False
            config = self._leer_config_json()
            config['clave_admin'] = nueva_clave
            self._guardar_config_json(config)
            return True
        except Exception as e:
            logger.warning("Error cambiando clave_admin: %s", e)
            return False

    def obtener_numero_presupuesto_inicial(self) -> int:
        """Obtiene el número inicial de presupuesto desde config.json"""
        try:
            config = self._leer_config_json()
            return int(config.get('numero_presupuesto_inicial', 1))
        except Exception as e:
            logger.warning("Error leyendo numero_presupuesto_inicial: %s", e)
            return 1

    def cambiar_numero_presupuesto_inicial(self, nuevo_numero: int) -> bool:
        """Cambia el número inicial de presupuesto en config.json"""
        try:
            config = self._leer_config_json()
            config['numero_presupuesto_inicial'] = int(nuevo_numero)
            self._guardar_config_json(config)
            return True
        except Exception as e:
            logger.warning("Error cambiando numero_presupuesto_inicial: %s", e)
            return False

    def obtener_configuracion_correo(self) -> Optional[Dict[str, Any]]:
        """Obtiene la configuracion de correo sin usar secretos hardcodeados."""
        try:
            config = self._leer_config_json()
            correo = (config.get("correo_remitente") or "").strip()
            contrasena = config.get("contrasena_correo") or ""
            servidor = (config.get("servidor_smtp") or "").strip()
            puerto = config.get("puerto_smtp")
            if not any([correo, contrasena, servidor, puerto]):
                logger.warning("No hay configuracion de correo definida en config.json")
                return None
            return {
                "correo_remitente": correo,
                "contrasena_correo": contrasena,
                "servidor_smtp": servidor,
                "puerto_smtp": int(puerto) if puerto not in (None, "") else DEFAULT_PUERTO_SMTP,
            }
        except Exception as e:
            logger.warning("Error leyendo configuracion de correo desde config.json: %s", e)
            return None

    def guardar_configuracion_correo(self, config_correo: Dict[str, Any]) -> bool:
        """Guarda configuracion de correo validando campos minimos."""
        correo = (config_correo.get("correo_remitente") or "").strip()
        contrasena = config_correo.get("contrasena_correo") or ""
        servidor = (config_correo.get("servidor_smtp") or "").strip()
        puerto = config_correo.get("puerto_smtp")
        if not correo or "@" not in correo:
            logger.warning("Se intento guardar configuracion de correo sin remitente valido")
            return False
        if not contrasena:
            logger.warning("Se intento guardar configuracion de correo sin contrasena")
            return False
        if not servidor:
            logger.warning("Se intento guardar configuracion de correo sin servidor SMTP")
            return False
        try:
            puerto = int(puerto)
        except (TypeError, ValueError):
            logger.warning("Se intento guardar configuracion de correo con puerto invalido: %s", puerto)
            return False
        if puerto <= 0:
            logger.warning("Se intento guardar configuracion de correo con puerto no positivo: %s", puerto)
            return False
        try:
            config = self._leer_config_json()
            config.update(
                {
                    "correo_remitente": correo,
                    "contrasena_correo": contrasena,
                    "servidor_smtp": servidor,
                    "puerto_smtp": puerto,
                }
            )
            self._guardar_config_json(config)
            return True
        except Exception as e:
            logger.warning("Error guardando configuracion de correo en config.json: %s", e)
            return False

    def obtener_parametros_sistema(self) -> Dict[str, Any]:
        sql = """
            SELECT correo_remitente, contrasena_correo, servidor_smtp, puerto_smtp, 
                   numero_inicial_presupuesto, color_global_defecto, 
                   desperdicio_defecto, fv_defecto, iva_porcentaje
            FROM [presupuestos].dbo.parametros_sistema WHERE id = 1
        """
        try:
            row = self.db.fetchone(sql, [])
            if row:
                correo_cfg = self.obtener_configuracion_correo() or {}
                return {
                    'correo_remitente': row[0] or correo_cfg.get("correo_remitente", DEFAULT_CORREO_REMITENTE),
                    'contrasena_correo': row[1] or correo_cfg.get("contrasena_correo", ""),
                    'servidor_smtp': row[2] or correo_cfg.get("servidor_smtp", DEFAULT_SERVIDOR_SMTP),
                    'puerto_smtp': row[3] or correo_cfg.get("puerto_smtp", DEFAULT_PUERTO_SMTP),
                    'numero_inicial_presupuesto': row[4] or 1,
                    'color_global_defecto': row[5] or 'VARIOS',
                    'desperdicio_defecto': row[6] if row[6] is not None else 2.0,
                    'fv_defecto': row[7] if row[7] is not None else 25.0,
                    'iva_porcentaje': row[8] if row[8] is not None else 16.0
                }
        except Exception as e:
            logger.warning("No se pudieron leer parametros_sistema desde la BD: %s", e)
        correo_cfg = self.obtener_configuracion_correo() or {}
        return {
            'correo_remitente': correo_cfg.get("correo_remitente", DEFAULT_CORREO_REMITENTE),
            'contrasena_correo': correo_cfg.get("contrasena_correo", ""),
            'servidor_smtp': correo_cfg.get("servidor_smtp", DEFAULT_SERVIDOR_SMTP),
            'puerto_smtp': correo_cfg.get("puerto_smtp", DEFAULT_PUERTO_SMTP),
            'numero_inicial_presupuesto': self.obtener_numero_presupuesto_inicial(),
            'color_global_defecto': 'VARIOS',
            'desperdicio_defecto': 2.0,
            'fv_defecto': 25.0,
            'iva_porcentaje': 16.0
        }

    def guardar_parametros_sistema(self, p: Dict[str, Any]) -> bool:
        sql = """
            UPDATE [presupuestos].dbo.parametros_sistema
            SET correo_remitente = ?, contrasena_correo = ?, servidor_smtp = ?, 
                puerto_smtp = ?, numero_inicial_presupuesto = ?, 
                color_global_defecto = ?, desperdicio_defecto = ?, fv_defecto = ?, iva_porcentaje = ?
            WHERE id = 1
        """
        try:
            with self.db.cursor() as cur:
                cur.execute(sql, (
                    p.get('correo_remitente'), p.get('contrasena_correo'),
                    p.get('servidor_smtp'), p.get('puerto_smtp'),
                    p.get('numero_inicial_presupuesto'),
                    p.get('color_global_defecto', 'VARIOS'),
                    p.get('desperdicio_defecto', 2.0),
                    p.get('fv_defecto', 25.0),
                    p.get('iva_porcentaje', 16.0)
                ))
                cur.commit()
                correo_data = {
                    "correo_remitente": p.get("correo_remitente", ""),
                    "contrasena_correo": p.get("contrasena_correo", ""),
                    "servidor_smtp": p.get("servidor_smtp", ""),
                    "puerto_smtp": p.get("puerto_smtp", 0),
                }
                if any(correo_data.values()) and not self.guardar_configuracion_correo(correo_data):
                    logger.warning("No se pudo persistir la configuracion de correo en config.json despues del guardado en BD")
                return True
        except Exception as e:
            logger.warning("Fallo guardando parametros_sistema completos; se intentara fallback basico: %s", e)
            # Fallback a actualización básica si fallan las nuevas columnas
            sql_basic = """
                UPDATE [presupuestos].dbo.parametros_sistema
                SET correo_remitente = ?, contrasena_correo = ?, servidor_smtp = ?, 
                    puerto_smtp = ?, numero_inicial_presupuesto = ?
                WHERE id = 1
            """
            with self.db.cursor() as cur:
                cur.execute(sql_basic, (
                    p.get('correo_remitente'), p.get('contrasena_correo'),
                    p.get('servidor_smtp'), p.get('puerto_smtp'),
                    p.get('numero_inicial_presupuesto')
                ))
                cur.commit()
                correo_data = {
                    "correo_remitente": p.get("correo_remitente", ""),
                    "contrasena_correo": p.get("contrasena_correo", ""),
                    "servidor_smtp": p.get("servidor_smtp", ""),
                    "puerto_smtp": p.get("puerto_smtp", 0),
                }
                if any(correo_data.values()) and not self.guardar_configuracion_correo(correo_data):
                    logger.warning("No se pudo persistir la configuracion de correo en config.json tras fallback basico")
                return True

    def guardar_configuracion_presupuesto(self, pid: int, n: str, fp: str, pe: str,
                                          descuento: Optional[float] = None) -> bool:
        """
        Guarda notas, forma de pago y plazo de entrega del presupuesto.
        NUEVO: si 'descuento' no es None, también persiste descuento_porcentaje
        (si es None, NO toca la columna: lo que no se envía, no se modifica).
        """
        if descuento is None:
            sql = "UPDATE [presupuestos].dbo.presupuestos SET notas = ?, forma_pago = ?, plazo_entrega = ? WHERE id = ?"
            params = (n, fp, pe, pid)
        else:
            sql = ("UPDATE [presupuestos].dbo.presupuestos "
                   "SET notas = ?, forma_pago = ?, plazo_entrega = ?, descuento_porcentaje = ? WHERE id = ?")
            params = (n, fp, pe, descuento, pid)
        with self.db.cursor() as cur:
            cur.execute(sql, params)
            cur.commit()
            return True

    def obtener_configuracion_presupuesto(self, pid: int) -> Dict[str, Any]:
        """
        NUEVO: también devuelve descuento_porcentaje (0.0 si NULL).
        """
        sql = ("SELECT notas, forma_pago, plazo_entrega, descuento_porcentaje "
               "FROM [presupuestos].dbo.presupuestos WHERE id = ?")
        row = self.db.fetchone(sql, [pid])
        if row:
            try:
                descuento = float(row[3]) if row[3] is not None else 0.0
            except (TypeError, ValueError):
                descuento = 0.0
            return {'notas': row[0] or '', 'forma_pago': row[1] or '',
                    'plazo_entrega': row[2] or '', 'descuento_porcentaje': descuento}
        return {'notas': '', 'forma_pago': '', 'plazo_entrega': '', 'descuento_porcentaje': 0.0}