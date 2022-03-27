import sys, threading
import re
import pandas
from urllib import request
from lxml import html
from flask import Flask, jsonify, abort, make_response

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

def get_company_info(code):
        URL = "https://finance.yahoo.co.jp/quote/%s.T" % code
        data = request.urlopen(URL)
        raw_html = data.read().decode(data.headers.get_content_charset(), errors='ignore')
        xml = html.fromstring(str(raw_html))

        companyName = xml.xpath('//*[@id="root"]/main/div/div/div[1]/div[2]/section[1]/div[2]/header/div[1]/h1')[0].text
        currentPrice = xml.xpath('//*[@id="root"]/main/div/div/div[1]/div[2]/section[1]/div[2]/header/div[2]/span/span/span')[0].text
        previousClose = xml.xpath('//*[@id="detail"]/section[1]/div/ul/li[1]/dl/dd/span[1]/span/span')[0].text

        return {
            'company_name'      : { 'name': "企業名",   'value': companyName },
            'current_price'     : { 'name': "現在株価", 'value': float(currentPrice.replace(",", "")) },
            'previous _close'   : { 'name': "前日終値", 'value': float(previousClose.replace(",", ""))  }
        }

class parallelProcess(threading.Thread):
    def __init__(self, code):
        threading.Thread.__init__(self)
        self.code = code
        self.obj = get_company_info(self.code)

@app.route('/', methods=['GET', 'POST'])
def index():
    abort(403)

@app.route('/api/companyList', methods=['GET'])
def api__get_company_list():

    xls_data = pandas.read_excel("https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls", usecols=[1, 2, 3])
    result = []
    for row in xls_data.itertuples():
        result.append({
            'index'         : row[0],
            'company_code'  : row[1],
            'company_name'  : row[2],
            'market_dv'     : row[3]
        })
    return make_response(jsonify(result))


@app.route('/api/companyInfo/<string:code>', methods=['GET'])
def api__get_company_info(code):

    # 証券コード以外は400エラー
    if not re.match(r'^(\d{4},?)+$', code): abort(400)

    param = code.split(',')
    result = []
    for cd in param:
        if not cd: break
        thread = parallelProcess(cd)
        thread.start()
        result.append(thread.obj)

    return make_response(jsonify(result))
    
@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)

@app.errorhandler(403)
def forbidden(error):
    return make_response(jsonify({'error': 'Forbidden'}), 403)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
