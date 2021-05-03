#!/usr/bin/python3

from brownie import GovernanceToken, accounts


def main():
    return GovernanceToken.deploy({'from': accounts[0]})
