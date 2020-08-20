from locust import HttpUser, TaskSet, task, between
import random, uuid, time, io, requests, urllib, os, base64, json

IMAGES = [
    'https://raw.githubusercontent.com/Wook-2/ImageReader/locust/static/menu.jpg',
    'https://raw.githubusercontent.com/Wook-2/ImageReader/locust/static/roadSign.jpeg',
    'https://raw.githubusercontent.com/Wook-2/ImageReader/locust/static/roadsign2.jpeg',
    'https://raw.githubusercontent.com/Wook-2/ImageReader/locust/static/signboard.jpg',
    'https://raw.githubusercontent.com/Wook-2/ImageReader/locust/static/signboard2.jpg'
]

responsetime = 0 
response200 = 0

def getFilenameFromURL(url):
    parsedUrl = urllib.parse.urlparse(url)
    return os.path.basename(parsedUrl.path)

def fileopen(image):
    fetched = requests.get(image)
    f_image = (
        getFilenameFromURL(image),
        io.BytesIO(fetched.content),
    )
    return f_image

class UserBehavior(TaskSet):
    @task
    def ITS(self):
        global responsetime, response200
        response_aver = 0

        req_id = str(uuid.uuid4())
        image = random.choice(IMAGES)

        index = IMAGES.index(image)

        image_bytes = fileopen(image)

        start = time.time()
        response = self.client.post(
            "/upload",
            files={
                'file': image_bytes,
            }
        )
        duration = time.time() - start

        if response.status_code == 200:
            response200 += 1
            responsetime += duration
        if response200 > 0:
            response_aver = responsetime/response200
        print(('out', req_id, duration, index, response.status_code, response_aver))

TARGET_RPS = 1

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]

    def wait_time(self):
        target_wait = between(0, 2 / TARGET_RPS)(self)  
        print(("wait", target_wait))
        return target_wait
