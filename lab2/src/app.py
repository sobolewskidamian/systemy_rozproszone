from flask import Flask, request

from currency import CurrencyResponse
from exception import ApiException

app = Flask(__name__)


@app.errorhandler(ApiException)
def handle_invalid_usage(error):
    return error.message, error.status_code


@app.route('/')
def hello():
    return '<form action="/currency" method="post">' \
           'Kod waluty: <input type="text" id="currency" name="value"><br>' \
           '<input type="submit" value="Pokaż statystyki">' \
           '</form>'


@app.route('/currency', methods=['POST'])
def currency_endpoint():
    currency: str = request.form.get('value')
    if not currency:
        raise ApiException("Bad input")

    response = CurrencyResponse(currency)
    response.process()
    return response.get_html()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
