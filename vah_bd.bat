@echo off
setlocal enabledelayedexpansion

set "SERVIDOR=DESKTOP-AE60PIU\SQLEXPRESS"
set "ARCHIVO_SALIDA=vah_bd.txt"

echo Generando estructura de la base de datos...
echo Por favor espere...

:: Crear archivo temporal con la consulta SQL
set "SQL_TEMP=%TEMP%\temp_query.sql"

> "%SQL_TEMP%" (
    echo USE master;
    echo GO
    echo DECLARE @dbName NVARCHAR(128^)
    echo DECLARE @sql NVARCHAR(MAX^)
    echo 
    echo DECLARE db_cursor CURSOR FOR
    echo     SELECT name FROM sys.databases
    echo     WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb', 'Distribution')
    echo     ORDER BY name
    echo 
    echo OPEN db_cursor
    echo FETCH NEXT FROM db_cursor INTO @dbName
    echo 
    echo WHILE @@FETCH_STATUS = 0
    echo BEGIN
    echo     PRINT '==================================================='
    echo     PRINT 'BASE DE DATOS: ' + @dbName
    echo     PRINT '==================================================='
    echo     PRINT ''
    echo     
    echo     SET @sql = '
    echo     USE [' + @dbName + ']
    echo     SELECT 
    echo         ''>>TABLA: '' + TABLE_NAME,
    echo         ''   >>CAMPO: '' + COLUMN_NAME,
    echo         ''      >>TIPO: '' + DATA_TYPE + 
    echo         CASE 
    echo             WHEN CHARACTER_MAXIMUM_LENGTH IS NOT NULL AND CHARACTER_MAXIMUM_LENGTH > 0 
    echo                 AND CHARACTER_MAXIMUM_LENGTH <> -1
    echo             THEN ''('' + CAST(CHARACTER_MAXIMUM_LENGTH AS VARCHAR^) + '')''
    echo             WHEN CHARACTER_MAXIMUM_LENGTH = -1 THEN ''(MAX)''
    echo             WHEN DATA_TYPE IN (''decimal'', ''numeric'') 
    echo                 AND NUMERIC_PRECISION IS NOT NULL
    echo             THEN ''('' + CAST(NUMERIC_PRECISION AS VARCHAR^) + '','' + 
    echo                  CAST(NUMERIC_SCALE AS VARCHAR^) + '')''
    echo             ELSE ''''
    echo         END,
    echo         ''      >>NULO: '' + 
    echo         CASE WHEN IS_NULLABLE = ''YES'' THEN ''SI'' ELSE ''NO'' END,
    echo         ''      >>PK: '' + 
    echo         ISNULL((SELECT ''SI'' 
    echo                  FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
    echo                  JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
    echo                  ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
    echo                  WHERE tc.CONSTRAINT_TYPE = ''PRIMARY KEY''
    echo                  AND tc.TABLE_NAME = cols.TABLE_NAME
    echo                  AND kcu.COLUMN_NAME = cols.COLUMN_NAME), ''NO'')
    echo     FROM INFORMATION_SCHEMA.COLUMNS cols
    echo     ORDER BY TABLE_NAME, ORDINAL_POSITION
    echo     '
    echo     
    echo     EXEC sp_executesql @sql
    echo     
    echo     FETCH NEXT FROM db_cursor INTO @dbName
    echo END
    echo 
    echo CLOSE db_cursor
    echo DEALLOCATE db_cursor
)

:: Ejecutar la consulta
sqlcmd -S "%SERVIDOR%" -E -i "%SQL_TEMP%" -o "%ARCHIVO_SALIDA%" -W

:: Verificar si se generó correctamente
if exist "%ARCHIVO_SALIDA%" (
    echo.
    echo ===================================================
    echo Archivo generado: %ARCHIVO_SALIDA%
    echo ===================================================
    
    :: Mostrar primeras lineas como verificacion
    echo.
    echo Vista previa de las primeras lineas:
    echo -------------------------------------
    type "%ARCHIVO_SALIDA%" | findstr /n "^" | findstr "^[1-9][0-9]*:" | more +1
) else (
    echo.
    echo [ERROR] No se pudo generar el archivo.
    echo.
    echo Verificando conexion a SQL Server...
    sqlcmd -S "%SERVIDOR%" -E -Q "SELECT @@VERSION" -W
    if errorlevel 1 (
        echo [ERROR] No se pudo conectar a SQL Server.
        echo Revise que el servidor este en ejecucion y tenga permisos.
    ) else (
        echo [ERROR] Conexion exitosa pero la consulta fallo.
        echo Revise las permisos de las bases de datos.
    )
)

:: Limpiar archivo temporal
if exist "%SQL_TEMP%" del "%SQL_TEMP%"

echo.
pause