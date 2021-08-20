import datetime
from urllib.parse import parse_qs
from flask import render_template, redirect, request, current_app, \
    url_for, g, send_from_directory, abort, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import form
from . import main
from app.models import Article, Tag, Category, article_tag, Recommend, User, \
     InvitationCode, OnlineTool, Comment, OrderLog
from .forms import SearchForm, LoginForm,RegistForm, PasswordForm, InviteRegistForm, \
    CommentForm
from app.ext import db, csrf, alipay
from ..import db, sitemap
from app.util import get_bing_img_url, request_form_auto_fill

def build_template_path(tpl: str) -> str:
    """ 获取模板路径 """
    return '{}/{}'.format(current_app.config['H3BLOG_TEMPLATE'], tpl)

@main.before_request
def before_request():
    if request.endpoint == 'main.static':
    # if '/css/' in request.path or '/js/' in request.path or '/img/' in request.path:
        return
    g.search_form = SearchForm(prefix='search')


@main.route('/', methods=['GET'])
def index():
    page = request.args.get('page', 1, type=int)
    articles = Article.query.filter_by(state=1). \
        order_by(Article.timestamp.desc()). \
        paginate(page, per_page=current_app.config['H3BLOG_POST_PER_PAGE'], error_out=False)

    recommends = Recommend.query.filter(Recommend.state == 1).order_by(Recommend.sn.desc()).all()
    return render_template(build_template_path('index.html'), articles=articles, recommends = recommends)

@main.route('/favicon.ico')
def favicon():
    return main.send_static_file('img/favicon.ico')

@main.route('/hot/',methods=['GET'])
def hot():
    page = request.args.get('page',1,type=int)
    articles = Article.query.filter_by(state=1). \
        order_by(Article.vc.desc()). \
        paginate(page,per_page=current_app.config['H3BLOG_POST_PER_PAGE'],error_out=False)
    recommends = Recommend.query.filter(Recommend.state == 1).order_by(Recommend.sn.desc()).all()
    return render_template(build_template_path('index.html'),articles=articles, recommends = recommends)

@main.route('/about/', methods=['GET', 'POST'])
def about():
    article = Article.query.filter(Article.name=='about-me').first()
    if article :
        article.vc = article.vc + 1
        return render_template('article.html', article=article)
    return render_template(build_template_path('about.html'))


@main.route('/article/<name>/', methods=['GET', 'POST'])
def article(name):
    article = Article.query.filter_by(name=name).first()
    if article is None:
        abort(404)
    article.vc = article.vc + 1
    db.session.commit()
    category = article.category
    tpl_name = category.tpl_page
    return render_template(build_template_path(tpl_name), article=article)

@main.route('/tags/')
def tags():
    tags = Tag.query.all()
    return render_template(build_template_path('tags.html'),tags = tags)


@main.route('/tag/<t>/', methods=['GET'])
def tag(t):
    page = request.args.get('page', 1, type=int)
    tag = Tag.query.filter(Tag.code == t).first()
    articles = tag.articles.filter(Article.state == 1).\
        order_by(Article.timestamp.desc()). \
        paginate(page, per_page=current_app.config['H3BLOG_POST_PER_PAGE'], error_out=False)
    return render_template(build_template_path('tag.html'), articles=articles, tag=tag,orderby='time')

@main.route('/tag/<t>/hot/', methods=['GET'])
def tag_hot(t):
    page = request.args.get('page', 1, type=int)
    tag = Tag.query.filter(Tag.code == t).first()
    articles = tag.articles.filter(Article.state == 1).\
        order_by(Article.vc.desc()). \
        paginate(page, per_page=current_app.config['H3BLOG_POST_PER_PAGE'], error_out=False)
    return render_template(build_template_path('tag.html'), articles=articles, tag=tag,orderby='hot')


@main.route('/category/<c>/', methods=['GET', 'POST'])
def category(c):
    """
    文章分类列表
    """
    cty = Category.query.filter_by(name=c).first()
    tpl_name = cty.tpl_list
    if cty.tpl_mold == 'single_page':
        tpl_name = cty.tpl_page
    return render_template(build_template_path(tpl_name), category=cty,orderby='time')

