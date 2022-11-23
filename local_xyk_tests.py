################################################
# imports
################################################

import pandas as pd
import os
import yaml
from terra_sdk.client.lcd import LCDClient
from terra_sdk.core.wasm import MsgStoreCode, MsgInstantiateContract, MsgExecuteContract, MsgMigrateContract
from terra_sdk.core.fee import Fee
from terra_sdk.core.bank.msgs import MsgSend
from terra_sdk.key.mnemonic import MnemonicKey
from terra_sdk.client.lcd.api.tx import CreateTxOptions
from terra_sdk.client.localterra import LocalTerra
from terra_sdk.core.coins import Coins, Coin
import base64
import json
import pendulum
import subprocess
import argparse
from terra_sdk.core.wasm.data import AccessConfig
from terra_proto.cosmwasm.wasm.v1 import AccessType
import time

################################################
# parse configs
################################################

contracts_df = pd.read_csv("/repos/metadata/contracts.tsv", sep="\t")

################################################
# terra objects
################################################

terra_local = LocalTerra()
terra = LCDClient(url="http://3.88.107.200:1317", chain_id="localterra")

wallet1 = terra_local.wallets["test1"]
wallet2 = terra_local.wallets["test2"]
wallet3 = terra_local.wallets["test3"]
wallet4 = terra_local.wallets["test4"]

worker_wallet = terra_local.wallets["test7"]


################################################
# deploy func
################################################

def deploy_local_wasm(file_path, wallet, terra):
  with open(file_path, "rb") as fp:
    file_bytes = base64.b64encode(fp.read()).decode()
    store_code_msg = MsgStoreCode(wallet.key.acc_address, file_bytes, instantiate_permission=AccessConfig(AccessType.ACCESS_TYPE_EVERYBODY, ""))
    store_code_tx = wallet.create_and_sign_tx(CreateTxOptions(msgs=[store_code_msg], fee=Fee(6900000, "2000000uluna")))
    store_code_result = terra.tx.broadcast(store_code_tx)

  #persist code_id
  deployed_code_id = store_code_result.logs[0].events_by_type["store_code"]["code_id"][0]

  return deployed_code_id

def init_contract(code_id, init_msg, wallet, terra, name):

  #invoke contract instantiate
  instantiate_msg = MsgInstantiateContract(
    wallet.key.acc_address,
    wallet.key.acc_address,
    code_id,
    name,
    init_msg,
    {"uluna": 1000000},
  )

  #there is a fixed UST fee component now, so it's easier to pay fee in UST
  instantiate_tx = wallet.create_and_sign_tx(CreateTxOptions(msgs=[instantiate_msg], fee=Fee(690000, "500000uluna")))
  instantiate_tx_result = terra.tx.broadcast(instantiate_tx)

  return instantiate_tx_result

def execute_msg(address, msg, wallet, terra, coins=None):

  execute_msg = MsgExecuteContract(
    sender=wallet.key.acc_address,
    contract=address,
    msg=msg,
    coins=coins 
  )

  tx = wallet.create_and_sign_tx(CreateTxOptions(msgs=[execute_msg], fee=Fee(6900000, "1500000uluna")))
  tx_result = terra.tx.broadcast(tx)

  return tx_result

def migrate_msg(contract_address, new_code_id, msg, wallet, terra):
  migrate_msg = MsgMigrateContract(
    sender=wallet.key.acc_address,
    contract=contract_address,
    code_id=new_code_id,
    msg=msg,
  )

  tx = wallet.create_and_sign_tx(CreateTxOptions(msgs=[migrate_msg], fee=Fee(6900000, "1500000uluna")))
  tx_result = terra.tx.broadcast(tx)

  return tx_result

def bank_msg_send(recipient, amount, wallet, terrra):

  bank_msg = MsgSend(
    from_address=wallet.key.acc_address,
    to_address=recipient,
    amount=amount,
  )

  #there is a fixed UST fee component now, so it's easier to pay fee in UST
  tx = wallet.create_and_sign_tx(CreateTxOptions(msgs=[bank_msg], fee=Fee(2000000, "10000000uusd")))
  tx_result = terra.tx.broadcast(tx)

  return tx_result

def to_binary(msg):
  return base64.b64encode(json.dumps(msg).encode("utf-8")).decode("utf-8")

def proto_to_binary(msg):
  return base64.b64encode(msg.SerializeToString()).decode("utf-8")


