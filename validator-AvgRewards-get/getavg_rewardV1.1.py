import pandas as pd
from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException
import statistics

substrate = SubstrateInterface(url="wss://polkadot.public.curie.radiumblock.co/ws")

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
            print(f'查询到目标地址{query[0]}')
            validator_era_score = query[1]
            break
    print(f'其本周期分数为{validator_era_score}')
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
    response = substrate.query('Staking', 'ActiveEra', [])
    active_era = response['index']
    active_era = int(str(active_era))
    
    # 计算待查询的 era 范围
    start_era = active_era - range_era
    total_validator_rewards = []
    
    # 遍历每个 era，查询验证人的收益，并计入 total_validator_rewards 列表
    for era in range(start_era, active_era):
        print(f'------当前查询的era为{era}------')
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
        avg_validator_rewards = sum(total_validator_rewards) / len(total_validator_rewards)
        std_validator_rewards = statistics.stdev(total_validator_rewards)
    
    active_ratio_validator = len(total_validator_rewards)/range_era
    
    print(f'{add_validator}的近{range_era}个era的平均收益为{avg_validator_rewards:.3f}')
    if  std_validator_rewards != None:
        print(f'{add_validator}的近{range_era}个era的标准差为{std_validator_rewards:.3f}')
    else:
        print(f'{add_validator}的近{range_era}个era的标准差无法计算"None"')
    print(f'{add_validator}的近{range_era}个era的活跃度为{active_ratio_validator:.3f}')
    
    return(avg_validator_rewards, std_validator_rewards, active_ratio_validator)

# 读取csv文件
df = pd.read_csv('address_list.csv')

# 循环遍历每个地址，并查询收益、标准差和活跃度
for index, row in df.iterrows():
    address = row['Address']
    avg_rewards, std_rewards, active_ratio = get_Nera_avg_rewards(address, 14)
    df.at[index, 'Avg_Rewards'] = avg_rewards
    df.at[index, 'Std_Rewards'] = std_rewards
    df.at[index, 'Active_Ratio'] = active_ratio

# 将数据写回csv文件
df.to_csv('address_list_with_rewards.csv', index=False)
