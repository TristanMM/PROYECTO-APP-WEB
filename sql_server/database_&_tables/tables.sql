-- Verificar si la base de datos existe y crearla si no
IF NOT EXISTS (SELECT *
    FROM sys.databases
    WHERE name = 'BD_Okami')
BEGIN
 CREATE DATABASE BD_Okami;
END
GO

USE BD_Okami;
GO

-- 1. CREACIÓN DE TABLAS