// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.7.0;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract GovernanceToken is ERC20('GovernanceToken', 'GOV'), Ownable {
    
    using SafeMath for uint256;

    event PayRequestedETH(address indexed to, uint256 amount);
    event HangingETH(address indexed to, uint256 amount);
    event PayHangingETH(uint256 amount);
    event Deposit(address indexed sender, uint256 amount);
    event MintTokens(address indexed to, uint256 amount);

    /// @dev parameters of an extra token emission
    // Emission logs, than contract receives ETH
    struct EmissionInfo {
        // new totalSupply after emission
        uint256 totalSupply;

        // total balance of Ether stored at the contract before emission
        uint256 totalBalanceWas;
    }

    EmissionInfo[] public emissions;

    mapping(address => uint256) lastAccountEmission;
    mapping(address => uint256) lastTotalBalance;

    uint256 public totalETH;
    uint256 public totalHangingETH;


    constructor() {
        emissions.push(EmissionInfo({
            totalSupply: 0,
            totalBalanceWas: 0
        }));
    }

    receive() external payable {
        if (msg.value > 0) {
            emit Deposit(msg.sender, msg.value);
                        emissions.push(EmissionInfo({
                totalSupply: super.totalSupply(),
                totalBalanceWas: totalETH
            }));
            totalETH = totalETH.add(msg.value);
        }
    }

    /// @dev creates _amount tokens and assigns them to _for insreasing totalSupply
    function mint(address _for, uint256 _amount) onlyOwner public payable {
        require(msg.sender != address(0));
        // before minting we pay ETH to acount we mint tokens for
        this.payETH(_for);
        
        // changing account info to an actual state of contract 
        lastAccountEmission[_for] = getLastEmissionNum();
        lastTotalBalance[_for] = totalETH;
        emit MintTokens(_for, _amount);
        _mint(_for, _amount);
    }

    /// @notice request Ether for current account 
    function requestETH() public {
        this.payETH(msg.sender);
    }

    /// @notice request hanging Ether for contract owner
    function requestHangingETH() onlyOwner public {
        super.transfer(owner() ,totalHangingETH);
        emit PayHangingETH(totalHangingETH);
        totalHangingETH = 0;
    }

    /// @notice hook on standard ERC20#transfer to pay dividends
    function transfer(address _to, uint256 _value) public override returns (bool) {
        this.payETH(msg.sender);
        this.payETH(_to);
        return super.transfer(_to, _value);
    }

    /// @notice hook on standard ERC20#transferFrom to pay dividends
    function transferFrom(address _from, address _to, uint256 _value) public override returns (bool) {
        this.payETH(_from);
        this.payETH(_to);
        return super.transferFrom(_from, _to, _value);
    }

    /// @dev adds Ether to the account _to
    function payETH(address _to) external payable {
        (bool hasNewETH, uint256 ETH, uint256 lastProcessedEmissionNum) = this.countETHShare(_to);
        if (!hasNewETH)
            return;

        if (ETH != 0) {
            bool res = payable(_to).send(ETH);
            if (res) {
                emit PayRequestedETH(_to, ETH);
            } else {
                // _to probably is a contract not able to receive ether
                emit HangingETH(_to, ETH);
                totalHangingETH = totalHangingETH.add(ETH);
            }
        }

        lastAccountEmission[_to] = lastProcessedEmissionNum;
        if (lastProcessedEmissionNum == getLastEmissionNum()) {
            lastTotalBalance[_to] = totalETH;
        } else {
            lastTotalBalance[_to] = emissions[lastProcessedEmissionNum.add(1)].totalBalanceWas;
        }
    }

    /// @dev calculates dividends for the account _for
    /// returns (true if state has to be updated, dividend amount (could be 0!), lastProcessedEmissionNum)
    function countETHShare(address _for) external returns(
        bool hasNewETH,
        uint256 ETH,
        uint256 lastProcessedEmissionNum
    ) {
        uint256 lastEmissionNum = getLastEmissionNum();
        uint256 lastAccountEmissionNum = lastAccountEmission[_for];
        require(lastAccountEmissionNum <= lastEmissionNum);

        uint256 totalBalanceWasWhenLastPay = lastTotalBalance[_for];
        require(totalBalanceWasWhenLastPay <= totalETH);


        if (totalETH == totalBalanceWasWhenLastPay) {
            return (false, 0, lastAccountEmissionNum);
        }

        uint256 initialBalance = balanceOf(_for);

        // if no tokens owned by account
        if (initialBalance == 0) {
            return (true, 0, lastEmissionNum);
        }
            

          // We start with last processed emission because some ether could be collected before next emission
        // we pay all remaining ether collected and continue with all the next emissions
        uint256 iter = 0;
        uint256 iterMax = getMaxIterationsForRequestETH();


        for (uint256 emissionToProcess = lastAccountEmissionNum; emissionToProcess <= lastEmissionNum; emissionToProcess++) {
            if (iter++ > iterMax)
                break;

            lastAccountEmissionNum = emissionToProcess;
            EmissionInfo storage emission = emissions[emissionToProcess];

            if (emission.totalSupply == 0)
                continue;

            uint256 totalETHDuringEmission;
            // last emission we stopped on
            if (emissionToProcess == lastEmissionNum) {
                totalETHDuringEmission = totalETH.sub(totalBalanceWasWhenLastPay);
            } else {
                totalETHDuringEmission = emissions[emissionToProcess.add(1)].totalBalanceWas.sub(totalBalanceWasWhenLastPay);
                totalBalanceWasWhenLastPay = emissions[emissionToProcess.add(1)].totalBalanceWas;
            }

            uint256 emissionETH = totalETHDuringEmission.mul(initialBalance).div(emission.totalSupply);
            ETH = ETH.add(emissionETH);
        }

        return (true, ETH, lastAccountEmissionNum);
    }

    function getLastEmissionNum() private view returns(uint256) {
        return emissions.length - 1;
    }

    function getMaxIterationsForRequestETH() internal pure returns(uint256) {
        return 1000;
    }
}
