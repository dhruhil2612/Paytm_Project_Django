from django.shortcuts import render
from .models import * 
from .paytm import generate_checksum, verify_checksum
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def login(request):
    if request.POST:
        email = request.POST['email']
        password = request.POST['password']
        uid = User.objects.get(email=email)
        if uid:
            if uid.password== password:
                return render(request,"myapp/pay.html",{'uid':uid})
        
    else:
        return render(request,"myapp/home.html")

def initiate_payment(request):
    if request.method == "GET":
        return render(request, 'myapp/pay.html')
    try:
        username = request.POST['username']
        amount = int(request.POST['amount'])
        uid=User.objects.get(email=username)
    except:
        return render(request, 'myapp/pay.html', context={'error': 'Wrong Accound Details or amount'})

    transaction = Transaction.objects.create(made_by=uid, amount=amount)
    transaction.save()
    merchant_key = settings.PAYTM_SECRET_KEY

    params = (
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str(transaction.made_by.email)),
        ('TXN_AMOUNT', str(transaction.amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        # ('EMAIL', request.user.email),
        # ('MOBILE_N0', '9911223388'),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', 'http://127.0.0.1:8000/myapp/callback/'),
        # ('PAYMENT_MODE_ONLY', 'NO'),
    )

    paytm_params = dict(params)
    checksum = generate_checksum(paytm_params, merchant_key)

    transaction.checksum = checksum
    transaction.save()

    paytm_params['CHECKSUMHASH'] = checksum
    print('SENT: ', checksum)
    return render(request, 'myapp/redirect.html', context=paytm_params)


@csrf_exempt
def callback(request):
    if request.method == 'POST':
        received_data = dict(request.POST)
        paytm_params = {}
        paytm_checksum = received_data['CHECKSUMHASH'][0]
        for key, value in received_data.items():
            if key == 'CHECKSUMHASH':
                paytm_checksum = value[0]
            else:
                paytm_params[key] = str(value[0])
        # Verify checksum
        is_valid_checksum = verify_checksum(paytm_params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
        if is_valid_checksum:
            received_data['message'] = "Checksum Matched"
        else:
            received_data['message'] = "Checksum Mismatched"
            return render(request, 'myapp/callback.html', context=received_data)
        return render(request, 'myapp/callback.html', context=received_data)

