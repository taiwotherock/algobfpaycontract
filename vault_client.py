from email import message
from algokit_utils import AlgorandClient, Account
from smart_contracts.artifacts.vaultlending.vaultlending_client import VaultlendingClient
import os
from algosdk import transaction
from algosdk.logic import get_application_address
import base64

from smart_contracts.artifacts.vaultlending.vaultlending_client import (
        VaultlendingFactory,
    )

import asyncio
from dotenv import load_dotenv
load_dotenv()
# -----------------------------
# 1️⃣ Load environment variables
# -----------------------------
DEPLOYER_MNEMONIC = os.getenv("DEPLOYER")
APP_ID : str = os.getenv("VAULT_APP_ID") ;  # The deployed VaultLending App ID
USDC_ASA_ID : str = os.getenv("USDC_ASA_ID")
MERCHANT_ADDR = os.getenv("MERCHANT_ADDR")

if not DEPLOYER_MNEMONIC or not APP_ID or not USDC_ASA_ID or not MERCHANT_ADDR:
    raise ValueError("Please set DEPLOYER_MNEMONIC, VAULT_APP_ID, USDC_ASA_ID, and MERCHANT_ADDR in your environment.")

# -----------------------------
# 2️⃣ Setup Algorand client
# -----------------------------
algod_client = AlgorandClient.testnet()
deployer = algod_client.account.from_mnemonic(mnemonic=DEPLOYER_MNEMONIC)
print("🔑 Deployer address:", deployer.address)



# -----------------------------
# 3️⃣ Load AppClient using App ID
# -----------------------------

#factory = algod_client.get_typed_app_factory(VaultlendingFactory, default_sender=deployer)
APP_SPEC_PATH = "smart_contracts/artifacts/vaultlending/Vaultlending.arc56.json"


def whitelist(amount_microalgos: int, mnemonic: str):
    client = VaultlendingClient(
        algorand=algod_client,
        app_id=int(APP_ID),
        default_sender=deployer.address,  # required to send transactions
        default_signer=deployer.signer,   # required to sign transactions
    )

    print("VaultLending client ready. App ID:", client.app_address)

    whitelist_tx = client.params.whitelist_account( (
        deployer.address,  # account to whitelist
        True               # allowed
    ))
    print("✅ Deployer whitelisted ")
    print(whitelist_tx)
    return whitelist_tx




async def deposit_algo(amount_microalgos: int, key: str):
    """
    Deposit specified amount of ALGO into the VaultLending smart contract.

    :param amount_microalgos: Deposit amount in microAlgos (1 Algo = 1_000_000 microAlgos)
    :param mnemonic: Mnemonic phrase of the sender/depositor
    """

    # --- 1️⃣ Connect to TestNet ---
    algorand = AlgorandClient.testnet()

    # --- 2️⃣ Load sender account from mnemonic ---
    #print(depositor_address)
    account = algorand.account.from_mnemonic(mnemonic=key)

    # --- 3️⃣ Initialize VaultLending client ---
    '''client = VaultlendingClient(
        algorand=algorand,
        app_id=int(APP_ID),
        default_sender=account.address,
        default_signer=account.signer,
    )
    '''

    
    print('address : ' + account.address)
    factory = algorand.client.get_typed_app_factory(
        VaultlendingFactory, default_sender=account.address
    )

    client = factory.get_app_client_by_id(int(APP_ID), default_sender=account.address,
        default_signer=account.signer)
    

    # --- 4️⃣ Prepare payment transaction ---
    suggested_params = algorand.client.algod.suggested_params()
    suggested_params.fee = 2000
    suggested_params.flat_fee = True
    app_addr = get_application_address(int(APP_ID))

    payment_txn = transaction.PaymentTxn(
        sender=account.address,
        receiver=app_addr,
        amt=int(amount_microalgos),
        sp=suggested_params,
    
    )

    # --- 5️⃣ Call deposit_algo ABI method ---
    #print(f"💰 Depositing {amount_microalgos / 1_000_000:.6f} ALGO to VaultLending (AppID: {APP_ID})")

    '''result = client.send.deposit_algo((
            payment_txn,  # payment: gtxn.PaymentTransaction
        ))
    '''

    #amount_microalgos = int(amount_microalgos * 1_000_000)
    #call_params = client.params.deposit_algo((amount_microalgos,))
    #result = client.send.deposit_algo(signer=deployer.signer, sender=deployer.address)

    result = client.send.deposit_algo((
            payment_txn,  # payment: gtxn.PaymentTransaction
        
        ))
    
    '''call_params = client.params.deposit_algo((
            payment_txn,  # payment: gtxn.PaymentTransaction
        ))
    result = call_params.sender(signer=account.signer)
    '''
    
    
    try:
        tx_id = result.tx_id
    except AttributeError:
        tx_id = None

    if tx_id:
        print(f"✅ Deposit complete! TX ID: {tx_id}")
        print(f"🌐 Explorer: https://allo.info/testnet/transaction/{tx_id}")
    else:
        print("⚠️ Deposit executed but no TX ID available in result.")

    tx_id = result.tx_id
    print("✅ Deposit confirmed!")
    print(f"🔗 Transaction ID: {tx_id}")
    print(f"🌐 Explorer: https://allo.info/testnet/transaction/{tx_id}")
    
    return {"success": True, "tx_id": tx_id, "message": "PENDING"}

async def check_vault_balance():
    algod_client = AlgorandClient.testnet()
    contract_address = get_application_address(int(APP_ID))
    accountInfo = algod_client.client.algod.account_info(contract_address);
    print(accountInfo)

    print("Account balance (microAlgos):", accountInfo['amount']);
    print("Account balance (Algos):", accountInfo['amount'] / 1e6);

    return {"success" :True, "balance": accountInfo['amount'] / 1e6};

async def check_wallet_balance(walletAddress: str):
    algod_client = AlgorandClient.testnet()
    accountInfo = algod_client.client.algod.account_info(walletAddress);
    print(accountInfo)
    key ="amazing indicate parent ugly stereo bounce huge bubble mushroom company wire double amused arena toddler point month genuine talk crop black boil furnace absorb web"

    print("Account balance (microAlgos):", accountInfo['amount']);
    print("Account balance (Algos):", accountInfo['amount'] / 1e6);

    account = algod_client.account.from_mnemonic(mnemonic=key)
    factory = algod_client.client.get_typed_app_factory(
        VaultlendingFactory, default_sender=account.address
    )

    client = factory.get_app_client_by_id(int(APP_ID), default_sender=account.address)
    result = client.send.get_balance({walletAddress})
    print(result)

    

    '''
    algod = algod_client.client.algod
    #app_addr = get_application_address(int(APP_ID))
    box_name_bytes = walletAddress.encode("utf-8")
    #box_name = base64.b64encode(walletAddress.encode()).decode()

    box_data = algod.application_box_by_name(int(APP_ID), box_name_bytes)
    print(box_data)
    raw_value = base64.b64decode(box_data["value"])
    # Convert 8-byte UInt64 big-endian encoded value to int
    user_balance = int.from_bytes(raw_value, byteorder="big")


    #user_balance = client.boxes.algo_deposits[walletAddress]
    '''

    return {"success" :True, "balance": accountInfo['amount'] / 1e6, "depositBalance": ''};
    