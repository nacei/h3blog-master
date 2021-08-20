# -*- coding: utf-8 -*-
import os
import sys
import hashlib
from flask import current_app, render_template
from flask.app import Flask

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


class BaseConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY') or hashlib.new(name='md5', data=b'h3blog python@#').hexdigest()

    DEBUG_TB_INTERCEPT_REDIRECTS = False

    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ECHO = False

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('H3BLOG Admin', MAIL_USERNAME)

    H3BLOG_TITLE = os.getenv('H3BLOG_TITLE','何三笔记')
    H3BLOG_DOMAIN = os.getenv('H3BLOG_DOMAIN','www.h3blog.com')
    H3BLOG_KEYWORDS = os.getenv('H3BLOG_KEYWORDS','python,flask,个人博客')
    H3BLOG_DESCRIPTION = os.getenv('H3BLOG_DESCRIPTION','一个注重创作的轻博客系统，选用python语言flask框架开发，前端采用bootstrap4轻量模板，注重内容创作与工具开发 ')
    H3BLOG_EMAIL = os.getenv('H3BLOG_EMAIL','')
    H3BLOG_POST_PER_PAGE = 10
    H3BLOG_MANAGE_POST_PER_PAGE = 15
    H3BLOG_COMMENT_PER_PAGE = 15
    H3BLOG_SLOW_QUERY_THRESHOLD = 1
    H3BLOG_REGISTER_INVITECODE = os.getenv('H3BLOG_REGISTER_INVITECODE',False)   # 是否开启邀请码注册
    H3BLOG_COMMENT = os.getenv("H3BLOG_COMMENT", False) # 是否开发评论，默认不开启
    H3BLOG_EDITOR = os.getenv('H3BLOG_EDITOR', 'markdown') # 默认编辑器
    H3BLOG_TEMPLATE = os.getenv('H3BLOG_TEMPLATE', 'tend') # 前端模板

    H3BLOG_UPLOAD_TYPE = os.getenv('H3BLOG_UPLOAD_TYPE','') # 默认本地上传
    H3BLOG_UPLOAD_PATH = os.path.join(basedir, 'uploads')
    H3BLOG_ALLOWED_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'webp']
    H3BLOG_TONGJI_SCRIPT = os.getenv('H3BLOG_TONGJI_SCRIPT','') #统计代码
    H3BLOG_EXTEND_META = os.getenv('H3BLOG_EXTEND_META', '') # 扩展META
    H3BLOG_ROBOTS = os.getenv('H3BLOG_ROBOTS', 'User-agent: *\nAllow: /') # 网站robots定义

    MAX_CONTENT_LENGTH = 32 * 1024 * 1024

    QINIU_CDN_URL = os.getenv('QINIU_CDN_URL','http://cdn.h3blog.com/')
    QINIU_BUCKET_NAME = os.getenv('QINIU_BUCKET_NAME','h3blog')
    QINIU_ACCESS_KEY = os.getenv('QINIU_ACCESS_KEY','key123')
    QINIU_SECRET_KEY = os.getenv('QINIU_SECRET_KEY','secret456')

    BAIDU_PUSH_TOKEN = os.getenv('BAIDU_PUSH_TOKEN') #主动推送给百度链接，token是在搜索资源平台申请的推送用的准入密钥

    SITEMAP_URL_SCHEME = os.getenv('SITEMAP_URL_SCHEME','http')
    SITEMAP_MAX_URL_COUNT = os.getenv('SITEMAP_MAX_URL_COUNT',100000)

    ALIPAY_APPID= os.getenv('ALIPAY_APPID', '') # 设置签约的appid
    ALIPAY_PUBLIC_KEY = os.getenv('ALIPAY_PUBLIC_KEY', '') # 支付宝公钥
    ALIPAY_PRIVATE_KEY =os.getenv('ALIPAY_PRIVATE_KEY', '') # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥
    ALIPAY_DEBUG = os.getenv('ALIPAY_DEBUG', True)
    ALIPAY_NOTIFY_URL = os.getenv('ALIPAY_NOTIFY_URL', '')
    

    

class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', prefix + os.path.join(basedir, 'data-dev.db'))

class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # in-memory database


class ProductionConfig(BaseConfig):
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', prefix + os.path.join(basedir, 'data.db'))
    pass

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

def exist_config() -> bool:
    return _exist_config(current_app)


def _exist_config(app: Flask) -> bool:
    filename = "{}/config.py".format(app.root_path)
    return os.path.exists(filename)


def create_config(db_uri:str) -> None:
    config_name = current_app.config['CONFIG_NAME']
    import_config = 'ProductionConfig'
    if config_name == 'development':
        import_config = 'DevelopmentConfig'
    elif config_name == 'testing':
        import_config = 'TestingConfig'
    data = render_template("config.tpl", db_uri = db_uri, import_config = import_config)
    filename = '{}/config.py'.format(current_app.root_path)
    with open(filename, 'w') as f:
        f.write(data)

if __name__ == "__main__":
    pass