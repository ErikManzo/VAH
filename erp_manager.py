import pyodbc
import pandas as pd
from common.logger_config import get_logger

logger = get_logger("erp_manager")

class ERPManager:
    def __init__(self):
        self.server = "DESKTOP-AE60PIU\\SQLEXPRESS"
        self.modulos_disponibles = {
            'vah': 'Presupuestos',
            'clientes': 'Clientes',
            'proveedores': 'Proveedores',
            'aluminio': 'Material Aluminio',
            'vidrio': 'Material Vidrio',
            'plasticos': 'Material Plásticos',
            'herrajes': 'Material Herrajes',
            'herreria': 'Material Herrería',
            'otros': 'Otros Materiales'
        }
    
    def conectar(self, modulo):
        """Conecta a una base de datos específica"""
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={modulo};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
            f"Encrypt=yes;"
        )
        return pyodbc.connect(conn_str)
    
    def listar_tablas(self, modulo):
        """Lista todas las tablas de un módulo"""
        conn = self.conectar(modulo)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        tablas = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tablas
    
    def consultar(self, modulo, sql):
        """Ejecuta una consulta SQL y retorna DataFrame"""
        conn = self.conectar(modulo)
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    
    def listar_modulos(self):
        """Muestra los módulos disponibles"""
        print("\n📦 MÓDULOS DISPONIBLES:")
        logger.info("Listando modulos disponibles del ERP")
        for key, desc in self.modulos_disponibles.items():
            print(f"   • {key}: {desc}")
            logger.info("Modulo disponible: %s -> %s", key, desc)
