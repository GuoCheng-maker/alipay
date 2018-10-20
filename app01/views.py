from django.shortcuts import render,redirect,HttpResponse
from utils.pay import AliPay
import time
from app01 import models
# Create your views here.

def aliPay():
    alipay=AliPay(
        appid="2016092200569287",
        app_notify_url="http://119.27.182.182:8000/update_order/",   #如果支付成功，支付宝会向这个地址发送POST请求,（校验是否支付成功）
        return_url="http:/119.27.182.182:8000/pay_result/",       #如果支付成功，跳转的页面
        app_private_key_path="keys/app_private_2048.txt",    #应用私钥
        alipay_public_key_path="keys/alipay_public_2048.txt",#支付宝公钥
        debug=True   #默认false
    )
    return alipay



def index(request):
    if request.method == "GET":
        return render(request,'index.html')

    #实例化alipay对象
    alipay=aliPay()


    money=float(request.POST.get("price"))
    subject="iPhone XS Max(512GB)"
    out_trade_no = "x2" + str(time.time())   #订单号
    #在数据库创建一条数据：状态(待支付)
    models.Order.objects.create(title=subject,order_num=out_trade_no,status=1)

    print(money)
    #价格，购买的商品加密，拼接成URL

    query_params=alipay.direct_pay(
        subject=subject,     #商品描述
        out_trade_no=out_trade_no, #随机生成商户订单号
        total_amount=money,                 #交易金额（单位：元 保留2位小数）
    )

    pay_url="https://openapi.alipaydev.com/gateway.do?{}".format(query_params)
    return redirect(pay_url)



def pay_result(request):
    params=request.GET.dict()
    sign=params.pop('sign',None)

    alipay = aliPay()
    status=alipay.verify(params,sign)          #进行是否真正支付进行验证
    if status:
        #校验是否是阿里返回的数据，而不是别人伪造的
        return HttpResponse("支付成功")
    else:
        return HttpResponse("支付失败")



from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def update_order(request):
    '''
    支付成功后，支付宝向该地址发送POST请求（用于修改订单状态）
    :param rqeuest:
    :return:
    '''
    if request.method=='POST':
        from urllib.parse import parse_qs
        body_str=request.body.decode('utf-8')
        post_data=parse_qs(body_str)

        post_dict={}
        for k,v in post_data.items():
            post_dict[k]=v[0]
        print(post_dict)

        sign=post_dict.pop('sign',None)
        alipay = aliPay()

        status=alipay.verify(post_dict,sign)
        if status:
            print(post_dict)
            #返回前更改一下订单状态
            #models.object.filter().update()

            #订单号：
            out_trade_no=post_dict.get("out_trade_no")
            print(out_trade_no)
            #拿到这个订单号对数据库的数据把订单改为已支付。
            models.Order.objects.filter(order_num=out_trade_no).update(status=2)
            return HttpResponse("支付成功！")
        else:
            return HttpResponse("支付失败!")
