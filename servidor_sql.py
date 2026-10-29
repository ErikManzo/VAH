import asyncio
import pyodbc
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from common.logger_config import get_logger

logger = get_logger("servidor_sql")

# Configuración de conexión
SERVER = "DESKTOP-AE60PIU\\SQLEXPRESS"
DATABASE = "vah"
CONN_STR = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    f"Trusted_Connection=yes;"
    f"TrustServerCertificate=yes;"
    f"Encrypt=yes;"
)

# Crear servidor
server = Server("sqlserver-erp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="consultar",
            description="Ejecuta una consulta SQL en la base de datos",
            inputSchema={
                "type": "object",
                "properties": {
                    "consulta": {
                        "type": "string",
                        "description": "La consulta SQL a ejecutar",
                    }
                },
                "required": ["consulta"],
            },
        ),
        types.Tool(
            name="listar_tablas",
            description="Muestra todas las tablas de la base de datos",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="estructura_tabla",
            description="Muestra la estructura de una tabla específica",
            inputSchema={
                "type": "object",
                "properties": {
                    "tabla": {
                        "type": "string",
                        "description": "Nombre de la tabla",
                    }
                },
                "required": ["tabla"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        conn = pyodbc.connect(CONN_STR)
        cursor = conn.cursor()
        
        if name == "listar_tablas":
            cursor.execute("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            tablas = cursor.fetchall()
            resultado = "📋 TABLAS DISPONIBLES:\n" + "-"*30 + "\n"
            for tabla in tablas:
                resultado += f"   • {tabla[0]}\n"
                
        elif name == "estructura_tabla":
            tabla = arguments.get("tabla")
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """, (tabla,))
            columnas = cursor.fetchall()
            
            resultado = f"📁 ESTRUCTURA DE TABLA: {tabla}\n" + "-"*40 + "\n"
            for col in columnas:
                nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                resultado += f"   • {col[0]}: {col[1]} ({nullable})\n"
                
        elif name == "consultar":
            consulta = arguments.get("consulta")
            cursor.execute(consulta)
            
            if consulta.strip().upper().startswith("SELECT"):
                columnas = [desc[0] for desc in cursor.description]
                filas = cursor.fetchall()
                
                resultado = f"📊 RESULTADOS ({len(filas)} filas):\n" + "-"*50 + "\n"
                resultado += " | ".join(columnas) + "\n"
                resultado += "-"*50 + "\n"
                
                for fila in filas[:15]:
                    valores = []
                    for valor in fila:
                        if valor is None:
                            valores.append("NULL")
                        elif isinstance(valor, (int, float)):
                            valores.append(str(valor))
                        else:
                            valores.append(str(valor)[:30])
                    resultado += " | ".join(valores) + "\n"
                    
                if len(filas) > 15:
                    resultado += f"... y {len(filas)-15} filas más\n"
            else:
                conn.commit()
                resultado = f"✅ Consulta ejecutada. Filas afectadas: {cursor.rowcount}"
        
        conn.close()
        return [types.TextContent(type="text", text=resultado)]
        
    except Exception as e:
        logger.exception("Error en herramienta MCP SQL Server")
        return [types.TextContent(type="text", text=f"❌ ERROR: {str(e)}")]

async def main():
    print("🚀 Servidor SQL Server MCP iniciado")
    print(f"📁 Base de datos: {DATABASE}")
    print(f"🖥️  Servidor: {SERVER}")
    print("-" * 40)
    logger.info("Servidor SQL Server MCP iniciado para database=%s server=%s", DATABASE, SERVER)
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="sqlserver-erp",
                server_version="1.0.0",
                capabilities={}  # <-- Campo requerido añadido
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
