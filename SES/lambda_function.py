import json
import boto3
import urllib
import time
import decimal
import traceback

# DynamoDB オブジェクト
dynamodb = boto3.resource('dynamodb')

# メール送信関数
MAILFROM = '@gmail.com'
def sendmail(to, subject, body):
    client = boto3.client('ses', region_name='ap-northeast-1')

    response = client.send_email(
        Source = MAILFROM,
        ReplyToAddresses = [MAILFROM],
        Destination = {
            'ToAddresses' : [
                to
            ]
        },
        Message = {
            'Subject' : {
                'Data' : subject,
                'Charset' : 'UTF-8',
            },
            'Body' : {
                'Text' : {
                    'Data' : body,
                    'Charset' : 'UTF-8'
                }
            }
        }
    )

# 連番を更新して返す関数
def next_seq(table, tablename):
    response = table.update_item(
        Key={
            'tablename' : tablename
        },
        UpdateExpression="set seq = seq + :val",
        ExpressionAttributeValues={
            ':val' : 1
        },
        ReturnValues='UPDATED_NEW'
    )
    return response['Attributes']['seq']

def lambda_handler(event, context):
    try:
        # フォームに入力されたデータを得る
        param = urllib.parse.parse_qs(event['body'])
        username = param['username'][0]
        email = param['email'][0]

        # クライアントのIPを得る
        host = event['requestContext']['identity']['sourceIp']
        
        # シーケンスデータを得る
        seqtable = dynamodb.Table('sequence')
        nextseq = next_seq(seqtable, 'user')

        # 現在のUNIXタイムスタンプを得る
        now = time.time()
        
        # 署名付きURLを作る
        s3 = boto3.client('s3')
        url = s3.generate_presigned_url(
            ClientMethod = 'get_object',
            Params = {'Bucket' : 'secret-web-000', 'Key' : 'special.pdf'}, 
            ExpiresIn = 48 * 24 * 60 * 60, 
            HttpMethod = 'GET')

        # userテーブルに登録する
        usertable = dynamodb.Table("user")
        usertable.put_item(
            Item = {
                'id' : nextseq,
                'username' : username,
                'email' : email,
                'accepted_at' : decimal.Decimal(str(now)),
                'host' : host,
                'url' : url
            }
        )

        # メールを送信する
        mailbody = """

    {0}様

    ご登録ありがとうございました。
    下記のURLからダウンロードできます。

    {1}
    """.format(username, url)
         
        sendmail(email, "登録ありがとうございました", mailbody)

        # 結果を返す
        return {
            'statusCode' : 200,
            'headers' : {
                'content-type' : 'text/html'
            },
            'body' : '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>登録ありがとうございました。</body></html>'
        }
    except:
        traceback.print_exc()
        return {
            'statusCode' : 500,
            'headers' : {
                'content-type' : 'text/html'
            },
            'body' : '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>内部エラーが発生しました。</body></html>'
        }