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


def crear_checkout_session(items_carrito, orden_id, email_cliente, success_url, cancel_url):

    line_items = []
    for item in items_carrito:
        # Crear producto
        prod_response = requests.post(
            f'{ONVO_API_URL}/products',
            json={'name': item['nombre']},
            headers={
                'Authorization': f'Bearer {ONVO_SECRET_KEY}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        print(f"Producto status: {prod_response.status_code}")
        print(f"Producto respuesta: {prod_response.text}")
        prod_data = prod_response.json()
        product_id = prod_data.get('id')

        # Crear precio
        price_response = requests.post(
    f'{ONVO_API_URL}/prices',
    json={
        'unitAmount': int(item['precio']) * 100,  # ← multiplicar por 100
        'currency':   'CRC',
        'productId':  product_id,
        'type':       'one_time'
    },
    headers={
        'Authorization': f'Bearer {ONVO_SECRET_KEY}',
        'Content-Type': 'application/json'
    },
    timeout=10
)
        print(f"Precio status: {price_response.status_code}")
        print(f"Precio respuesta: {price_response.text}")
        price_data = price_response.json()
        price_id = price_data.get('id')

        line_items.append({
            'quantity': int(item['cantidad']),
            'priceId':  price_id
        })

    payload = {
        'customerName':  'Cliente Okami Fit',
        'customerEmail': email_cliente,
        'redirectUrl':   success_url,
        'cancelUrl':     cancel_url,
        'captureMethod': 'automatic',
        'lineItems':     line_items
    }

    print(f"=== ONVOPAY DEBUG ===")
    print(f"Payload: {payload}")

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
    print(f"====================")

    data = response.json()
    if response.status_code == 201:
        return {'ok': True, 'url': data.get('url'), 'id': data.get('id')}
    else:
        return {'ok': False, 'error': str(data.get('message', 'Error'))}