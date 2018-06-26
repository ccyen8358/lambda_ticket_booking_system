# written by Cheng-Chieh Yen
import boto3
import zipfile
import xml.etree.ElementTree as ET
import datetime
import urllib.parse
import os
import json
import uuid
import textwrap

def lambda_handler(event, context):
    
	# API轉發的訂票內容會以json的形式存在event['body']裡
	# 我們把這個json轉換成叫obj的dictionary物件，之後我們會會把這個obj寫入DynamoDB
    obj = json.loads(event['body'])
    obj['total'] = int(obj['total'])
    for ticket in obj['purchase']:
        ticket['ticket_count'] = int(ticket['ticket_count'])
        ticket['ticket_price'] = int(ticket['ticket_price'])
    
	# 給obj添加訂單序號與訂票日期
    purchase_uuid = str(uuid.uuid4())
    obj["uuid"] = purchase_uuid
    obj["date"] = datetime.datetime.now().isoformat();
    
	# 將含有訂票資訊的物件obj寫入DynamoDB裡的"ticket_purchase"資料表
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ticket_purchase')
    table.put_item(
        Item=obj
    )
    
    # 確認客戶訂單是否有電話號碼
	# 若有的話就使用SNS寄出SMS短信
    if 'customer_phone' in obj and (obj['customer_phone'].startswith('09') or obj['customer_phone'].startswith('9')):
        
		# 電話號碼
        phone = obj['customer_phone'];
        
        ticket_msg = "購買項目:\n"
        for ticket in obj['purchase']:
            ticket_msg = ticket_msg + "\t" + "{0} (NT${1}) x {2}".format(ticket['ticket_type'], ticket['ticket_price'], ticket['ticket_count']) + "\n"
        
        mr_mrs = "先生" if obj["gender"] == 'male' else "小姐"
        
		# 短信的字串
        sns_message = textwrap.dedent("""    
            購票成功    
            {0} {1}，感謝您的購買。
            
            演唱會名稱: {2}
            {3}
            總計: NT${4}
            訂單序號: {5}
        """).format(obj['customer_name'], mr_mrs, obj['event_name'], ticket_msg, obj['total'], purchase_uuid)
        
        phone = phone.replace("-", "");
        if phone.startswith('09'):
            phone = '+886' + phone[1:]
        else:
            phone = '+886' + phone
		
		# 使用SNS寄出短信
        try:
            sns = boto3.client('sns', region_name='ap-southeast-1')  
            sns.publish(  
                PhoneNumber = phone,
                Message = sns_message
            )
        except:
            print('error')
    
	# 向發出AJAX訂單請求的演唱會網站回傳一個200 OK的response，這個response含有一個訂單序號
	# 我們的演唱會網站在會收到這個訂單序號後會自動轉址並顯示訂單收據
    out = {}
    out['isBase64Encoded'] = False
    out['headers'] = { 
        'Content-Type': 'text/plain',
        "Access-Control-Allow-Origin" : "*",
        "Access-Control-Allow-Credentials" : True
    }
    out['statusCode'] = 200
    out['body'] = purchase_uuid
    
    return out
    
    
    