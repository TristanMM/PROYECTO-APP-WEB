# pagos.py
import requests
import hashlib
import os

PAYVALIDA_MERCHANT_ID = os.environ.get('PAYVALIDA_MERCHANT_ID', 'TU_MERCHANT_ID')
PAYVALIDA_API_KEY     = os.environ.get('PAYVALIDA_API_KEY', 'TU_API_KEY')
PAYVALIDA_URL         = os.environ.get('PAYVALIDA_URL', 'https://sandbox.payvalida.com/api/')  # cambiar en producción

def generar_firma(merchant_id, orden_id, monto, api_key):
    """Payválida requiere un hash MD5 como firma de seguridad."""
    cadena = f"{merchant_id}{orden_id}{monto}{api_key}"
    return hashlib.md5(cadena.encode()).hexdigest()

def crear_orden_pago(orden_id, monto_colones, descripcion, email_cliente):
    """
    Crea una orden de pago en Payválida.
    Retorna la URL de pago a donde redirigir al cliente.
    """
    firma = generar_firma(
        PAYVALIDA_MERCHANT_ID,
        orden_id,
        monto_colones,
        PAYVALIDA_API_KEY
    )

    payload = {
        "merchant_id":   PAYVALIDA_MERCHANT_ID,
        "order_id":      orden_id,
        "amount":        monto_colones,
        "currency":      "CRC",
        "description":   descripcion,
        "email":         email_cliente,
        "return_url":    "https://tudominio.com/pago/exitoso",
        "cancel_url":    "https://tudominio.com/pago/cancelado",
        "notify_url":    "https://tudominio.com/pago/webhook",
        "signature":     firma
    }

    try:
        response = requests.post(
            PAYVALIDA_URL + "create_order",
            json=payload,
            timeout=10
        )
        data = response.json()

        if data.get("status") == "success":
            return {"ok": True, "url_pago": data["payment_url"]}
        else:
            return {"ok": False, "error": data.get("message", "Error desconocido")}

    except Exception as e:
        return {"ok": False, "error": str(e)}