USE BD_Okamifit 
GO

CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Root12345'


CREATE CERTIFICATE CertificadoProyecto WITH SUBJECT = 'Certificado para encriptar datos del proyecto'



CREATE SYMMETRIC KEY ClaveSimetricaProyecto
WITH ALGORITHM = AES_256
ENCRYPTION BY CERTIFICATE CertificadoProyecto


CREATE OR ALTER PROCEDURE sp_registrar_Usuario
    @nombre NVARCHAR(50),
    @contrasena VARCHAR(255),
	@rol NVARCHAR (50)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @id_usuario_nuevo INT;
    DECLARE @contrasena_encriptada VARBINARY(MAX);

    -- Abrimos la clave simétrica para poder usarla
    OPEN SYMMETRIC KEY ClaveSimetricaProyecto DECRYPTION BY CERTIFICATE CertificadoProyecto;

    -- Encriptamos la contraseña
    SET @contrasena_encriptada = ENCRYPTBYKEY(KEY_GUID('ClaveSimetricaProyecto'), @contrasena);

    -- Cerramos la clave
    CLOSE SYMMETRIC KEY ClaveSimetricaProyecto;

    -- Usamos una transacción para asegurar la integridad de los datos
    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO USUARIOS(nombreUsuario,hashPassword,rol) VALUES (@nombre,@contrasena_encriptada,@rol);
        SET @id_usuario_nuevo = SCOPE_IDENTITY();

        
        COMMIT TRANSACTION;
        SELECT 1 AS 'Success', 'Usuario registrado correctamente' AS 'Message', @id_usuario_nuevo AS 'CustomerID';
    END TRY
    BEGIN CATCH
        -- Si algo falla, revertimos todos los cambios
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        SELECT 0 AS 'Success', ERROR_MESSAGE() AS 'Message', -1 AS 'CustomerID';
    END CATCH
END





-- Procedimiento para validar el login de un usuario
CREATE OR ALTER PROCEDURE sp_validar_login
    @nombreUsuario VARCHAR(50),
    @contrasena VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @id_usuario INT;  
    DECLARE @contrasena_desencriptada VARCHAR(255);

    BEGIN TRY
        OPEN SYMMETRIC KEY ClaveSimetricaProyecto DECRYPTION BY CERTIFICATE CertificadoProyecto;

        SELECT @id_usuario = u.IdUsuario,
               @contrasena_desencriptada = CONVERT(VARCHAR(255), DECRYPTBYKEY(hashPassword))
        FROM USUARIOS u
        WHERE u.nombreUsuario = @nombreUsuario;

        CLOSE SYMMETRIC KEY ClaveSimetricaProyecto;

        IF (@id_usuario IS NOT NULL AND @contrasena_desencriptada = @contrasena)
        BEGIN
            SELECT 1 AS 'Success', 'Login correcto' AS 'Message', @id_usuario AS 'CustomerID';
        END
        ELSE
        BEGIN
            SELECT 0 AS 'Success', 'Correo o contraseña incorrectos' AS 'Message', -1 AS 'CustomerID';
        END
    END TRY
    BEGIN CATCH
        IF EXISTS (SELECT * FROM sys.openkeys WHERE key_name = 'ClaveSimetricaProyecto')
            CLOSE SYMMETRIC KEY ClaveSimetricaProyecto;

        SELECT 0 AS 'Success', ERROR_MESSAGE() AS 'Message', -1 AS 'CustomerID';
    END CATCH
END




-- Procedimiento para crear la sesion de un usuario
CREATE OR ALTER PROCEDURE sp_Crear_SESION
    @id_usuario INT,
    @token VARCHAR(255),
    @minutos_expiracion INT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        -- 1. Verifica si el usuario existe Y no está borrado
        IF NOT EXISTS (SELECT 1 FROM USUARIOS WHERE idUsuario = @id_usuario AND esBorrado = 0)
        BEGIN
            SELECT 0 AS 'Success', 'El usuario no existe o está inactivo.' AS 'Message';
            RETURN;
        END

        -- 2. Inserta la sesión
        INSERT INTO SESIONES (id_usuario, token, fecha_inicio, fecha_expiracion)
        VALUES (@id_usuario, @token, GETDATE(), DATEADD(minute, @minutos_expiracion, GETDATE()));
        
        SELECT 1 AS 'Success', 'Sesión creada.' AS 'Message';
    END TRY
    BEGIN CATCH
        SELECT 0 AS 'Success', ERROR_MESSAGE() AS 'Message';
    END CATCH
