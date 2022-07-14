from flask import Flask, request, jsonify
from flask_restful import Api
import json
import eth_account
import algosdk

app = Flask(__name__)
api = Api(app)
app.url_map.strict_slashes = False


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    content = request.get_json(silent=True)

    info = {'platform': content['payload']['platform'],
            'message': json.dumps(content['payload']),
            'public_key': content['payload']['pk'],
            'secret_key': content['sig']}

    if (info['platform'] == 'Algorand' and algosdk.util.verify_bytes(info['message'].encode('utf-8'),
                                                                     info['secret_key'], info['public_key'])) or (
            info['platform'] == 'Ethereum' and eth_account.Account.recover_message(
            eth_account.messages.encode_defunct(text=info['message']), signature=info['secret_key']) == info[
                'public_key']):

        return jsonify(True)

    return jsonify(False)


if __name__ == '__main__':
    app.run(port='5002')
