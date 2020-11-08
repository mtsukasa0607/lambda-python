import json
import boto3
import urllib
import time
import decimal

# DynamoDB オブジェクト
dynamodb = boto3.resource('dynamodb')

# 連番を更新して返す関数
def next_seq(table, tablename):
    response = table.update_item(
        Key = {
            'table' : tablename
        },
        UpdateExpression = "seq seq = seq + :val",
        ExpressionAttributeValues = {
            ':val' : 1
        },
        ReturnValues = 'UPDATE_NEW'
    )
    return response['Attributes']['seq']

def lambda_handler(event, context):
    try:
        # シーケンスデータを得る
        seqtable = dynamodb.Table('sequence')
        nextseq = next_seq(seqtable, 'user')

        # フォームに入力されたデータを得る
        param = urllib.parse.parse_qs(event['body'])
        username = param['username'][0]
        email = param['email'][0]

        # クライアントのIPを得る
        host = event['requestContext']['identity']['sourceIp']

        # 現在のUNIXタイムスタンプを得る
        now = time.time()

        # userテーブルに登録する
        usertable = dynamodb.Table("user")
        usertable.put_item(
            Item = {
                'id' : nextseq,
                'username' : username,
                'email' : email,
                'acccepted_at' : decimal.Decimal(str(now)),
                'host' : host,
            }
        )

        # 結果を返す
        return {
            'statusCode' : 200,
            'headers' : {
                'content-type' : 'text/html'
            },
            'body' : '<!DOCTYPE html><html><head><meta charset="UTF-8"><body>登録ありがとうございました。</body></head></html>'
        }
        except:
            import traceback
            traceback.print_exec()
            return {
                'statusCode' : 500,
                'headers' : {
                    'content-type' : 'text/html'
                },
                'body' : '<!DOCTYPE html><html><head><meta charset="UTF-8"><body>内部エラーが発生しました。</body></head></html>'
        }