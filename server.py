import requests

easy_ocr_addr = 'https://easyocrgpu-wook-2.endpoint.ainize.ai/word_extraction'

files = [
    ('base_image', open('test_kor.png', 'rb'))
]
data = {'language':'ko'}
headers ={}

response = requests.request("POST", easy_ocr_addr, headers=headers, data=data, files=files)

print(response.text)


