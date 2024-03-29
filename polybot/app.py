import flask
from flask import request
import os
from bot import ObjectDetectionBot
import boto3
from botocore.exceptions import ClientError
import json
import signal
import sys

app = flask.Flask(__name__)

TELEGRAM_APP_URL = os.environ['TELEGRAM_APP_URL']
REGION_NAME = os.environ['REGION_NAME']


# TODO load TELEGRAM_TOKEN value from Secret Manager
def get_secret():
    secret_name = "MoshikoSecret"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=REGION_NAME
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = json.loads(get_secret_value_response['SecretString'])
    secret_value = secret['TELEGRAM_TOKEN']
    return secret_value


TELEGRAM_TOKEN = get_secret()

# variable for server readiness
server_ready = True


@app.route('/', methods=['GET'])
def index():
    return 'Ok'


@app.route(f'/{TELEGRAM_TOKEN}/', methods=['POST'])
def webhook():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'


@app.route(f'/results/', methods=['GET'])
def results():
    prediction_id = request.args.get('predictionId')
    chat_id = request.args.get('chatId')
    # TODO use the prediction_id to retrieve results from DynamoDB and send to the end-user
    dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
    table = dynamodb.Table('Moshiko_Yolo')

    try:
        response = table.get_item(
            Key={
                'prediction_id': prediction_id,
                'ChatID': chat_id,
            }
        )
        item = response.get('Item')
        if item:
            text_results = item
            bot.send_text(chat_id, text=str(text_results))
            return 'Results sent to the user'
        else:
            return 'No results found for the given prediction ID'
    except Exception as e:
        return f'Error: {str(e)}'


@app.route(f'/loadTest/', methods=['POST'])
def load_test():
    req = request.get_json()
    bot.handle_message(req['message'])
    return 'Ok'


@app.route('/ready', methods=['GET'])
def ready():
    if server_ready:
        return 'Server is ready', 200
    else:
        return 'Server is not ready', 503


def signal_handler(sig, frame):
    global server_ready
    print('Shutting down gracefully...')
    server_ready = False
    # Perform cleanup tasks here if needed
    sys.exit(0)


signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    bot = ObjectDetectionBot(TELEGRAM_TOKEN, TELEGRAM_APP_URL)

    app.run(host='0.0.0.0', port=8443)
