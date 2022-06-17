import ast
from datetime import datetime
from genericpath import isdir, isfile
import json
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware

# TokenSet ABI
def getABI():
    with open("abi.json") as f:
        return json.load(f)


abi = getABI()

# Token ABI
EIP20_ABI = json.loads(
    '[{"constant":true,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_spender","type":"address"},{"name":"_value","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_from","type":"address"},{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transferFrom","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"_owner","type":"address"},{"name":"_spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":true,"name":"_to","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_owner","type":"address"},{"indexed":true,"name":"_spender","type":"address"},{"indexed":false,"name":"_value","type":"uint256"}],"name":"Approval","type":"event"}]'
)


def initConnection(pipe):
    # Init Connection
    try:
        w3 = Web3(Web3.HTTPProvider(pipe))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    except Exception as inst:
        now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        print(f"\n{now} -- Error connecting to HTTPProvider {pipe} with ERROR: ", inst)
        exit()
    return w3


# Check if Provided Address is Valid
def checkAddress(w3, address):
    is_address_valid = w3.isAddress(address)
    if is_address_valid:
        return False
    else:
        now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        print(f"\n{now} -- Provided Contract Address is not a valid Address.")
        return True


# get last Positions scanned for from positions.txt. If file not exsisting or emply, creating it and writing latest Positions to it.
def lastPositions(positions, address):
    if not isdir("positions"):
        os.mkdir("positions")
    if isfile(f"positions/{address}.txt"):
        with open(f"positions/{address}.txt", "r") as f:
            if os.stat(f"positions/{address}.txt").st_size > 0:
                return ast.literal_eval(f.read())
            else:
                with open(f"positions/{address}.txt", "w") as f:
                    f.write(str(positions))
                now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                print(
                    f"\n{now} -- {address}.txt was empty, updated with latest Position"
                )
                return None
    else:
        with open(f"positions/{address}.txt", "w") as f:
            f.write(str(positions))
        now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        print(f"\n{now} -- {address}.txt created and updated with latest Position.")
        return None


# get latest Positons from the Contract via getPositions()
def getPositions(w3, address):

    # Create Web3 contract object
    contract = w3.eth.contract(address=address, abi=abi)
    # Get Positions
    positions = contract.functions.getPositions().call()
    return positions


def convert(amount):
    #: Convert gwei to wei
    # wei_amount = Decimal(amount) * (Decimal(10) ** 9)  # Gigaweis are billions
    eth_amount = Web3.fromWei(amount, "ether")
    return eth_amount


def isIn(p, lastPos):
    for lp in lastPos:
        if lp[0] == p[0]:
            oldUnit = lp[2]
            newUnit = p[2]
            return oldUnit, newUnit
    # if token not in new position anymore, return none
    return None, None


def isOut(positions, lp):
    for p in positions:
        if p[0] == lp[0]:
            return False
    return True


def comparePositions(lastPos, positions):
    if positions == lastPos:
        return None
    if lastPos == None:
        return None
    obj = {"in": [], "out": [], "pout": [], "pin": [], "same": []}
    for p in positions:
        oldUnit, newUnit = isIn(p, lastPos)
        if oldUnit == None:
            obj["in"].append(p[0])
            continue
        if oldUnit == newUnit:
            obj["same"].append(p[0])
            continue
        if oldUnit < newUnit:
            obj["pin"].append(p[0])
        if oldUnit > newUnit:
            obj["pout"].append(p[0])
    for lp in lastPos:
        if isOut(positions, lp):
            obj["out"].append(lp[0])
    return obj


def updateFile(positions, address):
    with open(f"positions/{address}.txt", "w") as f:
        f.write(str(positions))
    now = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    print(f"\n{now} -- {address}.txt Updated.")


def getSymbol(w3, address):
    token_contract = w3.eth.contract(address=address, abi=EIP20_ABI)
    return token_contract.functions.symbol().call()


def getName(w3, address):
    token_contract = w3.eth.contract(address=address, abi=EIP20_ABI)
    return token_contract.functions.name().call()


def loopPositions(positions, w3):
    # struct Position {
    #     address component;    struct pos 0
    #     address module;       struct pos 1
    #     int256 unit;          struct pos 2
    #     uint8 positionState;  struct pos 3
    #     bytes data;           struct pos 4
    # }
    for i in positions:
        token_contract = w3.eth.contract(address=i[0], abi=EIP20_ABI)
        symbol = token_contract.functions.symbol().call()
        unit = i[2]
        return symbol, unit
