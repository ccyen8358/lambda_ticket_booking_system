# !/usr/bin/python
# written by Cheng-Chieh Yen

import boto3
from flask import Flask, render_template, request, redirect, url_for

# 我們使用flask來當作web server
# flask會使用route map來定義不同request url時應做的動作
app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', 'ap-southeast-1')

app.config['UPLOAD_FOLDER'] = ''
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


# 這是購票網首頁，它會顯示所有演唱會資料		   
@app.route('/', methods=['POST', 'GET'])
def home():
    table = dynamodb.Table('events')
	# 讀取全部的演唱會資料
    response = table.scan()
    # 使用render_template來將演唱會資料pass到前端
	# 前端的index.html必須使用Jinja2語法
    return render_template('index.html', items=response['Items'])

# 這是特定演唱會的購票頁面，URL裡的evt_id就是演唱會的序號
@app.route('/view/<evt_id>', methods=['GET'])
def view_evt(evt_id):	
    table = dynamodb.Table('events')
	# 使用指定的evt_id來讀取特定的演唱會資料
    response = table.get_item(
        Key={
            'uuid': evt_id
        }
    )
    # 使用render_template來將演唱會資料pass到前端
	# 前端的ticket.html必須使用Jinja2語法
    return render_template('ticket.html', item=response['Item'])

# 這是訂票收據頁面，URL裡的rct_id就是訂票的收據序號
@app.route('/receipt/<rct_id>', methods=['GET'])
def view_receipt(rct_id):
    table = dynamodb.Table('ticket_purchase')
	# 使用指定的rct_id來讀取特定的訂票收據資料
    response = table.get_item(
        Key={
            'uuid': rct_id
        }
    )
    receipt = response['Item']
    # 使用render_template來將訂票收據資料pass到前端
	# 前端的receipt.html必須使用Jinja2語法
    receipt['mr_mrs'] = "Mr." if receipt['gender'] == 'male' else "Ms."
	
    return render_template('receipt.html', item=response['Item'])

'''
@app.route('/test', methods=['GET'])
def test():
    return render_template('test.html')
'''

# 啟動使用80 port來啟動web server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)