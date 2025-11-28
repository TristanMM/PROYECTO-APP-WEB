USE BD_Okamifit
GO

----------------------------------------------------
-- 1. CONFIGURACIÓN DE SEGURIDAD (ENCRIPTACIÓN)
----------------------------------------------------

-- Crea la Master Key (requerida para crear la clave simétrica y el certificado)
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'Root12345';
GO

-- Crea el Certificado
CREATE CERTIFICATE CertificadoProyecto
WITH SUBJECT = 'Certificado para encriptar datos del proyecto';
GO

-- Crea la Clave Simétrica (AES_256) encriptada por el Certificado
CREATE SYMMETRIC KEY ClaveSimetricaProyecto
WITH ALGORITHM = AES_256
ENCRYPTION BY CERTIFICATE CertificadoProyecto;
GO


----------------------------------------------------
-- 2. PROCEDIMIENTOS DE USUARIOS Y SESIONES
----------------------------------------------------

-- Procedimiento para registrar un nuevo usuario (con contraseña encriptada)
CREATE OR ALTER PROCEDURE sp_registrar_Usuario1
    @nombre NVARCHAR(50),
    @contrasena VARCHAR(255),
    @rol NVARCHAR (50)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @id_usuario_nuevo INT;
    DECLARE @contrasena_encriptada VARBINARY(MAX);

    -- 1. Abre la clave simétrica para encriptar
    OPEN SYMMETRIC KEY ClaveSimetricaProyecto DECRYPTION BY CERTIFICATE CertificadoProyecto;

    SET @contrasena_encriptada = ENCRYPTBYKEY(KEY_GUID('ClaveSimetricaProyecto'), @contrasena);

    -- 2. Cierra la clave simétrica
    CLOSE SYMMETRIC KEY ClaveSimetricaProyecto;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- 3. Inserta el usuario con la contraseña encriptada
        INSERT INTO USUARIOS(nombreUsuario, hashPassword, rol)
        VALUES (@nombre, @contrasena_encriptada, @rol);

        SET @id_usuario_nuevo = SCOPE_IDENTITY();

        COMMIT TRANSACTION;

        SELECT
            1 AS Success,
            'Usuario registrado correctamente' AS Message,
            @id_usuario_nuevo AS CustomerID;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        SELECT
            0 AS Success,
            ERROR_MESSAGE() AS Message,
            -1 AS CustomerID;
    END CATCH
END
GO

-- Procedimiento para validar el login de un usuario
CREATE OR ALTER PROCEDURE sp_validar_login1
    @nombreUsuario VARCHAR(50),
    @contrasena VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @id_usuario INT;
    DECLARE @hashPassword VARBINARY(MAX);
    DECLARE @contrasena_desencriptada VARCHAR(255);

    BEGIN TRY
        -- 1. Obtiene el hash y el ID del usuario
        SELECT @id_usuario = u.IdUsuario,
               @hashPassword = u.hashPassword
        FROM USUARIOS u
        WHERE u.nombreUsuario = @nombreUsuario
          AND u.esBorrado = 0; -- Asegura que el usuario no esté borrado

        -- 2. Si el usuario existe, intenta desencriptar
        IF (@id_usuario IS NOT NULL)
        BEGIN
            OPEN SYMMETRIC KEY ClaveSimetricaProyecto DECRYPTION BY CERTIFICATE CertificadoProyecto;

            SET @contrasena_desencriptada = CONVERT(VARCHAR(255), DECRYPTBYKEY(@hashPassword));

            CLOSE SYMMETRIC KEY ClaveSimetricaProyecto;

            -- 3. Compara la contraseña
            IF (@contrasena_desencriptada = @contrasena)
            BEGIN
                SELECT 1 AS 'Success', 'Login correcto' AS 'Message', @id_usuario AS 'CustomerID';
            END
            ELSE
            BEGIN
                SELECT 0 AS 'Success', 'Correo o contraseña incorrectos' AS 'Message', -1 AS 'CustomerID';
            END
        END
        ELSE
        BEGIN
            -- Usuario no encontrado o borrado
            SELECT 0 AS 'Success', 'Correo o contraseña incorrectos' AS 'Message', -1 AS 'CustomerID';
        END

    END TRY
    BEGIN CATCH
        IF EXISTS (SELECT * FROM sys.openkeys WHERE key_name = 'ClaveSimetricaProyecto')
             CLOSE SYMMETRIC KEY ClaveSimetricaProyecto;

        SELECT 0 AS 'Success', ERROR_MESSAGE() AS 'Message', -1 AS 'CustomerID';
    END CATCH
