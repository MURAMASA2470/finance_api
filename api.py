import sys
import re
from urllib import request
from lxml import html
from flask import Flask, jsonify, abort, make_response

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/api/<string:code>', methods=['GET'])
def get_company_info(code):

    # 証券コード以外は400エラー
    if not re.match(r'^\d{4}$', code): abort(400)

    param = code.split(',')
    result = []
    for cd in param:
        if not cd: break
        URL = "https://finance.yahoo.co.jp/quote/%s.T" % cd
        data = request.urlopen(URL)
        raw_html = data.read().decode(data.headers.get_content_charset(), errors='ignore')
        xml = html.fromstring(str(raw_html))

        companyName = xml.xpath('//*[@id="root"]/main/div/div/div[1]/div[2]/section[1]/div[2]/header/div[1]/h1')[0].text
        currentPrice = xml.xpath('//*[@id="root"]/main/div/div/div[1]/div[2]/section[1]/div[2]/header/div[2]/span/span/span')[0].text
        previousClose = xml.xpath('//*[@id="detail"]/section[1]/div/ul/li[1]/dl/dd/span[1]/span/span')[0].text

        obj = {
            'company_name'      : { 'name': "企業名",   'value': companyName },
            'current_price'     : { 'name': "現在株価", 'value': float(currentPrice.replace(",", "")) },
            'previous _close'   : { 'name': "前日終値", 'value': float(previousClose.replace(",", ""))  }
        }
        result.append(obj)

    return make_response(jsonify(result))

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)