END

-- Procedimiento para validar un token de sesión y obtener el ID de usuario
CREATE OR ALTER PROCEDURE sp_Validar_SESION
    @token VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id_usuario
    FROM sesiones
    WHERE token = @token AND fecha_expiracion > GETDATE();
END


-- Procedimiento para cerrar una sesión
CREATE OR ALTER PROCEDURE sp_Cerrar_SESION
    @token VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        DELETE FROM sesiones WHERE token = @token;
        SELECT 1 AS 'Success', 'Sesión cerrada' AS 'Message';
    END TRY
    BEGIN CATCH
        SELECT 0 AS 'Success', ERROR_MESSAGE() AS 'Message';
    END CATCH
END

--****************************CATEGORIAS***********************

CREATE OR ALTER PROCEDURE sp_Agregar_CATEGORIAS
    @nombreCategoria NVARCHAR(50)
AS
BEGIN
    INSERT INTO CATEGORIAS (nombreCategoria)
    VALUES (@nombreCategoria)
END
GO


-- R: Obtener (Filtra los registros borrados por defecto)
CREATE OR ALTER PROCEDURE sp_Obtener_CATEGORIAS
    @idCategoria INT = NULL,
    @incluirBorrados BIT = 0
AS
BEGIN
    SELECT idCategoria, nombreCategoria, esBorrado
    FROM CATEGORIAS
    WHERE idCategoria = ISNULL(@idCategoria, idCategoria)
      AND (esBorrado = 0 OR @incluirBorrados = 1); -- Filtro de borrado lógico
END


-- U: Actualizar
CREATE OR ALTER PROCEDURE sp_Actualizar_CATEGORIAS
    @idCategoria INT,
    @nombreCategoria NVARCHAR(50)
AS
BEGIN
    UPDATE CATEGORIAS
    SET nombreCategoria = @nombreCategoria
    WHERE idCategoria = @idCategoria;
END


-- D: Eliminar (Borrado Lógico)
CREATE OR ALTER PROCEDURE sp_Eliminar_CATEGORIAS
    @idCategoria INT
AS
BEGIN
    -- Marca el registro como borrado
    UPDATE CATEGORIAS
    SET esBorrado = 1
    WHERE idCategoria = @idCategoria;
END

--************************************VARIANTES***************************

-- C: Insertar
CREATE OR ALTER PROCEDURE sp_Agregar_VARIANTES
    @Presentacion NVARCHAR(50),
    @Contenido NVARCHAR(50),
    @Sabor NVARCHAR(50)
AS
BEGIN
    INSERT INTO VARIANTES (Presentacion, Contenido, Sabor)
    VALUES (@Presentacion, @Contenido, @Sabor);
END


-- R: Obtener (Filtra los registros borrados por defecto)
CREATE OR ALTER PROCEDURE sp_Obtener_VARIANTES
    @idVariante INT = NULL,
    @incluirBorrados BIT = 0
AS
BEGIN
    SELECT idVariante, Presentacion, Contenido, Sabor, esBorrado
    FROM VARIANTES
    WHERE idVariante = ISNULL(@idVariante, idVariante)
      AND (esBorrado = 0 OR @incluirBorrados = 1); -- Filtro de borrado lógico
END


-- U: Actualizar
CREATE OR ALTER PROCEDURE sp_Actualizar_VARIANTES
    @idVariante INT,
    @Presentacion NVARCHAR(50),
    @Contenido NVARCHAR(50),
    @Sabor NVARCHAR(50)
AS
BEGIN
    UPDATE VARIANTES
    SET Presentacion = @Presentacion,
        Contenido = @Contenido,
        Sabor = @Sabor
    WHERE idVariante = @idVariante;
END


-- D: Eliminar (Borrado Lógico)
CREATE OR ALTER PROCEDURE sp_Eliminar_VARIANTES
    @idVariante INT
AS
BEGIN
    -- Marca el registro como borrado
    UPDATE VARIANTES
    SET esBorrado = 1
    WHERE idVariante = @idVariante;
END


--****************************************PRODUCTOS********************
-- C: Insertar
CREATE OR ALTER PROCEDURE sp_Agregar_PRODUCTOS
    @nombre NVARCHAR(100),
    @precioBase INT,
    @descripcion NVARCHAR(MAX),
    @enOferta BIT,
    @idCategoria INT