@main.route('/category/<c>/hot/', methods=['GET', 'POST'])
def category_hot(c):
    cty = Category.query.filter_by(name=c).first()
    tpl_name = cty.tpl_list
    if cty.tpl_mold == 'single_page':
        tpl_name = cty.tpl_mold
    return render_template(build_template_path(tpl_name), category=cty,orderby='hot')

@main.route('/comment/add/', methods=['GET', 'POST'])
@login_required
def comment_add():
    form = CommentForm()
    ret = {}
    ret['code'] = 0
    if form.validate_on_submit():
        c = Comment()
        form.populate_obj(c)
        c.user_id = current_user.id
        db.session.add(c)
        a = Article.query.filter(Article.id == c.article_id).first()
        a.comment_num = a.comments.count()
        db.session.commit()
        ret['code'] = 1
        ret['id'] = c.id

    return jsonify(ret)

@main.route('/archive/',methods=['GET'])
def archive():
    """
    根据时间归档
    """
    articles = Article.query.filter_by(state=1).order_by(Article.timestamp.desc()).all()
    time_tag = []
    current_tag = ''
    for a in articles:
        a_t = a.timestamp.strftime('%Y-%m')
        if  a_t != current_tag:
            tag = dict()
            tag['name'] = a_t
            tag['articles'] = []
            time_tag.append(tag)
            current_tag = a_t
        tag = time_tag[-1]
        tag['articles'].append(a)
    return render_template(build_template_path('archives.html'),time_tag = time_tag)

@main.route('/search/', methods=['POST'])
def search():
    if not g.search_form.validate_on_submit():
        return redirect(url_for('.index'))

    return redirect(url_for('.search_results', query=g.search_form.search.data.strip()))


@main.route('/search_results/<query>', methods=['GET', 'POST'])
def search_results(query):
    page = request.args.get('page', 1, type=int)
    articles = Article.query.filter(Article.content_html.like('%%%s%%' % query), Article.state == 1).order_by(Article.timestamp.desc()). \
        paginate(page, per_page=current_app.config['H3BLOG_POST_PER_PAGE'], error_out=False)
    return render_template(build_template_path('search_result.html'), articles=articles, query=query)

@sitemap.register_generator
def sitemap():
    """
    sitemap生成
    """
    articles = Article.query.filter(Article.state == 1).all()
    categories = Category.query.all()
    tags = Tag.query.all()
    import datetime
    now = datetime.datetime.now()
    #首页
    yield 'main.index',{},now.strftime('%Y-%m-%dT%H:%M:%S'),'always',1.0
    #关于我
    yield 'main.about',{},now.strftime('%Y-%m-%dT%H:%M:%S'),'always',0.5
    #分类
    for category in categories:
        yield 'main.category',{'c':category.name},now.strftime('%Y-%m-%dT%H:%M:%S'),'always',0.9
    for categories in categories:
        yield 'main.category_hot',{'c':category.name},now.strftime('%Y-%m-%dT%H:%M:%S'),'always',0.9
    #标签
    yield 'main.tags',{},now.strftime('%Y-%m-%dT%H:%M:%S'),'always',0.9
    for t in tags:
        yield 'main.tag',{'t':t.code},now.strftime('%Y-%m-%dT%H:%M:%S'),'always',0.9
    for t in tags:
        yield 'main.tag_hot',{'t':t.code},now.strftime('%Y-%m-%dT%H:%M:%S'),'always',0.9

    #文章
    for a in articles:
        #posts.post是文章视图的endpoint,后面是其参数
        yield 'main.article',{'name':a.name}

@main.route('/robots.txt')
def robots():
    return current_app.config['H3BLOG_ROBOTS']

@main.route('/tool/')
def tool():
    tools = OnlineTool.query.order_by(OnlineTool.sn.desc()). \
        filter(OnlineTool.state == True).all()
    return render_template(build_template_path('tool.html'),tools = tools)


