from algokit_utils import AlgorandClient, Account
from smart_contracts.artifacts.vaultlending.vaultlending_client import VaultlendingClient
import os


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

lender = algod_client.account.from_mnemonic(mnemonic=os.getenv("LENDER"))
print("🔑 LENDER address:", lender.address)

borrower = algod_client.account.from_mnemonic(mnemonic=os.getenv("BORROWER"))
print("🔑 BORROWER address:", borrower.address)

creditOfficer = algod_client.account.from_mnemonic(mnemonic=os.getenv("CREDIT_OFFICER"))
print("🔑 CREDIT address:", creditOfficer.address)

# -----------------------------
# 3️⃣ Load AppClient using App ID
# -----------------------------

#factory = algod_client.get_typed_app_factory(VaultlendingFactory, default_sender=deployer)
APP_SPEC_PATH = "smart_contracts/artifacts/vaultlending/Vaultlending.arc56.json"

client = VaultlendingClient(
    algorand=algod_client,
    app_id=int(APP_ID),
    default_sender=deployer.address,  # required to send transactions
    default_signer=deployer.signer,   # required to sign transactions
)


# -----------------------------
# 4️⃣ Pass ApplicationClient to VaultlendingClient
# -----------------------------



print("VaultLending client ready. App ID:", client.app_address)


# -----------------------------
# 5️⃣ Whitelist deployer
# -----------------------------
whitelist_tx = client.params.whitelist_account( (
    deployer.address,  # account to whitelist
    True               # allowed
))
print("✅ Deployer whitelisted " + whitelist_tx.tx_id)

# === ✅ DEPOSIT ===
deposit_tx =client.params.deposit((
        deployer.address,  # depositor
        1_000_000          # amount in microAlgos (e.g., 1 Algo)
    ))

print("✅ Deposit transaction ID:", deposit_tx.tx_id)