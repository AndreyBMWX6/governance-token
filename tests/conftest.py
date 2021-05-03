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