################################################
# deploy code id
################################################

yield_token_code_id = deploy_local_wasm("/repos/contracts/artifacts/zodiac_yield_token.wasm", wallet2, terra)

vault_code_id = deploy_local_wasm("/repos/contracts/artifacts/zodiac_xyk_vault.wasm", wallet2, terra)

principal_token_id = str(int(contracts_df[(contracts_df["name"]=="token") & (contracts_df["protocol"]=="terraswap")]["code_id"].values[0]))

flash_loan_code_id = deploy_local_wasm("/repos/contracts/artifacts/zodiac_flash_loan.wasm", wallet2, terra)

fee_collector_code_id = deploy_local_wasm("/repos/contracts/artifacts/zodiac_terra_fee_collector.wasm", wallet2, terra)

factory_code_id = deploy_local_wasm("/repos/contracts/artifacts/zodiac_factory.wasm", wallet2, terra)

################################################
# astro setup
################################################

#create cw20
init_cw20 = {
  "name": "test coin",
  "symbol": "ZOD",
  "decimals": 6,
  "initial_balances":[
    {
      "address": wallet1.key.acc_address,
      "amount": "10000000",
    },
    {
      "address": wallet3.key.acc_address,
      "amount": "31000000",
    },
    {
      "address": wallet2.key.acc_address,
      "amount": "101000000",
    },
  ],
  "mint":{
    "minter": wallet2.key.acc_address,
  }
}

init_result = init_contract(principal_token_id, init_cw20, wallet2, terra, "testcoin")
testcoin_address = init_result.logs[0].events_by_type["instantiate"]["_contract_address"][0]

#create astroport liquidity pool
factory_contract = contracts_df[(contracts_df["protocol"] == "astroport")&(contracts_df["name"]=="factory")]["deployed_address"].values[0]

message = {
  "create_pair":
  {
    "pair_type": { "xyk":{}},
    "asset_infos":
    [
      { "token": {"contract_addr": testcoin_address}},
      { "native_token": {"denom": "uluna"}},
    ],
  }
}

result = execute_msg(factory_contract, message, wallet1, terra)
lp_token_address = result.logs[0].events_by_type["wasm"]["liquidity_token_addr"][0]
pair_address = result.logs[0].events_by_type["wasm"]["pair_contract_addr"][0]

#provide liquidity

DECIMALS=1000000

message = {
  "increase_allowance":{
    "spender": pair_address,
    "amount": str(10*DECIMALS),
  }
}

allowance_result = execute_msg(testcoin_address, message, wallet1, terra)

message = {
  "provide_liquidity":
  {
    "assets":
    [
      {
        "info": {"token": {"contract_addr": testcoin_address}},
        "amount": f"{10*DECIMALS}"
      },
      {
        "info": {"native_token": {"denom": "uluna"}},
        "amount": f"{10*DECIMALS}"
      },
    ]
  }
}
coins = Coins.from_str(f"{10*DECIMALS}uluna")
result = execute_msg(pair_address, message, wallet1, terra, coins)


message = {
  "increase_allowance":{
    "spender": pair_address,
    "amount": str(31*DECIMALS),
  }
}

allowance_result = execute_msg(testcoin_address, message, wallet3, terra)

message = {
  "provide_liquidity":
  {
    "assets":
    [
      {
        "info": {"token": {"contract_addr": testcoin_address}},
        "amount": f"{31*DECIMALS}"
      },
      {
        "info": {"native_token": {"denom": "uluna"}},
        "amount": f"{31*DECIMALS}"
      },
    ]
  }
}
coins = Coins.from_str(f"{31*DECIMALS}uluna")
result = execute_msg(pair_address, message, wallet3, terra, coins)

message = {
  "increase_allowance":{
    "spender": pair_address,
    "amount": str(101*DECIMALS),
  }
}

allowance_result = execute_msg(testcoin_address, message, wallet2, terra)

message = {
  "provide_liquidity":
  {
    "assets":
    [
      {
        "info": {"token": {"contract_addr": testcoin_address}},
        "amount": f"{101*DECIMALS}"
      },
      {
        "info": {"native_token": {"denom": "uluna"}},
        "amount": f"{101*DECIMALS}"
      },
    ]
  }
}
coins = Coins.from_str(f"{101*DECIMALS}uluna")
result = execute_msg(pair_address, message, wallet2, terra, coins)

