VALID_USER = {"email": "testuser@example.com", "password": "Test@123"}
INVALID_USER = {"email": "invalid@example.com", "password": "WrongPassword"}

PRODUCTS = {
    "mouse": 101,
    "keyboard": 102,
    "hub": 103,
    "headphones": 104,
    "out_of_stock": 105,
}

VALID_PAYMENT = {
    "cardholder_name": "Test User",
    "card_number": "4111111111111111",
    "expiration_date": "12/30",
    "cvv": "123",
}

DECLINED_PAYMENT = {
    "cardholder_name": "Test User",
    "card_number": "4000000000000002",
    "expiration_date": "12/30",
    "cvv": "123",
}
