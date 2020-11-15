import json
import boto3
import decimal

# DynamoDB オブジェクト
dynamodb = boto3.resource('dynamodb')

# 
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)
        
def lambda_handler(event, context):
    # userテーブルを全て取得
    usertable = dynamodb.Table("user")
    response = usertable.scan()
    
    # 結果を返す
    return {
        'statusCode' : 200,
        'body' : json.dumps(response['Items'], cls=DecimalEncoder),
        'headers' : {
            'content-type' : 'application/json'
        }
    }