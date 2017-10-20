from django.http import HttpResponse, HttpResponseBadRequest

from hashlib import sha1
from lxml import etree

def _check_token(request):
    get_dict = request.GET.dict()
    needed_token = ['signature', 'timestamp', 'nonce', 'echostr']
    for token in needed_token:
        if token not in get_dict:
            return HttpResponseBadRequest('invalid tokens')

    my_token = 'uvacsssvoice'
    arr = [my_token, get_dict['timestamp'], get_dict['nonce']]
    arr.sort()
    before_hash = arr[0] + arr[1] + arr[2]
    after_hash = sha1(before_hash.encode('utf-8')).hexdigest()

    if after_hash == get_dict['signature']:
        return HttpResponse(get_dict['echostr'])
    else:
        return HttpResponseBadRequest('something went wrong')


def index_page(request):
    if request.method == 'GET':
        return _check_token(request)

    if request.method == 'POST':
        tree = etree.fromstring(request.body.decode('utf-8'))
        ret_tree = etree.Element('xml')
        etree.SubElement(ret_tree, 'ToUserName').text = tree.xpath('/xml/FromUserName')[0].text
        etree.SubElement(ret_tree, 'FromUserName').text = tree.xpath('/xml/ToUserName')[0].text
        etree.SubElement(ret_tree, 'CreateTime').text = tree.xpath('/xml/CreateTime')[0].text
        etree.SubElement(ret_tree, 'MsgType').text = tree.xpath('/xml/MsgType')[0].text
        etree.SubElement(ret_tree, 'Content').text = '你好'
        ret = etree.tostring(ret_tree, pretty_print=True, encoding='unicode')
        return HttpResponse(ret, content_type='application/xml')