########################
#confirm TEST pool, balance, and allowance
########################
terra.wasm.contract_query(pair_address, {"pool":{}})
terra.wasm.contract_query(testcoin_address, {"balance":{"address": pair_address}})
terra.wasm.contract_query(lp_token_address, {"balance": {"address": wallet1.key.acc_address}})
terra.wasm.contract_query(lp_token_address, {"balance": {"address": wallet3.key.acc_address}})

################################################
# spawn flash loan contract
################################################

message = {
  "owner": wallet2.key.acc_address,
  "target_denom": {"native": "uluna"},
  "token_actions": []
}

fee_collector_result = init_contract(fee_collector_code_id, message, wallet2, terra, "fee_collector")
fee_collector_address = fee_collector_result.logs[0].events_by_type["instantiate"]["_contract_address"][0]

message = {
  "owner": wallet2.key.acc_address,
  "fee_collector": fee_collector_address,
  "fee": 9, # 9 bps
}

flash_loan_init = init_contract(flash_loan_code_id, message, wallet2, terra, "flash_loan")
flash_loan_address = flash_loan_init.logs[0].events_by_type["instantiate"]["_contract_address"][0]

################################################
# spawn zodiac vault
################################################

message = {
  "ptoken_code_id": int(principal_token_id),
  "ytoken_code_id": int(yield_token_code_id),
  "vault_types": [
    "xyk"
  ]
}

result = init_contract(factory_code_id, message, wallet2, terra, "zodiac_factory")
zodiac_factory_address = result.logs[0].events_by_type["instantiate"]["_contract_address"][0]

message = {
  "update_vault_config":{
    "config": {
      "code_id": int(vault_code_id),
      "vault_type": "xyk",
    }
  }
}

result = execute_msg(zodiac_factory_address, message, wallet2, terra)

maturity_timestamp = pendulum.now().int_timestamp + 36000
generator_address = contracts_df[(contracts_df["protocol"] == "astroport")&(contracts_df["name"]=="generator")]["deployed_address"].values[0]

message = {
  "create_vault": {
    "vault_type": "xyk",
    "collateral_token": lp_token_address,
    "maturity_month": 1,
    "maturity_year": 2024,
    "options": to_binary({
      "pool_address": pair_address,
      "incentive_denoms": [
        "uluna",
        testcoin_address,
      ],
      "ptoken_l": "1",
      "flash_loan_address": flash_loan_address,
      "fee_collector": fee_collector_address,
      "redeem_fee": 100,
      "claim_yield_fee": 10,
      "generator_address": generator_address,
      "incentives_expiration_timestamp": 0,
      "keeper_scripts": [],
      "owner": wallet2.key.acc_address,
    }),
    "name": "dragon"
  }
}

vault_result = execute_msg(zodiac_factory_address, message, wallet2, terra)

vault_df = pd.DataFrame(vault_result.logs[0].events_by_type["instantiate"])
principal_token_address = vault_df[vault_df["code_id"]==principal_token_id]["_contract_address"].values[0]
yield_token_address = vault_df[vault_df["code_id"]==yield_token_code_id]["_contract_address"].values[0]
vault_address = vault_df[vault_df["code_id"]==vault_code_id]["_contract_address"].values[0]

message = {
  "update_config":{
    "maturity_timestamp": maturity_timestamp
  }
}

result = execute_msg(vault_address, message, wallet2, terra)

################################################
# do some refraction
################################################

message = {
  "send":{
    "contract": vault_address,
    "amount": "10000000",
    "msg": base64.b64encode(json.dumps({"deposit_collateral":{}}).encode("utf-8")).decode("utf-8")
  }
}

result = execute_msg(lp_token_address, message, wallet1, terra)

message = {
  "send":{
    "contract": vault_address,
    "amount": "30000000",
    "msg": base64.b64encode(json.dumps({"deposit_collateral":{}}).encode("utf-8")).decode("utf-8")
  }
}

result = execute_msg(lp_token_address, message, wallet3, terra)

message = {
  "send":{
    "contract": vault_address,
    "amount": "51000000",
    "msg": base64.b64encode(json.dumps({"deposit_collateral":{}}).encode("utf-8")).decode("utf-8")
  }
}

result = execute_msg(lp_token_address, message, wallet2, terra)


################################################
# setup plp-lp pool
################################################

