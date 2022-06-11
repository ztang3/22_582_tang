import requests
import json

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	#YOUR CODE HERE

	payload = json.dumps(data)

	keys = {'API Key': '7d69306c401bd8ef8d4b', 'API Secret':'085bfe44590d896f11fc78c09eed8a81e6a2767ed352ab90139d70b9cf20a61d'}

	url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"

	headers = {'Content-Type': 'application/json',"pinata_api_key": keys["API Key"], "pinata_secret_api_key": keys["API Secret"]}

	response = requests.request("POST", url, headers=headers, data=payload)

	# print(response.text)
	cid = response.json()["IpfsHash"]
	# print(cid)

	return cid

def get_from_ipfs(cid,content_type="json"):

	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"

	url = 'https://gateway.pinata.cloud/ipfs/' + cid
	data = requests.get(url).json()

	assert isinstance(data, dict), f"get_from_ipfs should return a dict"

	return data
