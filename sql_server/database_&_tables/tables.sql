-- 1. CREACIÓN DE LA BASE DE DATOS
CREATE DATABASE BD_Okamifit
GO

USE BD_Okamifit
GO

-- 2. CREACIÓN DE TABLAS BASE (SIN DEPENDENCIAS DE OTRAS TABLAS)

-- Tabla de Usuarios
CREATE TABLE USUARIOS (
    idUsuario INT IDENTITY(1,1) PRIMARY KEY,
    nombreUsuario NVARCHAR(50) NOT NULL UNIQUE,
    hashPassword VARBINARY(MAX) NOT NULL,
    rol NVARCHAR(50) NOT NULL,
	esBorrado BIT NOT NULL DEFAULT 0
)
GO

-- Tabla de Categorías (referenciada por PRODUCTOS)
CREATE TABLE CATEGORIAS (
    idCategoria INT IDENTITY(1,1) PRIMARY KEY,
    nombreCategoria NVARCHAR(50) NOT NULL,
	esBorrado BIT NOT NULL DEFAULT 0
)
GO

-- Tabla de Variantes (referenciada por STOCK_VARIANTE)
CREATE TABLE VARIANTES (
    idVariante INT IDENTITY(1,1) PRIMARY KEY,
    Presentacion NVARCHAR(50) NOT NULL,
	Contenido NVARCHAR(50),
	Sabor NVARCHAR(50),
	esBorrado BIT NOT NULL DEFAULT 0
)
GO


-- 3. CREACIÓN DE TABLAS CON CLAVES FORÁNEAS SIMPLES

-- Tabla de Productos (depende de CATEGORIAS)
CREATE TABLE PRODUCTOS (
    idProducto INT IDENTITY(1,1) PRIMARY KEY,
    nombre NVARCHAR(100) NOT NULL,
    precioBase INT NOT NULL,
    descripcion NVARCHAR(MAX),
    enOferta BIT DEFAULT 0,
    idCategoria INT NOT NULL,
	esBorrado BIT NOT NULL DEFAULT 0,
	urlImagen NVARCHAR(MAX) NOT NULL,
    FOREIGN KEY (idCategoria) REFERENCES CATEGORIAS(idCategoria)
)
GO

-- Tabla de Sesiones (depende de USUARIOS)
CREATE TABLE SESIONES (
 id_sesion INT IDENTITY(1,1) PRIMARY KEY,
 id_usuario INT NOT NULL,
 token VARCHAR(255) NOT NULL UNIQUE,
 fecha_inicio DATETIME DEFAULT GETDATE(),
 fecha_expiracion DATETIME,
 CONSTRAINT FK_sesiones_usuario FOREIGN KEY (id_usuario) REFERENCES USUARIOS(idUsuario)
)
GO

-- 4. CREACIÓN DE TABLAS DE UNIÓN/MUCHOS A MUCHOS

-- Tabla de Stock por Variante (depende de PRODUCTOS y VARIANTES)
CREATE TABLE STOCK_VARIANTE (
    idProducto INT NOT NULL,
    idVariante INT NOT NULL,
    cantidadStock INT NOT NULL,
    PRIMARY KEY(idProducto, idVariante),
    FOREIGN KEY(idProducto) REFERENCES PRODUCTOS(idProducto),
    FOREIGN KEY(idVariante) REFERENCES VARIANTES(idVariante)
)
GO

-- 5. CONSULTA FINAL (solo para verificar)
SELECT * FROM PRODUCTOS
GO