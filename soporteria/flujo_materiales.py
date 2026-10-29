import os
from graphviz import Digraph

# Forzar a Python a reconocer Graphviz aunque el IDE no refresque PATH
os.environ["PATH"] += os.pathsep + r"C:\Program Files\Graphviz\bin"

# Crear el diagrama de flujo
dot = Digraph(comment="Flujo de botones - Módulo Materiales de Aluminio")
dot.attr(rankdir="TB", size="8")

# Nodos principales (botones)
dot.node("A", "Guardar", shape="rectangle", style="filled", fillcolor="lightblue")
dot.node("B", "Editar", shape="rectangle", style="filled", fillcolor="lightblue")
dot.node("C", "Eliminar", shape="rectangle", style="filled", fillcolor="lightblue")
dot.node("D", "Refresh", shape="rectangle", style="filled", fillcolor="lightblue")
dot.node("E", "Imprimir", shape="rectangle", style="filled", fillcolor="lightblue")
dot.node("F", "Importar", shape="rectangle", style="filled", fillcolor="lightblue")
dot.node("G", "Salir", shape="rectangle", style="filled", fillcolor="lightblue")

# Decisiones
dot.node("C1", "¿Confirmar eliminación?", shape="diamond", style="filled", fillcolor="yellow")
dot.node("E1", "¿Existen registros?", shape="diamond", style="filled", fillcolor="yellow")
dot.node("F1", "¿Archivo válido (Excel/PDF)?", shape="diamond", style="filled", fillcolor="yellow")
dot.node("F3", "¿Duplicados en BD?", shape="diamond", style="filled", fillcolor="yellow")

# Procesos normales
dot.node("C2", "Registro eliminado", shape="parallelogram", style="filled", fillcolor="lightgreen")
dot.node("C3", "Cancelado", shape="parallelogram", style="filled", fillcolor="lightgreen")
dot.node("E2", "Generar PDF\n(formato carta, cabecera, tabla)", shape="parallelogram", style="filled", fillcolor="lightgreen")
dot.node("E3", "Mostrar mensaje:\n'No hay datos'", shape="parallelogram", style="filled", fillcolor="orange")
dot.node("F2", "Convertir datos a Decimal,\nfiltrar blacklist", shape="parallelogram", style="filled", fillcolor="lightgreen")
dot.node("F4", "Insertar en SQL Server", shape="parallelogram", style="filled", fillcolor="lightgreen")
dot.node("F5", "Ignorar duplicados", shape="parallelogram", style="filled", fillcolor="orange")

# Errores
dot.node("F6", "Error: archivo inválido", shape="parallelogram", style="filled", fillcolor="red")

# Relaciones
dot.edge("C", "C1")
dot.edge("C1", "C2", label="Sí")
dot.edge("C1", "C3", label="No")

dot.edge("E", "E1")
dot.edge("E1", "E2", label="Sí")
dot.edge("E1", "E3", label="No")

dot.edge("F", "F1")
dot.edge("F1", "F2", label="Sí")
dot.edge("F1", "F6", label="No")
dot.edge("F2", "F3")
dot.edge("F3", "F4", label="No")
dot.edge("F3", "F5", label="Sí")

# Exportar a PDF y SVG
dot.render("flujo_materiales_aluminio", format="pdf", cleanup=True)
dot.render("flujo_materiales_aluminio", format="svg", cleanup=True)

print("✅ Diagramas generados: flujo_materiales_aluminio.pdf y flujo_materiales_aluminio.svg")