message = {
  "create_pair":
  {
    "pair_type": { "xyk":{}},
    "asset_infos":
    [
      { "token": {"contract_addr": principal_token_address}},
      { "token": {"contract_addr": lp_token_address}},
    ],
  }
}

result = execute_msg(factory_contract, message, wallet1, terra)
plp_lp_token_address = result.logs[0].events_by_type["wasm"]["liquidity_token_addr"][0]
plp_lp_address = result.logs[0].events_by_type["wasm"]["pair_contract_addr"][0]

#provide liquidity
message = {
  "increase_allowance":{
    "spender": plp_lp_address,
    "amount": str(50_000_000),
  }
}

allowance_result = execute_msg(principal_token_address, message, wallet2, terra)

message = {
  "increase_allowance":{
    "spender": plp_lp_address,
    "amount": str(40_000_000),
  }
}

allowance_result = execute_msg(lp_token_address, message, wallet2, terra)

message = {
  "provide_liquidity":
  {
    "assets":
    [
      {
        "info": {"token": {"contract_addr": principal_token_address}},
        "amount": str(50_000_000)
      },
      {
        "info": {"token": {"contract_addr": lp_token_address}},
        "amount": str(40_000_000)
      },
    ]
  }
}
result = execute_msg(plp_lp_address, message, wallet2, terra)


################################################
# test plp-ylp vAMM
################################################

vamm_code_id = deploy_local_wasm("/repos/contracts/artifacts/zodiac_xyk_vamm.wasm", wallet2, terra)

message = {
  "owner": wallet2.key.acc_address,
}

vamm_result = init_contract(vamm_code_id, message, wallet2, terra, "vamm")
vamm_address = vamm_result.logs[0].events_by_type["instantiate"]["_contract_address"][0]

#try swapping pLP to yLP

message = {
  "send":{
    "contract": vamm_address,
    "amount": str(1_000_000),
    "msg": to_binary({"to_y_l_p":{
      "vault_address": vault_address,
      "xyk_pool_address": plp_lp_address,
      "xyk_pool_fee": 30, # 20 bps
    }})
  }
}

result = execute_msg(principal_token_address, message, wallet1, terra)
ylp_received = result.logs[0].events_by_type["wasm-zodiac_deposit"]["ylp_minted"][0]

#add mapping to vamm
message = {
  "upsert_vault_pool_mapping":{
    "vault_address": vault_address,
    "pool_address": plp_lp_address,
    "pool_fee": 30,
  }
}

result = execute_msg(vamm_address, message, wallet2, terra)

#swap yLP back to pLP
message = {
  "send":{
    "contract": vamm_address,
    "amount": ylp_received,
    "msg": to_binary({"to_p_l_p":{
      "vault_address": vault_address,
    }})
  }
}

result = execute_msg(yield_token_address, message, wallet1, terra)
plp_received = result.logs[0].events_by_type["wasm"]["return_amount"][1]

#try swapping pLP to yLP #2

message = {
  "send":{
    "contract": vamm_address,
    "amount": str(plp_received),
    "msg": to_binary({"to_y_l_p":{
      "vault_address": vault_address,
    }})
  }
}

result = execute_msg(principal_token_address, message, wallet1, terra)
ylp_received = result.logs[0].events_by_type["wasm-zodiac_deposit"]["ylp_minted"][0]

#swap yLP back to pLP

message = {
  "send":{
    "contract": vamm_address,
    "amount": ylp_received,
    "msg": to_binary({"to_p_l_p":{
      "vault_address": vault_address,
    }})
  }
}

result = execute_msg(yield_token_address, message, wallet1, terra)
plp_received = result.logs[0].events_by_type["wasm"]["return_amount"][1]

################################################
# setup zodiac incentives contract
################################################

incentives_code_id = deploy_local_wasm("/repos/contracts/artifacts/vault_incentives_v1.wasm", wallet2, terra)

incentives_start = pendulum.now().int_timestamp + 60
incentives_end = pendulum.now().int_timestamp + 3600

init_msg = {
  "owner": wallet2.key.acc_address,
  "lp_token": {"cw20": lp_token_address},
  "yield_token": {"cw20": yield_token_address},
  "principal_token": {"cw20": principal_token_address},
  "pt_lp_token": {"cw20": plp_lp_token_address},
  "incentive_denom": {"cw20": testcoin_address},
  "yield_token_allocation_min": "0.2",
  "yield_token_allocation_max": "0.8",
  "yield_token_allocation_increase_step_size": "0.001",
  "yield_token_allocation_decrease_step_size": "0.001",
  "refracted_lp_ratio_delta_lower_bound": "0.9",
  "pt_lp_ratio_delta_lower_bound": "0.9",
  "yield_token_allocation": "0.5",
  "keeper_min_elapsed_time": 60,
}

