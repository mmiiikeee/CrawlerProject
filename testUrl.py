import urllib.request

# init url
url = "https://tieba.baidu.com/p/5107094720"

with urllib.request.urlopen(url) as reponse:
    page = reponse.read()

print(page)