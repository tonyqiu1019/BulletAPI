from django.http import HttpResponse, HttpResponseBadRequest

from hashlib import sha1
from lxml import etree

import urllib.request
import json

def _make_post_request(url, post_data):
    post_encoded = json.dumps(post_data).encode('utf-8')
    req = urllib.request.Request(url, data=post_encoded, method='POST')
    req.add_header('Content-Type', 'application/json')
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


def _reply(from_name, to_name, create_time, content):
    ret = etree.Element('xml')
    etree.SubElement(ret, 'FromUserName').text = from_name
    etree.SubElement(ret, 'ToUserName').text = to_name
    etree.SubElement(ret, 'CreateTime').text = create_time
    etree.SubElement(ret, 'MsgType').text = 'text'
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

    if msg_type == 'event':
        try:
            event = tree.xpath('/xml/Event')[0].text
            if event == 'subscribe':
                txt = '欢迎关注UVA CSSS微信公众号！\n今晚的好声音活动中，我们将使用此公众号为观众提供弹幕互动和投票功能，请按照\n\"弹幕 想发送的内容\"\n格式发弹幕，或回复\"投票\"为喜欢的歌手投票！\n感谢你的参与！'
                return _reply(to_name, from_name, create_time, txt)
            else:
                return HttpResponse('')
        except:
            return HttpResponse('')
    elif msg_type != 'text':
        txt = '目前仅支持文本信息，请按\n\"弹幕 想发送的内容\"\n格式发弹幕，或回复\"投票\"为喜欢的歌手投票'
        return _reply(to_name, from_name, create_time, txt)

    try:
        content = tree.xpath('/xml/Content')[0].text
    except:
        return HttpResponseBadRequest('cannot parse correct xml')

    if content == '投票':
        txt = '投票链接暂未开放，请等待比赛结束后统一为自己喜欢的选手投票哦！'
        return _reply(to_name, from_name, create_time, txt)

    if len(content) <= 2 or content[:2] != '弹幕':
        txt = '你的消息格式似乎不对哦，请按\n\"弹幕 想发送的内容\"\n格式发弹幕，或回复\"投票\"为喜欢的歌手投票'
        return _reply(to_name, from_name, create_time, txt)

    bul = content[2:]
    if len(bul) == 0:
        txt = '不能发送空弹幕，请按\n\"弹幕 想发送的内容\"\n格式发弹幕'
        return _reply(to_name, from_name, create_time, txt)
    if bul[0] != ' ':
        txt = '你的消息格式似乎不对哦，请按\n\"弹幕 想发送的内容\"\n格式发弹幕，或回复\"投票\"为喜欢的歌手投票'
        return _reply(to_name, from_name, create_time, txt)

    bul = bul.strip()
    if len(bul) == 0:
        txt = '不能发送空弹幕，请按\n\"弹幕 想发送的内容\"\n格式发弹幕'
        return _reply(to_name, from_name, create_time, txt)

    post_url = 'https://danmu-183606.appspot.com/api/create/'
    post_data = { 'content': bul, 'fingerprint': '#'+from_name }

    try:
        resp = _make_post_request(post_url, post_data)
        if resp['ok']:
            txt = '弹幕发送成功！'
            return _reply(to_name, from_name, create_time, txt)
        else:
            txt = '你已被禁言，请联系管理员，询问情况后再试'
            return _reply(to_name, from_name, create_time, txt)
    except:
        txt = 'oops，你的弹幕发送失败了...请稍等片刻再试哦'
        return _reply(to_name, from_name, create_time, txt)


def index_page(request):
    if request.method == 'GET': return _check_token(request)
    if request.method == 'POST': return _handle_reply(request)
    return HttpResponseBadRequest('bad request type')
