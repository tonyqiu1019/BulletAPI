from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.forms.models import model_to_dict
from django.utils import timezone
import json, collections, datetime

from api.models import *

# internal implementations
class JsonResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        kwargs.setdefault('content_type', 'application/json')
        data = json.dumps(data, ensure_ascii=False)
        super(JsonResponse, self).__init__(content=data, **kwargs)


def _is_hex(str):
    if len(str) != 6: return False
    allowed = ['0','1','2','3','4','5','6','7','8','9',
        'a','b','c','d','e','f']
    for i in range(6):
        if str[i].lower() not in allowed: return False
    return True


def _valid_content(str):
    return len(str) <= 140


# get un-retrieved bullets
def new_bullets(request):
    if request.method != 'GET':
        return HttpResponseBadRequest('bad request type')

    time_now = timezone.now()
    objs = Bullet.objects.filter(post_time=None).exclude(ret_time=None)
    for obj in objs:
        if time_now - obj.ret_time > datetime.timedelta(minutes=5):
            obj.ret_time = None; obj.save()

    objs = Bullet.objects.filter(ret_time=None, post_time=None)
    resp = { 'ok': True, 'bullets': [] }
    for obj in objs:
        obj.ret_time = time_now; obj.save()
        cur = { 'content': obj.content, 'color': obj.color, 'id': obj.id,
            'display_mode': obj.display_mode,'font_size': obj.font_size }
        resp['bullets'].append(cur)
        if len(resp['bullets']) >= 30: break

    return JsonResponse(resp)


# update posted bullets
def success_last_retrieve(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('bad request type')
    try:
        post_dict = json.loads(request.body.decode('utf-8'))
    except:
        return HttpResponseBadRequest('cannot serialize post json')

    if 'id' not in post_dict:
        return HttpResponseBadRequest('bad post key')
    if not isinstance(post_dict['id'], collections.Iterable):
        return HttpResponseBadRequest('key \'id\' is not iterable')

    time_now = timezone.now()
    for item_id in post_dict['id']:
        try:
            obj = Bullet.objects.get(id=item_id)
        except:
            return HttpResponseBadRequest('contains bad item id')
        if (not obj.ret_time is None) and (obj.post_time is None):
            obj.post_time = time_now; obj.save()

    return JsonResponse({ 'ok': True })


# create a new bullet
def create_bullet(request):
    if request.method != 'POST':
        return HttpResponseBadRequest('bad request type')
    try:
        post_dict = json.loads(request.body.decode('utf-8'))
    except:
        return HttpResponseBadRequest('cannot serialize post json')

    if 'content' not in post_dict:
        return HttpResponseBadRequest('please specify content')
    if not _valid_content(post_dict['content']):
        return HttpResponseBadRequest('content cannot pass filter')

    bul = Bullet(content=post_dict['content'])

    if 'color' in post_dict:
        if _is_hex(post_dict['color']):
            bul.color = post_dict['color'].lower()
        else:
            return HttpResponseBadRequest('bad key \'color\'')
    if 'display_mode' in post_dict:
        if post_dict['display_mode'] in ['s', 'f']:
            bul.display_mode = post_dict['display_mode']
        else:
            return HttpResponseBadRequest('bad key \'display_mode\'')
    if 'font_size' in post_dict:
        if isinstance(post_dict['font_size'], int):
            bul.font_size = post_dict['font_size']
        else:
            return HttpResponseBadRequest('bad key \'font_size\'')
    if 'info' in post_dict:
        bul.info = Info.objects.create(content=post_dict['info'])

    bul.save()
    """
    try:
        bul.save()
    except:
        return HttpResponseBadRequest('cannot save the bullet')
    """
    return JsonResponse({ 'ok': True })
