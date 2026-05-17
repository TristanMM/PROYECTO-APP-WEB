import requests
import os

ONVO_SECRET_KEY = os.environ.get('ONVO_SECRET_KEY', '')
ONVO_API_URL    = 'https://api.onvopay.com/v1'

def crear_payment_intent(monto_colones, descripcion):
    """
    Crea una intención de pago en OnvoPay.
    monto_colones debe ser entero (₡20000 → 20000)
    """
    response = requests.post(
        f'{ONVO_API_URL}/payment-intents',
        json={
            'amount':      monto_colones,
            'currency':    'CRC',
            'description': descripcion
        },
        headers={
            'Authorization': f'Bearer {ONVO_SECRET_KEY}',
            'Content-Type':  'application/json'
        },
        timeout=10
    )

    data = response.json()

    if response.status_code == 201:
        return {'ok': True, 'id': data['id']}
    else:
        return {'ok': False, 'error': data.get('message', 'Error desconocido')}


def crear_checkout_session(items_carrito, orden_id, email_cliente, success_url, cancel_url, conn):

    cursor = conn.cursor()
    line_items = []

    for item in items_carrito:
        # Busca el priceId guardado en tu BD
        cursor.execute(
            "SELECT onvo_price_id FROM productos WHERE idProducto = ?",
            (item['id'],)
        )
        row = cursor.fetchone()
        price_id = row[0] if row and row[0] else None

        if not price_id:
            print(f"⚠️ Producto {item['nombre']} no tiene onvo_price_id en la BD")
            continue

        line_items.append({
            'quantity': int(item['cantidad']),
            'priceId':  price_id
        })

    cursor.close()

    if not line_items:
        return {'ok': False, 'error': 'Ningún producto tiene precio configurado en OnvoPay'}

    payload = {
        'customerName':  email_cliente.split('@')[0],  # nombre aproximado
        'customerEmail': email_cliente,
        'redirectUrl':   success_url,
        'cancelUrl':     cancel_url,
        'captureMethod': 'automatic',
        'lineItems':     line_items
    }

    print(f"Payload enviado a OnvoPay: {payload}")

    response = requests.post(
        f'{ONVO_API_URL}/checkout/sessions/one-time-link',
        json=payload,
        headers={
            'Authorization': f'Bearer {ONVO_SECRET_KEY}',
            'Content-Type':  'application/json'
        },
        timeout=10
    )

    print(f"Status: {response.status_code}")
    print(f"Respuesta: {response.text}")

    data = response.json()
    if response.status_code == 201:
        return {'ok': True, 'url': data.get('url'), 'id': data.get('id')}
    else:
        return {'ok': False, 'error': str(data.get('message', 'Error'))}