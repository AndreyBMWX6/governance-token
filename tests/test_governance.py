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

def test_add_new_account(accounts, token_with_balances):
    token_with_balances.mint(accounts[4], 25)
    accounts[5].transfer(token_with_balances, 1000)
    balance_before = accounts[4].balance()
    token_with_balances.requestETH({'from': accounts[4]})
    balance_after = accounts[4].balance()
    assert balance_after - balance_before == 200
