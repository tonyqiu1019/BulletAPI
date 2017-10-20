from django.http import HttpResponse, HttpResponseBadRequest

from hashlib import sha1

def index_page(request):
    get_dict = request.GET.dict()
    needed_token = ['signature', 'timestamp', 'nonce', 'echostr']
    for token in needed_token:
        if token not in get_dict:
            return HttpResponseBadRequest('invalid tokens')

    my_token = 'uvacsssvoice'
    arr = [my_token, get_dict['timestamp'], get_dict['nonce']].sort()
    before_hash = arr[0] + arr[1] + arr[2]
    after_hash = sha1(before_hash.encode('utf-8')).hexdigest()

    if after_hash == get_dict['signature']:
        return HttpResponse(get_dict['echostr'])
    else:
        return HttpResponseBadRequest('something went wrong')
