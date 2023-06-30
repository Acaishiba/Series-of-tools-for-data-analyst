import pandas as pd
from substrateinterface import SubstrateInterface
from substrateinterface.exceptions import SubstrateRequestException
import statistics
import requests
import csv

substrate = SubstrateInterface(url="wss://polkadot-rpc-tn.dwellir.com")

url = 'https://polkadot.api.subscan.io/api/scan/staking/validators'
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'yourkey'  # Replace with your API key
}

era = 14

filename = "validator_avgrewards_list2.csv"

# Get validator era reward for the given address and era value
def get_validator_era_reward(validator_address: str, era: str):
    # Query ErasRewardPoints
    response = substrate.query('Staking', 'ErasRewardPoints', [era])
    validator_era_score = 0
    result = response['individual']
    total_score = response['total']
    # Iterate through all validators, query the score for the target validator in the current era
    for query in result:
        if query[0] == validator_address:
            print(f'Found target address: {query[0]}')
            validator_era_score = query[1]
            break
    print(f'The score for this era is: {validator_era_score}')
    # Query the total reward for this era
    total_reward = substrate.query('Staking', 'ErasValidatorReward', [era])
    # Convert the total reward to float
    total_reward = int(str(total_reward))
    total_reward = float(total_reward / 10000000000)
    # Calculate the validator's reward for this era
    validator_era_reward = total_reward * float(str(validator_era_score)) / float(str(total_score))
    return validator_era_reward

# Calculate the average rewards for the previous N eras
def get_Nera_avg_rewards(validator_address: str, range_era: int):
    # Query the current active era
    response = substrate.query('Staking', 'ActiveEra', [])
    active_era = response['index']
    active_era = int(str(active_era))

    # Calculate the range of eras to be queried
    start_era = active_era - range_era
    total_validator_rewards = []

    # Iterate through each era, query the validator's rewards, and add them to the total_validator_rewards list
    for era in range(start_era, active_era):
        print(f'------Querying era: {era}------')
        validator_era_reward = get_validator_era_reward(validator_address, str(era))
        if validator_era_reward != 0:
            total_validator_rewards.append(validator_era_reward)

    # Check the number of values in the total_validator_rewards list
    if len(total_validator_rewards) == 0:
        avg_validator_rewards = 0
        std_validator_rewards = None
    elif len(total_validator_rewards) == 1:
        avg_validator_rewards = total_validator_rewards[0]
        std_validator_rewards = None
    else:
        # Calculate the average rewards and standard deviation
        avg_validator_rewards = sum(total_validator_rewards) / len(total_validator_rewards)
        std_validator_rewards = statistics.stdev(total_validator_rewards)

    active_ratio_validator = len(total_validator_rewards) / range_era

    print(f'Average rewards for the last {range_era} eras for {validator_address}: {avg_validator_rewards:.3f}')
    if std_validator_rewards is not None:
        print(f'Standard deviation for the last {range_era} eras for {validator_address}: {std_validator_rewards:.3f}')
    else:
        print(f'Standard deviation for the last {range_era} eras for {validator_address}: N/A')
    print(f'Activity ratio for the last {range_era} eras for {validator_address}: {active_ratio_validator:.3f}')

    return avg_validator_rewards, std_validator_rewards, active_ratio_validator

def get_validator_list():
    payload = {}
    response = requests.post(url, headers=headers, json=payload)
    validator_list = []

    if response.status_code == 200:
        data = response.json()
        if data['code'] == 0:
            validators = data['data']['list']
            for validator in validators:
                stash_account = validator['stash_account_display']['address']
                print(stash_account)
                validator_list.append(stash_account)
        else:
            print("API Error:", data['message'])
    else:
        print('Request failed:', response.status_code)

    return validator_list

def insert_to_csv(address, avg_rewards, std_rewards, active_ratio, filename):
    # Create or open the CSV file
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        data = [address, avg_rewards, std_rewards, active_ratio]

        # Write data to the file
        writer.writerow(data)

    print("Insertion successful")

validator_list = get_validator_list()

for row in validator_list:
    print(row)
    address = row
    avg_rewards, std_rewards, active_ratio = get_Nera_avg_rewards(address, era)
    print(f'Validator address: {address}, Avg reward: {avg_rewards}, Std reward: {std_rewards}, Active ratio: {active_ratio}')
    insert_to_csv(address, avg_rewards, std_rewards, active_ratio, filename)