END
GO

-- Procedimiento para crear la sesion de un usuario
CREATE OR ALTER PROCEDURE sp_Crear_SESION1
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
GO

-- Procedimiento para validar un token de sesión y obtener el ID de usuario
CREATE OR ALTER PROCEDURE sp_Validar_SESION1
    @token VARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;
    -- Retorna el id_usuario solo si la sesión está activa y no ha expirado
    SELECT id_usuario
    FROM sesiones
    WHERE token = @token AND fecha_expiracion > GETDATE();
END
GO

-- Procedimiento para cerrar una sesión (elimina el registro)
CREATE OR ALTER PROCEDURE sp_Cerrar_SESION1
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
GO

----------------------------------------------------
-- 3. PROCEDIMIENTOS CRUD - CATEGORIAS
----------------------------------------------------

-- C: Insertar
CREATE OR ALTER PROCEDURE sp_Agregar_CATEGORIAS1
    @nombreCategoria NVARCHAR(50)
AS
BEGIN
    INSERT INTO CATEGORIAS (nombreCategoria, esBorrado)
    VALUES (@nombreCategoria, 0) -- Asegura que no está borrado al insertar
END
GO

-- R: Obtener (Filtra los registros borrados por defecto)
CREATE OR ALTER PROCEDURE sp_Obtener_CATEGORIAS1
    @idCategoria INT = NULL,
    @incluirBorrados BIT = 0
AS
BEGIN
    SELECT idCategoria, nombreCategoria, esBorrado
    FROM CATEGORIAS
    WHERE idCategoria = ISNULL(@idCategoria, idCategoria)
      AND (esBorrado = 0 OR @incluirBorrados = 1); -- Filtro de borrado lógico
END
GO

-- U: Actualizar
CREATE OR ALTER PROCEDURE sp_Actualizar_CATEGORIAS1
    @idCategoria INT,
    @nombreCategoria NVARCHAR(50)
AS
BEGIN
    UPDATE CATEGORIAS
    SET nombreCategoria = @nombreCategoria
    WHERE idCategoria = @idCategoria;
END
GO

-- D: Eliminar (Borrado Lógico)
CREATE OR ALTER PROCEDURE sp_Eliminar_CATEGORIAS1
    @idCategoria INT
AS
BEGIN
    -- Marca el registro como borrado
    UPDATE CATEGORIAS
    SET esBorrado = 1
    WHERE idCategoria = @idCategoria;
END
GO


----------------------------------------------------
-- 4. PROCEDIMIENTOS CRUD - VARIANTES
----------------------------------------------------

-- C: Insertar
CREATE OR ALTER PROCEDURE sp_Agregar_VARIANTES1
    @Presentacion NVARCHAR(50),
    @Contenido NVARCHAR(50),
    @Sabor NVARCHAR(50)
AS
BEGIN
    INSERT INTO VARIANTES (Presentacion, Contenido, Sabor, esBorrado)
    VALUES (@Presentacion, @Contenido, @Sabor, 0); -- Asegura que no está borrado al insertar
END
GO

-- R: Obtener (Filtra los registros borrados por defecto)
CREATE OR ALTER PROCEDURE sp_Obtener_VARIANTES1
    @idVariante INT = NULL,
    @incluirBorrados BIT = 0
AS
BEGIN
    SELECT idVariante, Presentacion, Contenido, Sabor, esBorrado
    FROM VARIANTES
    WHERE idVariante = ISNULL(@idVariante, idVariante)
      AND (esBorrado = 0 OR @incluirBorrados = 1); -- Filtro de borrado lógico
END
GO

-- U: Actualizar
CREATE OR ALTER PROCEDURE sp_Actualizar_VARIANTES1
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
GO

-- D: Eliminar (Borrado Lógico)
CREATE OR ALTER PROCEDURE sp_Eliminar_VARIANTES1
    @idVariante INT