result = init_contract(incentives_code_id, init_msg, wallet2, terra, "zodiac_incentives")
incentives_address = result.logs[0].events_by_type["instantiate"]["_contract_address"][0]

"""
incentives_code_id = deploy_local_wasm("/repos/contracts/artifacts/vault_incentives.wasm", wallet2, terra)
migrate_msg(incentives_address, incentives_code_id, {}, wallet2, terra)
execute_msg(incentives_address, {"keep":{}}, wallet2, terra)
"""

execute_msg(testcoin_address, {"mint": {"recipient": wallet2.key.acc_address, "amount": str(100_000_000)}}, wallet2, terra)

update_schedule_msg = {
  "send":{
    "contract": incentives_address,
    "amount": str(100_000_000),
    "msg": to_binary({
      "update_schedule":{
        "schedule":{
          "start_date": incentives_start,
          "end_date": incentives_end,
          "total_incentives": str(100_000_000)
        }
      }
    }) 
  }
}

result = execute_msg(testcoin_address, update_schedule_msg, wallet2, terra)

time.sleep(100)
execute_msg(incentives_address, {"keep":{}}, wallet2, terra)
result = execute_msg(incentives_address, {"claim":{}}, wallet1, terra)
wallet_1_rewards = result.logs[0].events_by_type["wasm"]["amount"][0]
wallet_1_yt = terra.wasm.contract_query(yield_token_address, {"balance": {"address": wallet1.key.acc_address}})["balance"]
result = execute_msg(incentives_address, {"claim":{}}, wallet2, terra)
wallet_2_rewards = result.logs[0].events_by_type["wasm"]["amount"][0]
wallet_2_yt = terra.wasm.contract_query(yield_token_address, {"balance": {"address": wallet2.key.acc_address}})["balance"]
result = execute_msg(incentives_address, {"claim":{}}, wallet3, terra)
wallet_3_rewards = result.logs[0].events_by_type["wasm"]["amount"][0]
wallet_3_yt = terra.wasm.contract_query(yield_token_address, {"balance": {"address": wallet3.key.acc_address}})["balance"]

if abs((int(wallet_1_rewards) / int(wallet_3_rewards)) - (int(wallet_1_yt) / int(wallet_3_yt))) > 0.001:
  sys.exit(f"""
  wallet1 rewards: {wallet_1_rewards}
  wallet1 ytoken: {wallet_1_yt}
  wallet3 rewards: {wallet_3_rewards}
  wallet3 ytoken: {wallet_3_yt}
  """)

if abs((int(wallet_1_rewards) / int(wallet_2_rewards)) - (int(wallet_1_yt) / int(wallet_2_yt))) > 0.001:
  sys.exit(f"""
  wallet1 rewards: {wallet_1_rewards}
  wallet1 ytoken: {wallet_1_yt}
  wallet3 rewards: {wallet_2_rewards}
  wallet3 ytoken: {wallet_2_yt}
  """)

