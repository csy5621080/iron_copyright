import oss2
import posixpath
import os
from django.core.files.storage import Storage
from django.conf import settings
from urllib.parse import urljoin
from django.utils.encoding import force_str, force_bytes
from django.core.files import File
from django.utils.module_loading import import_string
from io import BytesIO
from pypinyin import lazy_pinyin, Style


"""
    阿里云OSS集成
    1. settings.py内新增配置
        1>. Storage 配置
        DEFAULT_FILE_STORAGE = 'utils.AliYunOSS2Storage'
        STATICFILES_STORAGE = 'utils.AliYunOSS2Storage'
        2>. OSS Access key 配置
        OSS2_ACCESS_KEY_ID = "oss2_access_key_id"
        OSS2_ACCESS_KEY_SECRET = "oss2_access_key_secret"
        OSS2_END_POINT = "example.aliyuncs.com"
        OSS2_BUCKET_NAME = "oss2_bucket_name"
    2. Django Model Field写法
        
        from utils.aliyun_oss import get_image_path
        
        class DemoModel(models.Model):
            ...
            avatar = models.ImageField(u"用户头像", upload_to=get_image_path, null=True, blank=True)
            ...
        
        * FileField类型的字段的 upload_to 参数配置为 get_image_path方法
"""


class AliYunOSS2Storage(Storage):

    def __init__(self):
        self.location = settings.MEDIA_URL
        self.access_key_id = settings.OSS2_ACCESS_KEY_ID
        self.access_key_secret = settings.OSS2_ACCESS_KEY_SECRET
        self.end_point = settings.OSS2_END_POINT
        self.bucket_name = settings.OSS2_BUCKET_NAME

        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.service = oss2.Service(self.auth, self.end_point, connect_timeout=30)
        self.bucket = oss2.Bucket(self.auth, self.end_point, self.bucket_name)

        self.FileMode = AliYunOSS2File

    @staticmethod
    def _clean_name(name):
        clean_name = posixpath.normpath(name).replace('\\', '/')

        if name.endswith('/') and not clean_name.endswith('/'):
            return clean_name + '/'
        else:
            return clean_name

    def _normalize_name(self, name):

        base_path = force_str(self.location)
        base_path = base_path.rstrip('/')

        final_path = urljoin(base_path.rstrip('/') + "/", name)

        base_path_len = len(base_path)
        if not final_path.startswith(base_path) or final_path[base_path_len:base_path_len + 1] not in ('', '/'):
            raise Exception("Attempted access to '%s' denied." % name)
        return final_path.lstrip('/')

    def _get_target_name(self, name):
        return self._normalize_name(self._clean_name(name))

    def _open(self, name, mode='rb'):
        return self.FileMode(name)

    def save(self, name, content, max_length=None):
        return self._save(name, content)

    def _save(self, name, content):
        file_name = self._get_target_name(name)
        content.open()
        content_str = b''.join(chunk for chunk in content.chunks())
        self.bucket.put_object(file_name, content_str)
        content.close()
        return file_name

    def path(self, name):
        return self._get_target_name(name)

    def delete(self, name):
        name = self._get_target_name(name)
        self.bucket.delete_object(name)

    def exists(self, name):
        return self.bucket.object_exists(name)

    def listdir(self, path):
        name = self._get_target_name(path)
        if name and name.endswith('/'):
            name = name[:-1]

        files = []
        dirs = set()
        for obj in oss2.ObjectIterator(self.bucket, prefix=name, delimiter='/'):
            if obj.is_prefix():
                dirs.add(obj.key)
            else:
                files.append(obj.key)
        return list(dirs), files

    def size(self, name):
        obj = self.bucket.get_object(name)
        raise obj.size()

    def url(self, name):
        url = getattr(self.bucket, 'sign_url')('GET', name, 24*3600)
        return url

    def get_accessed_time(self, name):
        pass

    def get_created_time(self, name):
        pass

    def get_modified_time(self, name):
        pass


class AliYunOSS2File(File):

    def __init__(self, name):
        self._storage = AliYunOSS2Storage()
        self._name = name[len(self._storage.location):]
        self.file = BytesIO()
        self._reading = False
        self._dirty = False
        super(AliYunOSS2File, self).__init__(self.file, self._name)

    def read(self):
        if not self._reading:
            self.file = BytesIO(self._storage.bucket.get_object(self._name).read())
            self._reading = True
        return self.file.read()

    def write(self, content):
        self.file.write(force_bytes(content))
        self._dirty = True
        self._reading = True

    def close(self):
        if self._dirty:
            self.file.seek(0)
            self._storage.save(self._name, self.file)
        self.file.close()


def get_image_path(instance, filename):
    """
    获取图片的保存位置
    暂定以company.cid为单位
    """
    module_name = instance.__class__.__name__.lower()

    suffix = filename.split(".")[-1]

    if module_name == 'company':
        return f'{instance.domain_name}/{filename}'
    elif module_name == 'application':
        return f'{instance.company.domain_name}/app_logo/{instance.uuid}.{suffix}'
    elif module_name == 'user':
        return f'user_avatar/{instance.uuid}.{suffix}'
    elif module_name == 'app_store':
        return f'software_icon/{instance.name}.{suffix}'


def image_storage(field, file, object_id, company_id, call_path):
    """
    将图片保存到数据库对应的字段
    :param field: 待更新字段名
    :param file: 文件
    :param object_id: 待更新的数据ID
    :param company_id: 调用者所属企业ID
    :param call_path: 调用来源，一般传入__file__
    :return: dict
    """
    module_name = os.path.basename(os.path.dirname(call_path))
    module = import_string(f'apps.{module_name}.models.{module_name.capitalize()}')
    if module_name == "user":
        instance = module.objects.filter(id=object_id).first()
    else:
        instance = module.objects.filter(id=object_id, company_id=company_id).first()

    if not instance:
        raise ModuleNotFoundError()

    if hasattr(instance, field):
        setattr(instance, field, file)
        instance.save()  # TODO: 过期图片清理方式待定
        return {'img_url': getattr(instance, field).url}
    else:
        raise AttributeError()


def get_letters(text):
    """
        获取文本拼音首字母组成的字符串
        Args:
            text: 文本
        Returns:
            str: 拼音首字母组成的字符串
    """
    letters = ''
    letters_list = lazy_pinyin(text, style=Style.FIRST_LETTER)
    for letter in letters_list:
        letters += letter
    return letters.upper()
