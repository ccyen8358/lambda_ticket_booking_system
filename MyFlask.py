# !/usr/bin/python
# written by Cheng-Chieh Yen

import boto3
from flask import Flask, render_template, request, redirect, url_for

# we use flask as our web server
# flask uses route maps to define different actions to do for different urls
app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', 'ap-southeast-1')

app.config['UPLOAD_FOLDER'] = ''
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


# this is home page. it displays all concerts		   
@app.route('/', methods=['POST', 'GET'])
def home():
    table = dynamodb.Table('events')
	# load all concert data
    response = table.scan()
    # use render_template() to pass data to front end
	# we use Jinja2 syntax in index.html
    return render_template('index.html', items=response['Items'])

# this is ticket purchase page. it displays specific concert
@app.route('/view/<evt_id>', methods=['GET'])
def view_evt(evt_id):	
    table = dynamodb.Table('events')
	# use given evt_id to load concert data
    response = table.get_item(
        Key={
            'uuid': evt_id
        }
    )
    # use render_template() to pass data to front end
	# we use Jinja2 syntax in ticket.html
    return render_template('ticket.html', item=response['Item'])

# this is receipt page. it displays receipt information
@app.route('/receipt/<rct_id>', methods=['GET'])
def view_receipt(rct_id):
    table = dynamodb.Table('ticket_purchase')
	# use given rct_id to load receipt data
    response = table.get_item(
        Key={
            'uuid': rct_id
        }
    )
    receipt = response['Item']
    # use render_template() to pass data to front end
	# we use Jinja2 syntax in receipt.html
    receipt['mr_mrs'] = "Mr." if receipt['gender'] == 'male' else "Ms."
	
    return render_template('receipt.html', item=response['Item'])

'''
@app.route('/test', methods=['GET'])
def test():
    return render_template('test.html')
'''

# start web server with port 80
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)