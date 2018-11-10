from django.http import HttpResponse, HttpResponseBadRequest

from hashlib import sha1
from lxml import etree

import urllib.request
import json

# BULLET_API_URL = 'https://danmu-183606.appspot.com/api/create/'
BULLET_API_URL = 'https://ssserver-190705.appspot.com/api/create/'

FIRST_MSG = (
    '欢迎关注UVA CSSS微信公众号！\n',
    '今晚的好声音决赛中，我们将使用此公众号为观众提供弹幕互动和投票功能，请按照\n',
    '\"弹幕 想发送的内容\"\n',
    '格式发送弹幕。今晚的比赛结束后，你将有机会为自己最喜欢的三位选手投票。',
    '届时请输入\"投票\"关键字获取链接，你的投票将直接决定最终入围UVa好声音决赛的选手阵容！',
)
TUTORIAL = '发送弹幕请参考：http://mp.weixin.qq.com/s/pPOxYWzgmnXjWN6Dienf6Q'
VOTE = (
    '请点击：http://mp.weixin.qq.com/s?__biz=MzA5MTg5MDI2Mg==&mid=542807876&idx=1&sn=e1e7ad23db236c41c21700f72d6fcf4d&chksm=35db407d02acc96bb7d80871304540b94a06a71f6edeb87d63b2f2e4145c988a8df857a4c946#rd ',
    '为自己最喜欢的组合投票',
)

SUCCESS = '弹幕发送成功！'
_FAIL = '回复\"高级弹幕\"或\"教程\"获取发弹幕教程，或回复\"投票\"参与投票'
NON_TEXT = '目前仅支持文本信息，请按\n\"弹幕 想发送的内容\"\n格式发弹幕。' + _FAIL
BAD_FORMAT = '消息格式似乎不对哦，请按\n\"弹幕 想发送的内容\"\n格式发弹幕。' + _FAIL
NON_EMPTY = '不能发送空弹幕，请按\n\"弹幕 想发送的内容\"\n格式发弹幕。' + _FAIL
FORBIDDEN = '你已被禁言，请联系管理员，询问情况后再试。' + _FAIL
SERVER_ERR = 'oops，你的弹幕发送失败了...请稍等片刻再试哦！' + _FAIL


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
        return HttpResponse('')

    if msg_type == 'event':
        try:
            event = tree.xpath('/xml/Event')[0].text
            if event == 'subscribe':
                return _reply(to_name, from_name, create_time, FIRST_MSG)
            else:
                return HttpResponse('')
        except:
            return HttpResponse('')
    elif msg_type != 'text':
        return _reply(to_name, from_name, create_time, NON_TEXT)

    try:
        content = tree.xpath('/xml/Content')[0].text
    except:
        return HttpResponse('')

    if content == '高级弹幕' or content == '教程':
        return _reply(to_name, from_name, create_time, TUTORIAL)
    if content == '投票':
        return _reply(to_name, from_name, create_time, VOTE)

    if len(content) <= 2 or content[:2] != '弹幕':
        return _reply(to_name, from_name, create_time, BAD_FORMAT)
    bul = content[2:]
    if len(bul) == 0:
        return _reply(to_name, from_name, create_time, NON_EMPTY)
    if bul[0] != ' ':
        return _reply(to_name, from_name, create_time, BAD_FORMAT)
    bul = bul.strip()
    if len(bul) == 0:
        return _reply(to_name, from_name, create_time, NON_EMPTY)

    post_data = { 'content': bul, 'fingerprint': '#'+from_name }
    try:
        resp = _make_post_request(BULLET_API_URL, post_data)
        if resp['ok']:
            return _reply(to_name, from_name, create_time, SUCCESS)
        else:
            return _reply(to_name, from_name, create_time, FORBIDDEN)
    except:
        return _reply(to_name, from_name, create_time, SERVER_ERR)


def index_page(request):
    if request.method == 'GET': return _check_token(request)
    if request.method == 'POST': return _handle_reply(request)
    return HttpResponseBadRequest('bad request type')
