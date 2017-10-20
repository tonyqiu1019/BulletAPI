from django.http import HttpResponse, HttpResponseBadRequest

from hashlib import sha1
from lxml import etree

import urllib.request
import json

def _make_get_request(url):
    req = urllib.request.Request(url)
    resp_json = urllib.request.urlopen(req).read().decode('utf-8')
    resp = json.loads(resp_json)
    return resp


def _make_post_request(url, post_data):
    post_encoded = urllib.parse.urlencode(post_data).encode('utf-8')
    req = urllib.request.Request(url, data=post_encoded, method='POST')
    resp_json = urllib.request.urlopen(req).read().decode('utf-8')
    resp = json.loads(resp_json)
    return resp


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


def _reply(from_name, to_name, create_time, msg_type, content):
    ret = etree.Element('xml')
    etree.SubElement(ret, 'FromUserName').text = from_name
    etree.SubElement(ret, 'ToUserName').text = to_name
    etree.SubElement(ret, 'CreateTime').text = create_time
    etree.SubElement(ret, 'MsgType').text = msg_type
    etree.SubElement(ret, 'Content').text = content

    ret_str = etree.tostring(ret, pretty_print=True, encoding='unicode')
    return HttpResponse(ret_str, content_type='application/xml')


def _handle_reply(request):
    tree = etree.fromstring(request.body.decode('utf-8'))
    try:
        from_name = tree.xpath('/xml/FromUserName')[0].text
        to_name = tree.xpath('/xml/ToUserName')[0].text
        create_time = tree.xpath('/xml/CreateTime')[0].text
        msg_type = tree.xpath('/xml/MsgType')[0].text
    except:
        return HttpResponseBadRequest('cannot parse correct xml')

    if msg_type != 'text':
        txt = '弹幕仅支持文本信息，请按\n\"弹幕 想发送的内容\"\n格式发弹幕'
        return _reply(to_name, from_name, create_time, msg_type, txt)

    if len(content) <= 2 or content[:2] != '弹幕':
        txt = '你的弹幕格式似乎不对哦，请按\n\"弹幕 想发送的内容\"\n格式发弹幕'
        return _reply(to_name, from_name, create_time, msg_type, txt)

    bullet_txt = content[2:].strip()
    if len(bullet_txt) == 0:
        txt = '不能发送空弹幕，请按\n\"弹幕 想发送的内容\"\n格式发弹幕'
        return _reply(to_name, from_name, create_time, msg_type, txt)
    else:
        txt = '你发送的弹幕信息是：' + bullet_txt
        return _reply(to_name, from_name, create_time, msg_type, txt)


def index_page(request):
    if request.method == 'GET': return _check_token(request)
    if request.method == 'POST': return _handle_reply(request)
    return HttpResponseBadRequest('bad request type')
