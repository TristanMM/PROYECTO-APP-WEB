Use BD_Okamifit
GO

INSERT INTO USUARIOS (nombreUsuario, hashPassword, rol) VALUES
('admin_gym', HASHBYTES('SHA2_256', 'AdminSuple2025'), 'Administrador'),
('entrenador_fit', HASHBYTES('SHA2_256', 'fitlife123'), 'Vendedor'),
('cliente_fuerte', HASHBYTES('SHA2_256', 'clientef456'), 'Cliente'),
('nutri_health', HASHBYTES('SHA2_256', 'nutricion!'), 'Vendedor'),
('bodybuilder88', HASHBYTES('SHA2_256', 'gainzpass'), 'Cliente');

GO



INSERT INTO CATEGORIAS (nombreCategoria) VALUES
('Proteínas'),
('Creatinas'),
('Pre-Entrenos'),
('Aminoácidos'),
('Barras y Snacks');


INSERT INTO VARIANTES (Presentacion, Contenido, Sabor) VALUES
-- Variantes para Creatina (Generalmente sin sabor)
('Bote', '500 gramos', NULL), 

-- Variantes para Proteína (Diferentes sabores y formatos)
('Bolsa', '1000 gramos', 'Chocolate'), 
('Bote', '750 gramos', 'Vainilla'),

-- Variantes para Pre-Entreno (Diferentes contenidos y sabores)
('Bote', '30 Servicios', 'Tropical Punch'),
('Bote', '30 Servicios', 'Fresa'),

-- Variantes para Aminoácidos/Vitaminas (Cápsulas)
('Frasco', '120 Cápsulas', NULL); 




--IDs de CATEGORIAS: 1=Proteínas, 2=Creatinas, 3=Pre-Entrenos, 4=Aminoácidos, 5=Barras
INSERT INTO PRODUCTOS (nombre, precioBase, descripcion, enOferta, idCategoria) VALUES
(
    'Whey Protein Blend',65000,'Mezcla de proteína de suero concentrada y aislada.', 1,1 -- Proteínas
),      
(
    'Creatina Monohidratada Pura', 30000,'Creatina micronizada de alta calidad.',0,2 -- Creatinas
	),                       
(
    'Intense Focus Pre-Workout',42000,'Fórmula para máxima energía y rendimiento.',1,3 -- Pre-Entrenos
),                  
(
    'BCAA Recovery Plus',38000,'Aminoácidos para soporte de la recuperación y anticatabolismo.', 0,4 -- Aminoácidos
),                      
(
    'Barra Proteica High Fiber',4500,'Snack alto en proteína y fibra.',0,5 -- Barras y Snacks
	)

INSERT INTO STOCK_VARIANTE (idProducto, idVariante, cantidadStock) VALUES

(1, 2, 50),
(1, 3, 35),
(2, 1, 120),
(3, 4, 45), 
(3, 5, 60), 
(4, 6, 80);
GO

EXEC sp_registrar_Usuario 'OscarFargas','Coquito007','Administrador'

EXEC sp_validar_login 'OscarFargas', 'Coquito007'

EXEC sp_Agregar_CATEGORIAS 'PRUEBA 1'
EXEC sp_Obtener_CATEGORIAS '1'
EXEC sp_Actualizar_CATEGORIAS '6','Actualizado'
EXEC sp_Eliminar_CATEGORIAS '6'

EXEC sp_Agregar_PRODUCTOS 'PRUEBA 1','11111','Esto es una prueba','1','1'
EXEC sp_Obtener_PRODUCTOS '6'
EXEC sp_Actualizar_PRODUCTOS '6','Actualizado','0000','Esto es una prueba','2','2'
EXEC sp_Eliminar_PRODUCTOS '6'

EXEC sp_Agregar_VARIANTES 'LATA','1111 GM','SIN SABOR'
EXEC sp_Obtener_VARIANTES '7'
EXEC sp_Actualizar_VARIANTES '7', 'Actualizado','0000 GM','Con SABOR'
EXEC sp_Eliminar_VARIANTES '7'
