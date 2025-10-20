from algopy import (
    ARC4Contract,
    Account,
    Asset,
    BoxMap,
    Global,
    UInt64,
    Txn,
    arc4,
    gtxn,
    itxn,
    String,
)
from algopy.arc4 import abimethod


class Vaultlending(ARC4Contract):
    def __init__(self) -> None:
        # Track balances in ALGO or USDC for each account
        self.algo_deposits = BoxMap(Account, UInt64)
        self.asset_deposits = BoxMap(Account, UInt64)
        self.whitelist = BoxMap(Account, arc4.Bool)

        # Track overall vault asset and admin
        self.vault_asset = Asset(0)  # default none
        self.admin = Global.creator_address  # ✅ FIXED

    # -------- ADMIN / SETUP -------- #

    @abimethod
    def set_vault_asset(self, asset: Asset) -> None:
        """Admin chooses which ASA (like USDC) the vault uses."""
        assert Txn.sender == self.admin, "NOT_ADMIN"
        self.vault_asset = asset

    @abimethod
    def whitelist_account(self, account: Account, allowed: arc4.Bool) -> None:
        """Admin whitelists an account for withdraw/borrow."""
        assert Txn.sender == self.admin, "NOT_ADMIN"
        self.whitelist[account] = allowed

    # -------- DEPOSIT -------- #

    @abimethod
    def deposit_algo(self, payment: gtxn.PaymentTransaction) -> None:
        """Deposit ALGO into vault."""
        assert payment.receiver == Global.current_application_address, "WRONG_RECEIVER"
        assert payment.sender == Txn.sender, "SENDER_MISMATCH"

        # Inner payment transaction to self (the vault)
        itxn.Payment(
            receiver=Global.current_application_address,
            amount=payment.amount
        ).submit()

        current = self.algo_deposits.get(Txn.sender, default=UInt64(0))
        self.algo_deposits[Txn.sender] = current + payment.amount

    @abimethod
    def deposit_asset(self, asset_txn: gtxn.AssetTransferTransaction) -> None:
        """Deposit USDC (or ASA) into vault."""
        assert asset_txn.asset_receiver == Global.current_application_address, "WRONG_RECEIVER"
        assert asset_txn.sender == Txn.sender, "SENDER_MISMATCH"
        assert asset_txn.xfer_asset == self.vault_asset, "INVALID_ASSET"

        current = self.asset_deposits.get(Txn.sender, default=UInt64(0))
        self.asset_deposits[Txn.sender] = current + asset_txn.asset_amount

    # -------- WITHDRAW -------- #

    @abimethod
    def withdraw_algo(self, amount: arc4.UInt64) -> None:
        """Withdraw ALGO from vault (only if whitelisted)."""
        assert self.whitelist.get(Txn.sender, default=arc4.Bool(False)), "NOT_WHITELISTED"

        current = self.algo_deposits.get(Txn.sender, default=UInt64(0))
        assert current >= amount.native, "INSUFFICIENT_BALANCE"

        self.algo_deposits[Txn.sender] = current - amount.native

        itxn.Payment(
            receiver=Txn.sender,
            amount=amount.native,
        ).submit()

    @abimethod
    def withdraw_asset(self, amount: arc4.UInt64) -> None:
        """Withdraw USDC/ASA from vault (only if whitelisted)."""
        assert self.whitelist.get(Txn.sender, default=arc4.Bool(False)), "NOT_WHITELISTED"

        current = self.asset_deposits.get(Txn.sender, default=UInt64(0))
        assert current >= amount.native, "INSUFFICIENT_BALANCE"

        self.asset_deposits[Txn.sender] = current - amount.native

        itxn.AssetTransfer(
            xfer_asset=self.vault_asset,
            asset_receiver=Txn.sender,
            asset_amount=amount.native,
        ).submit()

    # -------- BORROW / REPAY -------- #

    @abimethod
    def borrow_to_merchant(
        self,
        merchant: Account,
        amount: arc4.UInt64,
    ) -> None:
        """Credit officer borrows from vault and transfers to merchant."""
        assert self.whitelist.get(Txn.sender, default=arc4.Bool(False)), "CREDIT_OFFICER_NOT_WHITELISTED"
        assert self.whitelist.get(merchant, default=arc4.Bool(False)), "MERCHANT_NOT_WHITELISTED"

        vault_balance = self.asset_deposits.get(Global.current_application_address, default=UInt64(0))
        assert vault_balance >= amount.native, "VAULT_EMPTY"

        # Update vault balance and transfer to merchant
        self.asset_deposits[Global.current_application_address] = vault_balance - amount.native

        itxn.AssetTransfer(
            xfer_asset=self.vault_asset,
            asset_receiver=merchant,
            asset_amount=amount.native,
        ).submit()

    @abimethod
    def repay_loan(self, asset_txn: gtxn.AssetTransferTransaction) -> None:
        """Borrower repays loan in vault asset (e.g., USDC)."""
        assert asset_txn.xfer_asset == self.vault_asset, "INVALID_ASSET"
        assert asset_txn.asset_receiver == Global.current_application_address, "WRONG_RECEIVER"

        current = self.asset_deposits.get(Txn.sender, default=UInt64(0))
        self.asset_deposits[Txn.sender] = current + asset_txn.asset_amount

    # -------- VIEW FUNCTIONS -------- #

    @abimethod(readonly=True)
    def get_balance(self, account: Account) -> arc4.UInt64:
        """Return combined ALGO + asset balance."""
        algo_balance = self.algo_deposits.get(account, default=UInt64(0))
        asset_balance = self.asset_deposits.get(account, default=UInt64(0))
        return arc4.UInt64(algo_balance + asset_balance)

    # -------- DEMO METHOD -------- #

    @abimethod
    def hello(self, name: String) -> String:
        """Simple test method."""
        return "Hello, " + name
