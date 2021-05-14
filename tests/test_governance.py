import brownie


def test_governance_token_recieve(accounts, token):
    accounts[0].transfer(token.address, 100)
    assert token.totalETH() == 100

def test_governance_token_mint(accounts, token):
    # owner mints token
    token_balance_before = token.balanceOf(accounts[1])
    token.mint(accounts[1], 100, {'from': accounts[0], 'value': 100})
    token_balance_after = token.balanceOf(accounts[1])
    assert token_balance_after - token_balance_before == 100

    # not owner tries to mint tokens
    token_balance_before = token.balanceOf(accounts[1])
    account_is_owner = True
    
    try:
        token.mint(accounts[1], 100, {'from': accounts[1], 'value': 100})
    except Exception:
        account_is_owner = False
    
    assert not account_is_owner
    token_balance_after = token.balanceOf(accounts[1])
    assert token_balance_after - token_balance_before == 0

def test_governance_token_requestETH(accounts, token_with_balances):
    # info about balances can be seen in `conftest.py`
    accounts[5].transfer(token_with_balances, 1000)
    
    acc1_balance_before = accounts[1].balance()
    token_with_balances.requestETH({'from': accounts[1]})
    acc1_balance_after = accounts[1].balance()
    assert acc1_balance_after - acc1_balance_before == 500
    
    acc2_balance_before = accounts[2].balance()
    token_with_balances.requestETH({'from': accounts[2]})
    acc2_balance_after = accounts[2].balance()
    assert acc2_balance_after - acc2_balance_before == 300

    acc3_balance_before = accounts[3].balance()
    token_with_balances.requestETH({'from': accounts[3]})
    acc3_balance_after = accounts[3].balance()
    assert acc3_balance_after - acc3_balance_before == 200

def test_governance_token_transfer(accounts, token_with_balances):
    assert token_with_balances.balanceOf(accounts[1]) >= 10
    
    token_balance_before = token_with_balances.balanceOf(accounts[2])
    token_with_balances.transfer(accounts[2], 10, {'from': accounts[1]})
    token_balance_after = token_with_balances.balanceOf(accounts[2])
    assert token_balance_after - token_balance_before == 10

def test_governance_token_transferFrom(accounts, token_with_allowances):
    # allowances can be seen in asserts or in `conftest.py`
    assert token_with_allowances.balanceOf(accounts[1]) >= 10
    assert token_with_allowances.allowance(accounts[1], accounts[2]) >= 10

    token_balance_before = token_with_allowances.balanceOf(accounts[2])
    token_with_allowances.transferFrom(accounts[1], accounts[2], 10, {'from': accounts[2]})
    token_balance_after = token_with_allowances.balanceOf(accounts[2])
    assert token_balance_after - token_balance_before == 10

def test_governance_token_countETHShare(accounts, token_with_balances):
    '''func returns: hasNewETH, ETH, lastProcessedEmissionNum parameters
                     (bool, uint256, uint256)'''

    # no new ETH
    assert token_with_balances.totalETH() == 0
    result = token_with_balances.countETHShare(accounts[1], {'from': accounts[1]})
    assert result.return_value == (False, 0, 0)

    # no tokens
    accounts[5].transfer(token_with_balances, 1000)
    assert token_with_balances.totalETH() == 1000
    result = token_with_balances.countETHShare(accounts[4], {'from': accounts[4]})
    assert result.return_value == (True, 0, 1)

    # new ETH and account has tokens
    assert token_with_balances.balanceOf(accounts[1]) == 50
    result = token_with_balances.countETHShare(accounts[1], {'from': accounts[1]})
    assert result.return_value == (True, 500, 1)

def test_mint_redistribution(accounts, token_with_balances):
    accounts[5].transfer(token_with_balances, 1000)
    
    # before minting accounts[1] have 50% of tokens so his ETH share is 500
    result = token_with_balances.countETHShare(accounts[1], {'from': accounts[1]})
    assert result.return_value[1] == 500

    token_with_balances.mint(accounts[4], 100)
    
    accounts[5].transfer(token_with_balances, 1000)
    # after minting accounts[1] have 25% of tokens so his share of new ETH is 250
    # total accounts[1] share is 500 + 250 = 750
    result = token_with_balances.countETHShare(accounts[1], {'from': accounts[1]})
    assert result.return_value[1] == 750

    balance_before = accounts[4].balance()    
    token_with_balances.requestETH({'from': accounts[4]})
    balance_after = accounts[4].balance()
    # after minting accounts[4] has 50% of tokens so he gets 500
    # we don't pay old ETH to accounts[4] because he didn't have tokens when we got it
    assert balance_after - balance_before == 500
    
    balance_before = accounts[1].balance()
    token_with_balances.requestETH({'from': accounts[1]})
    balance_after = accounts[1].balance()
    assert balance_after - balance_before == 750

def test_transfer_redistribution(accounts, token_with_balances):
    # info for tester(can be seen in `conftest.py`)
    assert token_with_balances.totalSupply() == 100
    assert token_with_balances.balanceOf(accounts[1]) == 50
    assert token_with_balances.balanceOf(accounts[2]) == 30

    accounts[5].transfer(token_with_balances, 1000)

    acc1_balance_before_transfer = accounts[1].balance()
    acc2_balance_before_transfer = accounts[2].balance()

    # we pay all collected ETH before transfer    
    token_with_balances.transfer(accounts[2], 10, {'from': accounts[1]})
    
    acc1_balance_after_transfer = accounts[1].balance()
    acc2_balance_after_transfer = accounts[2].balance()

    assert acc1_balance_after_transfer - acc1_balance_before_transfer == 500
    assert acc2_balance_after_transfer - acc2_balance_before_transfer == 300

    accounts[5].transfer(token_with_balances, 1000)

    token_with_balances.requestETH({'from': accounts[1]})
    token_with_balances.requestETH({'from': accounts[2]})

    acc1_balance_after_request = accounts[1].balance()
    acc2_balance_after_request = accounts[2].balance()

    # testing ETH distribution with new token balances
    assert acc1_balance_after_request - acc1_balance_after_transfer == 400
    assert acc2_balance_after_request - acc2_balance_after_transfer == 400

def test_double_spend(accounts, token_with_balances):
    # got new ETH
    accounts[5].transfer(token_with_balances, 1000)

    # requesting ETH
    balance_before = accounts[1].balance()
    token_with_balances.requestETH({'from': accounts[1]})
    balance_after = accounts[1].balance()
    assert balance_after - balance_before == 500

    # no new ETH payed to contract, old ETH is payed; 
    # requesting ETH one more time, should get 0
    balance_before = accounts[1].balance()
    token_with_balances.requestETH({'from': accounts[1]})
    balance_after = accounts[1].balance()
    assert balance_after - balance_before == 0

    balance_before = accounts[1].balance()
    token_with_balances.requestETH({'from': accounts[1]})
    balance_after = accounts[1].balance()
    assert balance_after - balance_before == 0

def test_uneven_distribution(accounts, token_with_uneven_distribution):
    accounts[5].transfer(token_with_uneven_distribution, 100000000000000000)

    acc1_balance_before = accounts[1].balance()
    token_with_uneven_distribution.requestETH({'from': accounts[1]})
    acc1_balance_after = accounts[1].balance()
    assert acc1_balance_after - acc1_balance_before == 99999999999999999

    acc2_balance_before = accounts[2].balance()
    token_with_uneven_distribution.requestETH({'from': accounts[2]})
    acc2_balance_after = accounts[2].balance()
    assert acc2_balance_after - acc2_balance_before == 1
