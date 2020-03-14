import requests
import json
from flask import Flask, request

app = Flask(__name__)


class ApiException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(ApiException)
def handle_invalid_usage(error):
    return error.message, error.status_code


@app.route('/')
def hello():
    return '<form action="/currency" method="get">' \
           'currency: <input type="text" id="currency" name="value"><br>' \
           '<input type="submit" value="Submit">' \
           '</form>'


class CurrencyRate:
    def __init__(self, mid, bid="Brak danych", ask="Brak danych"):
        self.mid = mid
        self.bid = bid
        self.ask = ask


class CurrencyResponse:
    def __init__(self, currency):
        self.currency_code = currency

    def get_html(self):
        response = "%s - PLN<br>%s<br>Aktualny kurs: %s<br><br>Kupno: %s<br>Sprzedaż: %s<br><br>%s<br>Za 100 %s kupisz %.2fg złota" % \
                   (
                       self.currency_code,
                       self.currency_name,
                       self.today_rate.mid,
                       self.today_rate.bid,
                       self.today_rate.ask,
                       self._get_rates_last_days_html(),
                       self.currency_code,
                       self.gold_amount
                   )
        return response

    def process(self):
        self._get_actual_info()
        self._get_today_info()
        self._get_rates_last_days()
        self._get_rates_last_days_buy_sell()
        self._get_amount_of_gold()

    def _get_actual_info(self):
        output = requests.get("http://api.nbp.pl/api/exchangerates/rates/a/%s/?format=json" % self.currency_code)
        if output.status_code != 200:
            raise ApiException("Currency does not exist. Examples: GBP, EUR, CHF")
        output = json.loads(output.content)
        self.currency_code = output.get("code")
        self.currency_name = output.get("currency")
        self.today_rate = CurrencyRate(str(output.get("rates")[0].get("mid")))

    def _get_today_info(self):
        output = requests.get("https://api.nbp.pl/api/exchangerates/rates/c/%s/today/?format=json" % self.currency_code)
        if output.status_code != 404:
            output = json.loads(output.content)
            rates = output.get("rates")[0]
            self.today_rate.ask = str(rates.get("ask"))
            self.today_rate.bid = str(rates.get("bid"))

    def _get_rates_last_days(self):
        output = requests.get(
            "https://api.nbp.pl/api/exchangerates/rates/a/%s/last/10/?format=json" % self.currency_code)
        output = json.loads(output.content)
        rates = output.get("rates")
        self.last_days_rates = {}
        for i in rates:
            self.last_days_rates[i["effectiveDate"]] = CurrencyRate(str(i["mid"]))

    def _get_rates_last_days_buy_sell(self):
        output = requests.get(
            "https://api.nbp.pl/api/exchangerates/rates/c/%s/last/10/?format=json" % self.currency_code)
        if output.status_code != 404:
            output = json.loads(output.content)
            rates = output.get("rates")
            for i in rates:
                self.last_days_rates[i["effectiveDate"]].ask = str(i["ask"])
                self.last_days_rates[i["effectiveDate"]].bid = str(i["bid"])

    def _get_rates_last_days_html(self):
        response = "<table><tr><td>Data</td><td>Kurs średni</td><td>Kupno</td><td>Sprzedaż</td></tr>"
        for date in list(self.last_days_rates.keys())[:-1]:
            rate = self.last_days_rates[date]
            response += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (date, rate.mid, rate.ask, rate.bid)
        response += "</table>"
        return response

    def _get_amount_of_gold(self):
        output = requests.get("https://api.nbp.pl/api/cenyzlota/?format=json")
        output = json.loads(output.content)
        price_pln = output[0]["cena"]
        self.gold_amount = 100 * float(self.today_rate.mid) / price_pln


@app.route('/currency')
def currency_endpoint():
    currency: str = request.args.get('value')
    if not currency:
        raise ApiException("Bad input")

    response = CurrencyResponse(currency)
    response.process()
    return response.get_html()


if __name__ == '__main__':
    app.run()