AS
BEGIN
    -- Marca el registro como borrado
    UPDATE VARIANTES
    SET esBorrado = 1
    WHERE idVariante = @idVariante;
END
GO


----------------------------------------------------
-- 5. PROCEDIMIENTOS CRUD - PRODUCTOS
----------------------------------------------------

-- C: Insertar
CREATE OR ALTER PROCEDURE sp_Agregar_PRODUCTOS1
    @nombre NVARCHAR(100),
    @precioBase INT,
    @descripcion NVARCHAR(MAX),
    @enOferta BIT,
    @idCategoria INT,
    @urlImagen NVARCHAR(MAX)
AS
BEGIN
    INSERT INTO PRODUCTOS (nombre, precioBase, descripcion, enOferta, idCategoria, urlImagen, esBorrado)
    VALUES (@nombre, @precioBase, @descripcion, @enOferta, @idCategoria, @urlImagen, 0);
END
GO

-- R: Obtener (Filtra los productos borrados por defecto, une con Categorías)
CREATE OR ALTER PROCEDURE sp_Obtener_PRODUCTOS1
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
        P.urlImagen,
        C.nombreCategoria,
        P.esBorrado
    FROM PRODUCTOS P
    JOIN CATEGORIAS C ON P.idCategoria = C.idCategoria
    WHERE P.idProducto = ISNULL(@idProducto, P.idProducto)
      AND (P.esBorrado = 0 OR @incluirBorrados = 1); -- Filtro de borrado lógico
END
GO

-- U: Actualizar
CREATE OR ALTER PROCEDURE sp_Actualizar_PRODUCTOS1
    @idProducto INT,
    @nombre NVARCHAR(100),
    @precioBase INT,
    @descripcion NVARCHAR(MAX),
    @enOferta BIT,
    @idCategoria INT,
    @urlImagen NVARCHAR(MAX)
AS
BEGIN
    UPDATE PRODUCTOS
    SET nombre = @nombre,
        precioBase = @precioBase,
        descripcion = @descripcion,
        enOferta = @enOferta,
        idCategoria = @idCategoria,
        urlImagen = @urlImagen
    WHERE idProducto = @idProducto;
END
GO

-- D: Eliminar (Borrado Lógico)
CREATE OR ALTER PROCEDURE sp_Eliminar_PRODUCTOS1
    @idProducto INT
AS
BEGIN
    -- Marca el registro como borrado
    UPDATE PRODUCTOS
    SET esBorrado = 1
    WHERE idProducto = @idProducto;
END
GO


----------------------------------------------------
-- 6. PROCEDIMIENTOS CRUD - STOCK_VARIANTE (N:M)
----------------------------------------------------

-- C: Insertar
CREATE OR ALTER PROCEDURE sp_Agregar_STOCK_VARIANTE1
    @idProducto INT,
    @idVariante INT,
    @cantidadStock INT
AS
BEGIN
    -- Usa MERGE o verifica si existe para evitar duplicados si es necesario.
    -- Para este caso simple de INSERT:
    INSERT INTO STOCK_VARIANTE (idProducto, idVariante, cantidadStock)
    VALUES (@idProducto, @idVariante, @cantidadStock);
END
GO

-- R: Obtener (Une con Productos y Variantes, filtra por producto no borrado)
CREATE OR ALTER PROCEDURE sp_Obtener_STOCK_VARIANTE1
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
      AND P.esBorrado = 0; -- Filtra stock de productos que han sido borrados lógicamente
END
GO

-- U: Actualizar
CREATE OR ALTER PROCEDURE sp_Actualizar_STOCK_VARIANTE1
    @idProducto INT,
    @idVariante INT,
    @cantidadStock INT
AS
BEGIN
    UPDATE STOCK_VARIANTE
    SET cantidadStock = @cantidadStock
    WHERE idProducto = @idProducto AND idVariante = @idVariante;
END
GO

-- D: Eliminar (Borrado Físico del registro de stock/variante)
CREATE OR ALTER PROCEDURE sp_Eliminar_STOCK_VARIANTE1
    @idProducto INT,
    @idVariante INT
AS
BEGIN
    DELETE FROM STOCK_VARIANTE
    WHERE idProducto = @idProducto AND idVariante = @idVariante;
END
GO