# app.py

from flask import Flask, render_template, request
from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException
import statistics

app = Flask(__name__)

substrate = SubstrateInterface(url="https://polkadot.api.onfinality.io/rpc?")

#给定地址和era值，返回该era的此validator的验证奖励
def get_validator_era_reward(add_validator: str, era: str):

    # 查询 ErasRewardPoints
    response = substrate.query('Staking', 'ErasRewardPoints', [era])
    validator_era_score = 0
    result = response['individual']
    total_score = response['total']
    # 遍历所有验证人，查询目标验证人的本周期分数
    for query in result:
        if query[0] == add_validator:
            validator_era_score = query[1]
            break

    # 查询本周期的总奖励
    total_reward = substrate.query('Staking', 'ErasValidatorReward', [era])
    # 将返回结果转为 float 类型
    total_reward = int(str(total_reward))
    total_reward = float(total_reward/10000000000)

    # 计算目标验证人能获得的本周期奖励
    validator_era_reward = total_reward * float(str(validator_era_score))/ float(str(total_score))
    
    return validator_era_reward

#前N个era的收益平均值
def get_Nera_avg_rewards(add_validator: str, range_era: int):
    # 查询当前活跃的 era 值
    response = substrate.query(
        'Staking', 'ActiveEra', []
    )

    active_era = response['index']
    active_era = int(str(active_era))
    
    # 计算待查询的 era 范围
    start_era = active_era - range_era
    total_validator_rewards = []
    
    # 遍历每个 era，查询验证人的收益，并计入 total_validator_rewards 列表
    for era in range(start_era, active_era):
        validator_era_reward = get_validator_era_reward(add_validator, str(era))
        if validator_era_reward != 0:
            total_validator_rewards.append(validator_era_reward)

        #判断total_validator_rewards集合内有几个数值
    if len(total_validator_rewards) == 0:
        avg_validator_rewards = 0
        std_validator_rewards = None
    elif len(total_validator_rewards) == 1:
        avg_validator_rewards = total_validator_rewards[0]
        std_validator_rewards = None
    else:
        # 计算平均收益和标准差
        #print(total_validator_rewards)
        avg_validator_rewards = sum(total_validator_rewards) / len(total_validator_rewards)
        std_validator_rewards = statistics.stdev(total_validator_rewards)
    
    #计算验证者活跃率
    active_ratio_validator = len(total_validator_rewards)/range_era
 
    
    return [avg_validator_rewards, std_validator_rewards,active_ratio_validator]



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 取得表单中提交的输入值
        add_validator = request.form['add_validator']
        era = request.form['era']

        # 获取avg/std_results结果
        avg_std_results = get_Nera_avg_rewards(add_validator, int(era))
        print(avg_std_results)
        avg_validator_rewards = avg_std_results[0]
        std_validator_rewards = avg_std_results[1]
        active_ratio_validator = avg_std_results[2]
        active_ratio_validator = active_ratio_validator *100
        
        # 返回一个HTML模板，里面包括查询结果
        return render_template('input.html', add_validator=add_validator, era=era, avg_validator_rewards=avg_validator_rewards, std_validator_rewards=std_validator_rewards,active_ratio_validator = active_ratio_validator)
    else:
        # 呈现一个包括表单供用户输入的HTML模板
        return render_template('input.html')


if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=8080, debug=True)