@main.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(prefix='login')
    if login_form.validate_on_submit():
        u = User.query.filter_by(username=login_form.username.data.strip()).first()
        if u is None:
            flash({'error': '帐号未注册！'})
        elif u is not None and u.verify_password(login_form.password.data.strip()) and u.status:
            login_user(user=u, remember=login_form.remember_me.data)
            flash({'success':'欢迎{}登陆成功'.format(u.username)})
            return redirect(request.args.get('next',url_for('main.index')))
        elif not u.status:
            flash({'error': '用户已被管理员注销！'})
        elif not u.verify_password(login_form.password.data.strip()):
            flash({'error': '密码不正确！'})

    return render_template(build_template_path('login.html'), form=login_form)

@main.route('/regist', methods=['GET', 'POST'])
def regist():
    '''
    注册
    '''
    is_use_invite_code = current_app.config['H3BLOG_REGISTER_INVITECODE']
    form = RegistForm(prefix='regist')
    if is_use_invite_code:
        form = InviteRegistForm(prefix='regist')
    if form.validate_on_submit(): 
        u = User(username=form.username.data.strip(),
                email=form.email.data.strip(),
                password=form.password.data.strip(),
                status=True, role=False
                )
        db.session.add(u)
        if is_use_invite_code:
            ic = InvitationCode.query.filter(InvitationCode.code == form.code.data.strip()).first()
            if ic :
                ic.user = u.username
                ic.state = False
        
        db.session.commit()
        login_user(user=u)
        flash({'success':'欢迎{}注册成功'.format(u.username)})
        return redirect(request.args.get('next',url_for('main.index')))
    return render_template(build_template_path('regist.html'),form=form)

@main.route('/logout')
@login_required
def logout():
    """退出系统"""
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/profile/',methods=['GET'])
@login_required
def profile():
    '''个人信息'''
    return render_template(build_template_path('profile.html'))

@main.route('/password',methods=['GET','POST'])
def password():
    '''修改密码'''
    form = PasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.pwd.data):
            current_user.password = form.password.data
            db.session.commit()
        flash({'success':'修改密码成功'})
        return redirect(url_for('.profile'))
    return render_template(build_template_path('password.html'),form=form)

@main.route('/pay', methods=['GET', 'POST'])
@login_required
def pay():
    """
    支付
    """
    pay_amount = 100
    from datetime import datetime
    out_trade_no = datetime.now().strftime("%Y%m%d%H%M%S")
    orderLog = OrderLog()
    orderLog.out_trade_no = out_trade_no
    orderLog.user_id = current_user.id
    orderLog.paystate = False
    orderLog.pay_amount = pay_amount
    db.session.add(orderLog)
    db.session.commit()
    qrcode_url = alipay.trade_precreate_qrcode_str(subject='测试',out_trade_no = out_trade_no, total_amount= pay_amount)
    return render_template(build_template_path('pay.html'), qrcode_url=qrcode_url, out_trade_no=out_trade_no)


@main.route('/alipay_nofity', methods=['POST'])
@csrf.exempt
def alipay_nofity():
    data = request.form.to_dict()
    sign = data.pop('sign', None)
    if alipay.verify(data, sign):
        # 通知参数说明 https://docs.open.alipay.com/194/103296#s5
        notify_time = data['notify_time']           # 通知发出的时间
        notify_type = data['notify_type']           # 通知类型
        trade_status = data['trade_status']         # 订单状态
        out_trade_no = data['out_trade_no']         # 订单号
        buyer_logon_id = data['buyer_logon_id']     # 买家支付宝账号
        total_amount = data['total_amount']         # 订单金额
        subject = data['subject']                   # 订单标题
        orderLog = OrderLog.query.filter(OrderLog.out_trade_no == out_trade_no).first()
        if orderLog is not None:
            request_form_auto_fill(orderLog)
            orderLog.paystate = True
            orderLog.notify_time = datetime.datetime.strptime(notify_time, "%Y-%m-%d %H:%M:%S")
            orderLog.callbacktime = datetime.datetime.now()
            db.session.commit()
        return 'success'

    print('验证签名失败')
    return '404'

@main.route('/bing_bg')
def bing_bg():
    '''
    获取背景地址
    '''
    return redirect(get_bing_img_url())