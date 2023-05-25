
from substrateinterface import SubstrateInterface
import csv
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import datetime

receivers = ["youremail@gmail.com"]
simple = 'DOT'



def transfer_alert(filename,address):
    print(address)
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
    # 遍历所有行
        count = 0
    
        for row in reader:
            if row[0] == address:
                count = count + 1
                break
            else:
                continue
        return (count)

def account_balance(address):
    result = substrate.query('System', 'Account', [address])
    account_balance = result.value['data']['free']
    account_balance = float(account_balance/10000000000)
    return(account_balance)
    
            
def send_transfer_email(from_or_to_code,from_address, to_address, amount,receivers):
    # 邮件发送方邮箱地址和密码
    sender = '12342@foxmail.com'
    password = 'nnnnnn'

    # 邮件接收方邮箱地址
    #receivers = ['receiver@receiver_domain.com']

    # 邮件内容
    if from_or_to_code == 1:
        from_address_balance = account_balance(from_address)
        message = f"[*SENT ALERT*]Transfer from {from_address} to {to_address} with {amount} {simple}\n \nThe balance of the {from_address} is {from_address_balance} {simple} right now"
    elif from_or_to_code ==2:
        to_address_balance = account_balance(to_address)
        message = f"[*RECIVE ALERT*]Transfer from {from_address} to {to_address} with {amount} {simple}\n \nThe balance of the {to_address} is {to_address_balance} {simple} right now"
        
    

    # 创建一个邮件内容对象
    subject = "Transfer Notification"
    content = MIMEText(message, 'plain')
    content['From'] = sender
    content['To'] = ", ".join(receivers)
    content['Subject'] = Header(subject, 'utf-8')
    
    # 发送邮件
    try:
        smtpObj = smtplib.SMTP_SSL('smtp.qq.com',465)
        smtpObj.login(sender, password)
        smtpObj.sendmail(sender, receivers, content.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException:
        print("Error: 无法发送邮件")



def subscription_transfers(storage_key, updated_obj, update_nr, subscription_id):
    events = updated_obj.value
    #获取当前时间
    current_time = datetime.datetime.now()

    for event in events:
        if 'event' in event:
            attributes = event['event']['attributes']
            if isinstance(attributes, tuple):
                continue  # Skip this event
            #print(attributes)
            if attributes is not None and not isinstance(attributes, str):
                from_address = attributes.get('from')
                to_address = attributes.get('to')
                amount = attributes.get('amount')
                if from_address is not None and to_address is not None and amount is not None:
                    check_parameters_from = transfer_alert('addresses_list.csv',from_address)
                    check_parameters_to = transfer_alert('addresses_list.csv',to_address)                    
                    if check_parameters_from == 1:
                        print(f"the address_from code is {check_parameters_from}")                   
                        amount = float(amount/10000000000)
                        print('----------warning------Tht address has sent DOT-----------')
                        print(f"[SENT ALERT]Transfer from {from_address} to {to_address} with {amount} at {current_time}")
                        send_transfer_email(1,from_address,to_address,amount,receivers)
                    elif check_parameters_to == 1:
                        print(f"the address_to code is {check_parameters_to}")
                        amount = float(amount/10000000000)
                        print('----------warning------Tht address has recive DOT-----------')
                        print(f"[RECIVE ALERT]Transfer from {from_address} to {to_address} with {amount} at {current_time}")
                        send_transfer_email(2,from_address,to_address,amount,receivers)
                    else:
                        print(f'-----NO match address--code is 0---skip-operation at {current_time}----')
                    #detail = event['event']
                    #print (detail)
                    #print(f"Transfer from {from_address} to {to_address} with {amount}")
                else:                    
                    continue


substrate = SubstrateInterface(url="wss://polkadot-rpc.dwellir.com")

# Accounts to track
storage_keys = [
    
    substrate.create_storage_key(
        "System", "Events"
    ),
]

result = substrate.subscribe_storage(
    storage_keys=storage_keys, subscription_handler=subscription_transfers
)