#stake a few pt_lp tokens
stake_msg = {
  "send":{
    "contract_addr": incentives_address,
    "amount": "1000000",
    "msg": to_binary({"stake_pt_lp: {}}),
  }
}
execute_msg(pt_lp_token, stake_msg, wallet1, terra)

stake_msg = {
  "send":{
    "contract_addr": incentives_address,
    "amount": "3000000",
    "msg": to_binary({"stake_pt_lp: {}}),
  }
}
execute_msg(pt_lp_token, stake_msg, wallet2, terra)

time.sleep(60)
execute_msg(incentives_address, {"keep":{}}, wallet2, terra)
result = execute_msg(incentives_address, {"claim":{}}, wallet1, terra)
wallet_1_rewards = result.logs[0].events_by_type["wasm"]["amount"][0]
wallet_1_yt = terra.wasm.contract_query(yield_token_address, {"balance": {"address": wallet1.key.acc_address}})["balance"]
result = execute_msg(incentives_address, {"claim":{}}, wallet2, terra)
wallet_2_rewards = result.logs[0].events_by_type["wasm"]["amount"][0]
wallet_2_yt = terra.wasm.contract_query(yield_token_address, {"balance": {"address": wallet2.key.acc_address}})["balance"]
result = execute_msg(incentives_address, {"claim":{}}, wallet3, terra)
wallet_3_rewards = result.logs[0].events_by_type["wasm"]["amount"][0]
wallet_3_yt = terra.wasm.contract_query(yield_token_address, {"balance": {"address": wallet3.key.acc_address}})["balance"]
yield_token_allocation = terra.wasm.contract_query(incentives_address, {"state":{}})["yield_token_allocation"]



################################################
# test rewards yield claim for ylp tokens
################################################

#holds bunch of astro tokens; need to send to the core generator with a schedule
vesting_address = contracts_df[(contracts_df["protocol"] == "astroport")&(contracts_df["name"]=="generator_vesting")]["deployed_address"].values[0]
astro_address = contracts_df[(contracts_df["protocol"] == "astroport")&(contracts_df["name"]=="token")]["deployed_address"].values[0]

#register pool with generator
message = {
  "setup_pools": {
    "pools":[
      [
        lp_token_address,
        "1"
      ]
    ]  
  }
}

pool_register_result = execute_msg(generator_address, message, wallet3, terra)

factory_generator_result = execute_msg(factory_contract, {"update_config": {"generator_address": generator_address}}, wallet3, terra)

#vamm swap to trigger deposit vault funds into generator
message = {
  "send":{
    "contract": vamm_address,
    "amount": str(plp_received),
    "msg": to_binary({"to_y_l_p":{
      "vault_address": vault_address,
      "xyk_pool_address": plp_lp_address,
      "xyk_pool_fee": 30, # 20 bps
    }})
  }
}

result = execute_msg(principal_token_address, message, wallet1, terra)
ylp_received = result.logs[0].events_by_type["wasm-zodiac_deposit"]["ylp_minted"][0]

#confirm we are earning incentives 
time.sleep(10)
message = {
  "extract_dex_incentives": {}
}

incentives_result = execute_msg(vault_address, message, wallet2, terra)
incentives_received = int(incentives_result.logs[0].events_by_type["wasm"]["claimed_amount"][0])

#insert a keeper script to compound astro into more lp tokens for the vault
luna_astro_pool = contracts_df[(contracts_df["protocol"] == "astroport")&(contracts_df["name"]=="luna-astro")]["deployed_address"].values[0]

message = {
  "upsert_keeper_script":{
    "keeper_script": {
      "name": "compound_generator_incentive_to_lp",
      "order": 1,
      "actions":[
        {
          "wasm":{
            "execute":{
              "contract_addr": vault_address,
              "funds": [],
              "msg": to_binary({
                "swap":{
                  "pair_address": luna_astro_pool,
                  "token_in": {
                    "cw20": astro_address,
                  },
                  "percent": "1.0",
                }
              })
            }
          }
        },
        {
          "wasm":{
            "execute":{
              "contract_addr": vault_address,
              "funds": [],
              "msg": to_binary({
                "zap":{
                  "token_in": {
                    "native": "uluna",
                  },
                }
              })
            }
          }
        },
      ]
    }
  }
}

keeper_script_result = execute_msg(vault_address, message, wallet2, terra)

message = {
  "extract_dex_incentives": {}
}

incentives_result = execute_msg(vault_address, message, wallet2, terra)

#confirm yield token holders receive the yield

message = {
  "claim_yield":{}
}

result = execute_msg(vault_address, message, wallet1, terra)
wallet1_yield = float(terra.wasm.contract_query(lp_token_address, {"balance":{"address": wallet1.key.acc_address}})["balance"])
wallet1_ytoken = float(terra.wasm.contract_query(yield_token_address, {"balance":{"address": wallet1.key.acc_address}})["balance"])

message = {
  "claim_yield":{}
}

result = execute_msg(vault_address, message, wallet3, terra)
wallet3_yield = float(result.logs[0].events_by_type["wasm"]["rewards"][0])
wallet3_ytoken = float(terra.wasm.contract_query(yield_token_address, {"balance":{"address": wallet3.key.acc_address}})["balance"])

if abs(wallet3_ytoken / wallet1_ytoken - wallet3_yield / wallet1_yield) > .01:
  sys.exit(f"""
  wallet1 yield: {wallet1_yield}
  wallet1 ytoken: {wallet1_ytoken}
  wallet3 yield: {wallet3_yield}
  wallet3 ytoken: {wallet3_ytoken}
  """)

"""
#ensure generator emission
message = {
  "set_tokens_per_block":{
    "amount": "1000"
  }
}
per_block_result = execute_msg(generator_address, message, wallet3, terra)
vesting_start = pendulum.now().int_timestamp + 60
vesting_end = pendulum.now().int_timestamp + 120
message = {
  "send":{
    "contract": vesting_address,
    "amount": "2000000",
    "msg": to_binary({"register_vesting_accounts":{
      "vesting_accounts":[
        {
          "address": generator_address,
          "schedules": [
            {
              "start_point":{
                "time": vesting_start,
                "amount": "1000000",
              },
              "end_point":{
                "time": vesting_end,
                "amount": "2000000",
              },            
            }
          ],          
        }
      ]
    }})
  }
}
register_result = execute_msg(astro_address, message, wallet3, terra)
"""


#remove pool from generator, confirm vault withdraws tokens back into contract


#spawn dummy 3rd party lp staking contract and proxy_generator; register to generator


################################################
# perform bunch of swaps (perhaps a direct send achieves same result?)
################################################

for i in range(3):
  print(i)

  message = {
    "swap":
    {
      "offer_asset":
      {
        "info": {"native_token": {"denom": "uluna"}},
        "amount": str(DECIMALS*10)
      },
      "max_spread": "0.5"
    }
  }

  coins = Coins.from_str(f"{10*DECIMALS}uluna")
  result = execute_msg(pair_address, message, wallet4, terra, coins)

  message = {
    "send":{
      "contract": pair_address,
      "amount": terra.wasm.contract_query(testcoin_address, {"balance": {"address": wallet4.key.acc_address}})["balance"],
      "msg": base64.b64encode(json.dumps({"swap":{"max_spread":"0.5"}}).encode("utf-8")).decode("utf-8")
    }
  }

  result = execute_msg(testcoin_address, message, wallet4, terra, coins)


terra.wasm.contract_query(pair_address, {"pool":{}})


################################################
# claim_yield
################################################

message = {
  "claim_yield":{}
}

result = execute_msg(vault_address, message, wallet1, terra)

message = {
  "claim_yield":{}
}

result = execute_msg(vault_address, message, wallet3, terra)

message = {
  "claim_yield":{}
}

result = execute_msg(vault_address, message, wallet2, terra)

message = {
  "increase_allowance":{
    "spender": vault_address,
    "amount": str(1*DECIMALS),
  }
}

allowance_result = execute_msg(principal_token_address, message, wallet1, terra)

message = {
  "increase_allowance":{
    "spender": vault_address,
    "amount": str(1*DECIMALS),
  }
}

allowance_result = execute_msg(yield_token_address, message, wallet1, terra)

message = {
  "combine":{
    "amount": str(1000000-99)
  }
}

combine_result = execute_msg(vault_address, message, wallet1, terra)

#test small fee scenario
message = {
  "combine":{
    "amount": "99"
  }
}

combine_result = execute_msg(vault_address, message, wallet1, terra)

message = {
  "send":{
    "contract": vault_address,
    "amount": "1000000",
    "msg": base64.b64encode(json.dumps({"redeem_principal":{}}).encode("utf-8")).decode("utf-8")
  }
}

result = execute_msg(principal_token_address, message, wallet1, terra)

message = {
  "send":{
    "contract": vault_address,
    "amount": "3000000",
    "msg": base64.b64encode(json.dumps({"redeem_principal":{}}).encode("utf-8")).decode("utf-8")
  }
}

result = execute_msg(principal_token_address, message, wallet3, terra)

################################################
# state check code
################################################

collateral_balance = int(terra.wasm.contract_query(lp_token_address, {"balance": {"address": vault_address}})["balance"])

collateral_composition = terra.wasm.contract_query(pair_address, {"share": {"amount": str(collateral_balance)}})

collateral_k = int(collateral_composition[0]["amount"]) * int(collateral_composition[1]["amount"])

sqrt_collateral_k = collateral_k ** 0.5

ptoken_supply = 1000000*4
ptoken_k = 100000000000000
project_sqrt_ptoken_k = ptoken_k**0.5* ptoken_supply/1000000.0


balance = (sqrt_collateral_k - project_sqrt_ptoken_k) / sqrt_collateral_k
balance = balance * collateral_balance