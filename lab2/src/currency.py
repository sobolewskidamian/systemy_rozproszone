import json
import requests

from exception import ApiException


class CurrencyResponse:
    def __init__(self, currency):
        self.currency_code = currency

    def get_html(self):
        response = "%s - PLN<br>%s<br><br>Aktualny kurs: %s<br>Kupno: %s<br>Sprzedaż: %s<br><br>%s<br>Za 100 %s kupisz %.2fg złota" % \
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
            raise ApiException("Waluta %s nie istnieje.<br><br>Dostępne waluty:<br>%s" % (
                self.currency_code, self._get_available_currencies()))
        output = json.loads(output.content)
        self.currency_code = output.get("code")
        self.currency_name = output.get("currency")
        self.today_rate = CurrencyRate(str(output.get("rates")[0].get("mid")))

    def _get_today_info(self):
        output = requests.get("https://api.nbp.pl/api/exchangerates/rates/c/%s/?format=json" % self.currency_code)
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
        for date in self.last_days_rates.keys():
            rate = self.last_days_rates[date]
            response += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (date, rate.mid, rate.ask, rate.bid)
        response += "</table>"
        return response

    def _get_amount_of_gold(self):
        output = requests.get("https://api.nbp.pl/api/cenyzlota/?format=json")
        output = json.loads(output.content)
        price_pln = output[0]["cena"]
        self.gold_amount = 100 * float(self.today_rate.mid) / price_pln

    @staticmethod
    def _get_available_currencies():
        output = requests.get("https://api.nbp.pl/api/exchangerates/tables/a/?format=json")
        output = json.loads(output.content)
        rates = output[0]["rates"]
        response = ""
        for i in rates:
            response += "%s - %s<br>" % (i["code"], i["currency"])
        return response


class CurrencyRate:
    def __init__(self, mid, bid="Brak danych", ask="Brak danych"):
        self.mid = mid
        self.bid = bid
        self.ask = ask