AS
BEGIN
    INSERT INTO PRODUCTOS (nombre, precioBase, descripcion, enOferta, idCategoria)
    VALUES (@nombre, @precioBase, @descripcion, @enOferta, @idCategoria);
END


-- R: Obtener (Filtra los productos borrados por defecto)
CREATE OR ALTER PROCEDURE sp_Obtener_PRODUCTOS
    @idProducto INT = NULL,
    @incluirBorrados BIT = 0
AS
BEGIN
    SELECT 
        P.idProducto, 
        P.nombre, 
        P.precioBase, 
        P.descripcion, 
        P.enOferta, 
        C.nombreCategoria,
        P.esBorrado
    FROM PRODUCTOS P
    JOIN CATEGORIAS C ON P.idCategoria = C.idCategoria
    WHERE P.idProducto = ISNULL(@idProducto, P.idProducto)
      AND (P.esBorrado = 0 OR @incluirBorrados = 1); -- Filtro de borrado lógico
END


-- U: Actualizar
CREATE OR ALTER PROCEDURE sp_Actualizar_PRODUCTOS
    @idProducto INT,
    @nombre NVARCHAR(100),
    @precioBase INT,
    @descripcion NVARCHAR(MAX),
    @enOferta BIT,
    @idCategoria INT
AS
BEGIN
    UPDATE PRODUCTOS
    SET nombre = @nombre,
        precioBase = @precioBase,
        descripcion = @descripcion,
        enOferta = @enOferta,
        idCategoria = @idCategoria
    WHERE idProducto = @idProducto;
END


-- D: Eliminar (Borrado Lógico)
CREATE OR ALTER PROCEDURE sp_Eliminar_PRODUCTOS
    @idProducto INT
AS
BEGIN
    -- Marca el registro como borrado
    UPDATE PRODUCTOS
    SET esBorrado = 1
    WHERE idProducto = @idProducto;
    
    -- Nota: En este esquema, no es necesario actualizar STOCK_VARIANTE, 
    -- ya que el filtro en PRODUCTOS se encargará de "ocultar" su stock asociado.
END


--***************************STOCK****************************
-- C: Insertar
CREATE OR ALTER PROCEDURE sp_Agregar_STOCK_VARIANTE
    @idProducto INT,
    @idVariante INT,
    @cantidadStock INT
AS
BEGIN
    INSERT INTO STOCK_VARIANTE (idProducto, idVariante, cantidadStock)
    VALUES (@idProducto, @idVariante, @cantidadStock);
END


-- R: Obtener (Filtra el stock de productos que NO están borrados)
CREATE OR ALTER PROCEDURE sp_Obtener_STOCK_VARIANTE
    @idProducto INT = NULL,
    @idVariante INT = NULL
AS
BEGIN
    SELECT 
        SV.idProducto, 
        P.nombre AS NombreProducto, 
        SV.idVariante, 
        V.Presentacion, 
        V.Contenido, 
        V.Sabor, 
        SV.cantidadStock
    FROM STOCK_VARIANTE SV
    JOIN PRODUCTOS P ON SV.idProducto = P.idProducto
    JOIN VARIANTES V ON SV.idVariante = V.idVariante
    WHERE SV.idProducto = ISNULL(@idProducto, SV.idProducto)
      AND SV.idVariante = ISNULL(@idVariante, SV.idVariante)
      AND P.esBorrado = 0; -- Filtra automáticamente si el producto está borrado
END


-- U: Actualizar
CREATE OR ALTER PROCEDURE sp_Actualizar_STOCK_VARIANTE
    @idProducto INT,
    @idVariante INT,
    @cantidadStock INT
AS
BEGIN
    UPDATE STOCK_VARIANTE
    SET cantidadStock = @cantidadStock
    WHERE idProducto = @idProducto AND idVariante = @idVariante;
END


-- D: Eliminar (Borrado Físico - Es común en tablas de enlace si la cantidad llega a cero, pero aquí lo mantendremos como físico si se quiere retirar la variante completamente)
CREATE OR ALTER PROCEDURE sp_Eliminar_STOCK_VARIANTE
    @idProducto INT,
    @idVariante INT
AS
BEGIN
    -- El borrado físico es aceptable en tablas de enlace N:M, ya que no suelen contener lógica histórica propia.
    DELETE FROM STOCK_VARIANTE
    WHERE idProducto = @idProducto AND idVariante = @idVariante;
END

