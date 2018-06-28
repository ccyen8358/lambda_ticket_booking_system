# written by Cheng-Chieh Yen
import boto3
import zipfile
import xml.etree.ElementTree as ET
import datetime
import urllib.parse
import os
import json
import uuid

# 使用boto3來存取AWS資源
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    
	# S3觸發的事件會存在一個Dictionary裡，這個Dictionary存放在event['Records']的序列中
    for record in event['Records']:
		# 上傳S3的Bucket Name
        BUCKET_NAME = record['s3']['bucket']['name']
		# 上傳至S3的zip檔名稱
        key = record['s3']['object']['key']
        raw_key = urllib.parse.unquote_plus(key)
		
		# 從S3下載被上傳的zip檔
        download_zip_path = '/tmp/{}'.format(key)
        s3.Bucket(BUCKET_NAME).download_file(raw_key, download_zip_path)
		        
        # 將zip檔解壓縮至/tmp之下("Lambda只能解壓縮至/tmp")
        zip_ref = zipfile.ZipFile(download_zip_path, 'r')
        zip_ref.extractall('/tmp')
        zip_ref.close()

		# 解壓縮後的演唱會資料是存在xml檔裡
        xml_path = os.path.splitext(download_zip_path)[0] + '.xml'
		
		# evt是一個Dictionary物件，我們會將演唱會資訊放至evt裡
		# 之後我們會將evt寫入DynamoDB裡
        evt = {}

        # 使用for迴圈讀取xml的節點並寫入至evt
        tree = ET.parse(xml_path)
        root = tree.getroot()

        for child in root:
			# 演唱會名稱
            if child.tag == 'name':
                evt['name'] = child.text
			# 主唱歌手
            elif child.tag == 'performer':
                evt['performer'] = child.text
			# 來賓歌手
            elif child.tag == 'guests':
                evt['guests'] = []
                for guest in child:
                    evt['guests'].append(guest.text)
			# 演唱會日期
            elif child.tag == 'date':
                date = datetime.datetime.strptime(child.text, '%Y-%m-%d-%H:%M')
                evt['date'] = date.isoformat()
			# 演唱會票種與票價
            elif child.tag == 'prices':
                evt['prices'] = []
                for price in child:
                    evt['prices'].append({ 'tier' : price.attrib['tier'],  'price' : int(price.text) })
			# 演唱會圖片
            elif child.tag == 'image':
				# 這邊會把解壓縮出來的演唱會圖片再次上傳至一個新的S3上
				# 請記得自己將'webapp-event-pics'修改為你自己的S3 Bucket名稱
                s3.Bucket('webapp-event-pics').upload_file('/tmp/{0}'.format(child.text), child.text)
                evt['image'] = child.text
        
		# 演唱會的料庫序號
        evt["uuid"] = str(uuid.uuid4())
        
		# 將evt寫入DynamoDB裡的"events"資料夾
        table = dynamodb.Table('events')
        table.put_item(
            Item=evt
        )