#!/usr/bin/python3

import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate(fn_isolation):
    # выполнять откат цепи после завершения каждого теста, чтобы обеспечить надлежащую изоляцию
    # https://eth-brownie.readthedocs.io/en/v1.10.3/tests-pytest-intro.html#isolation-fixtures
    pass


@pytest.fixture(scope="module")
def token(GovernanceToken, accounts):
    return GovernanceToken.deploy({'from': accounts[0]})


@pytest.fixture(scope="module")
def token_with_balances(token, accounts):
    token.mint(accounts[1], 50)
    token.mint(accounts[2], 30)
    token.mint(accounts[3], 20)
    return token

@pytest.fixture(scope="function")
def token_with_allowances(token, accounts):
    token.approve(accounts[2], 10, {'from': accounts[1]})
    return token

@pytest.fixture(scope="function")
def token_with_uneven_distribution(GovernanceToken, accounts):
    token = GovernanceToken.deploy({'from': accounts[0]})    
    token.mint(accounts[1], 99999999999999999)
    token.mint(accounts[2], 1)
    return token
