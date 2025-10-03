"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
import time
from store_manager import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    """
    Smoke test pour vérifier le processus complet de gestion des stocks.
    Ce test vérifie que toutes les opérations de base fonctionnent correctement.
    """
    
    # 1. Créer un utilisateur de test (nécessaire pour les commandes)
    timestamp = int(time.time())
    user_data = {'name': 'Test User', 'email': f'test{timestamp}@example.com'}
    user_response = client.post('/users',
                               data=json.dumps(user_data),
                               content_type='application/json')
    
    assert user_response.status_code == 201
    user_result = user_response.get_json()
    user_id = user_result['user_id']
    assert user_id > 0
    
    # 2. Créer un article (`POST /products`)
    product_data = {'name': 'Test Item', 'sku': 'TEST123', 'price': 99.90}
    product_response = client.post('/products',
                                  data=json.dumps(product_data),
                                  content_type='application/json')
    
    assert product_response.status_code == 201
    product_result = product_response.get_json()
    product_id = product_result['product_id']
    assert product_id > 0 

    # 3. Ajouter 5 unités au stock de cet article (`POST /stocks`)
    stock_data = {'product_id': product_id, 'quantity': 5}
    stock_response = client.post('/stocks',
                                data=json.dumps(stock_data),
                                content_type='application/json')
    
    assert stock_response.status_code == 201
    stock_result = stock_response.get_json()
    assert 'result' in stock_result

    # 4. Vérifier le stock - l'article doit avoir 5 unités (`GET /stocks/:id`)
    get_stock_response = client.get(f'/stocks/{product_id}')
    
    assert get_stock_response.status_code == 201
    stock_info = get_stock_response.get_json()
    assert stock_info['quantity'] == 5, f"Stock initial devrait être 5, mais était {stock_info['quantity']}"
    
    # 5. Créer une commande de 2 unités de l'article (`POST /orders`)
    order_data = {
        'user_id': user_id,
        'items': [{'product_id': product_id, 'quantity': 2}]
    }
    order_response = client.post('/orders',
                                data=json.dumps(order_data),
                                content_type='application/json')
    
    assert order_response.status_code == 201
    order_result = order_response.get_json()
    order_id = order_result['order_id']
    assert order_id > 0

    # 6. Vérifier le stock après la commande - doit être 3 unités (`GET /stocks/:id`)
    get_stock_response = client.get(f'/stocks/{product_id}')
    
    assert get_stock_response.status_code == 201
    stock_info = get_stock_response.get_json()
    assert stock_info['quantity'] == 3, f"Stock après commande devrait être 3, mais était {stock_info['quantity']}"
    
    # 7. Étape extra: supprimer la commande et vérifier que le stock revient à 5
    delete_order_response = client.delete(f'/orders/{order_id}')
    
    assert delete_order_response.status_code == 200
    delete_order_result = delete_order_response.get_json()
    assert delete_order_result['deleted'] == True
    
    # 8. Vérifier que le stock est revenu à 5 après suppression de la commande
    get_stock_response = client.get(f'/stocks/{product_id}')
    
    assert get_stock_response.status_code == 201
    stock_info = get_stock_response.get_json()
    assert stock_info['quantity'] == 5, f"Stock après suppression de commande devrait être 5, mais était {stock_info['quantity']}"