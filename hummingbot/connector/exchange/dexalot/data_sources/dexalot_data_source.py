import asyncio
from asyncio import Lock
from typing import List

from eth_account import Account
from eth_account.signers.local import LocalAccount
from hexbytes import HexBytes
from web3 import AsyncWeb3, Web3
from web3.middleware import async_geth_poa_middleware

from hummingbot.connector.exchange.dexalot import dexalot_constants as CONSTANTS
from hummingbot.connector.gateway.gateway_in_flight_order import GatewayInFlightOrder
from hummingbot.core.data_type.common import OrderType, TradeType

DEXALOT_TRADEPAIRS_ABI = '[{"name": "Executed", "type": "event", "inputs": [{"name": "version", "type": "uint8", "indexed": false, "internalType": "uint8"}, {"name": "pair", "type": "bytes32", "indexed": true, "internalType": "bytes32"}, {"name": "price", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "quantity", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "makerOrder", "type": "bytes32", "indexed": false, "internalType": "bytes32"}, {"name": "takerOrder", "type": "bytes32", "indexed": false, "internalType": "bytes32"}, {"name": "feeMaker", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "feeTaker", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "takerSide", "type": "uint8", "indexed": false, "internalType": "enum ITradePairs.Side"}, {"name": "execId", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "addressMaker", "type": "address", "indexed": true, "internalType": "address"}, {"name": "addressTaker", "type": "address", "indexed": true, "internalType": "address"}], "anonymous": false}, {"name": "Initialized", "type": "event", "inputs": [{"name": "version", "type": "uint8", "indexed": false, "internalType": "uint8"}], "anonymous": false}, {"name": "NewTradePair", "type": "event", "inputs": [{"name": "version", "type": "uint8", "indexed": false, "internalType": "uint8"}, {"name": "pair", "type": "bytes32", "indexed": false, "internalType": "bytes32"}, {"name": "basedisplaydecimals", "type": "uint8", "indexed": false, "internalType": "uint8"}, {"name": "quotedisplaydecimals", "type": "uint8", "indexed": false, "internalType": "uint8"}, {"name": "mintradeamount", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "maxtradeamount", "type": "uint256", "indexed": false, "internalType": "uint256"}], "anonymous": false}, {"name": "OrderStatusChanged", "type": "event", "inputs": [{"name": "version", "type": "uint8", "indexed": false, "internalType": "uint8"}, {"name": "traderaddress", "type": "address", "indexed": true, "internalType": "address"}, {"name": "pair", "type": "bytes32", "indexed": true, "internalType": "bytes32"}, {"name": "orderId", "type": "bytes32", "indexed": false, "internalType": "bytes32"}, {"name": "clientOrderId", "type": "bytes32", "indexed": false, "internalType": "bytes32"}, {"name": "price", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "totalamount", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "quantity", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "side", "type": "uint8", "indexed": false, "internalType": "enum ITradePairs.Side"}, {"name": "type1", "type": "uint8", "indexed": false, "internalType": "enum ITradePairs.Type1"}, {"name": "type2", "type": "uint8", "indexed": false, "internalType": "enum ITradePairs.Type2"}, {"name": "status", "type": "uint8", "indexed": false, "internalType": "enum ITradePairs.Status"}, {"name": "quantityfilled", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "totalfee", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "code", "type": "bytes32", "indexed": false, "internalType": "bytes32"}], "anonymous": false}, {"name": "ParameterUpdated", "type": "event", "inputs": [{"name": "version", "type": "uint8", "indexed": false, "internalType": "uint8"}, {"name": "pair", "type": "bytes32", "indexed": true, "internalType": "bytes32"}, {"name": "param", "type": "string", "indexed": false, "internalType": "string"}, {"name": "oldValue", "type": "uint256", "indexed": false, "internalType": "uint256"}, {"name": "newValue", "type": "uint256", "indexed": false, "internalType": "uint256"}], "anonymous": false}, {"name": "Paused", "type": "event", "inputs": [{"name": "account", "type": "address", "indexed": false, "internalType": "address"}], "anonymous": false}, {"name": "RoleAdminChanged", "type": "event", "inputs": [{"name": "role", "type": "bytes32", "indexed": true, "internalType": "bytes32"}, {"name": "previousAdminRole", "type": "bytes32", "indexed": true, "internalType": "bytes32"}, {"name": "newAdminRole", "type": "bytes32", "indexed": true, "internalType": "bytes32"}], "anonymous": false}, {"name": "RoleGranted", "type": "event", "inputs": [{"name": "role", "type": "bytes32", "indexed": true, "internalType": "bytes32"}, {"name": "account", "type": "address", "indexed": true, "internalType": "address"}, {"name": "sender", "type": "address", "indexed": true, "internalType": "address"}], "anonymous": false}, {"name": "RoleRevoked", "type": "event", "inputs": [{"name": "role", "type": "bytes32", "indexed": true, "internalType": "bytes32"}, {"name": "account", "type": "address", "indexed": true, "internalType": "address"}, {"name": "sender", "type": "address", "indexed": true, "internalType": "address"}], "anonymous": false}, {"name": "Unpaused", "type": "event", "inputs": [{"name": "account", "type": "address", "indexed": false, "internalType": "address"}], "anonymous": false}, {"type": "fallback", "stateMutability": "nonpayable"}, {"name": "DEFAULT_ADMIN_ROLE", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "bytes32", "internalType": "bytes32"}], "stateMutability": "view"}, {"name": "EXCHANGE_ROLE", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "bytes32", "internalType": "bytes32"}], "stateMutability": "view"}, {"name": "TENK", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}], "stateMutability": "view"}, {"name": "VERSION", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "bytes32", "internalType": "bytes32"}], "stateMutability": "view"}, {"name": "addLimitOrderList", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_clientOrderIds", "type": "bytes32[]", "internalType": "bytes32[]"}, {"name": "_prices", "type": "uint256[]", "internalType": "uint256[]"}, {"name": "_quantities", "type": "uint256[]", "internalType": "uint256[]"}, {"name": "_sides", "type": "uint8[]", "internalType": "enum ITradePairs.Side[]"}, {"name": "_type2s", "type": "uint8[]", "internalType": "enum ITradePairs.Type2[]"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "addOrder", "type": "function", "inputs": [{"name": "_trader", "type": "address", "internalType": "address"}, {"name": "_clientOrderId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_price", "type": "uint256", "internalType": "uint256"}, {"name": "_quantity", "type": "uint256", "internalType": "uint256"}, {"name": "_side", "type": "uint8", "internalType": "enum ITradePairs.Side"}, {"name": "_type1", "type": "uint8", "internalType": "enum ITradePairs.Type1"}, {"name": "_type2", "type": "uint8", "internalType": "enum ITradePairs.Type2"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "addOrderType", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_type", "type": "uint8", "internalType": "enum ITradePairs.Type1"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "addTradePair", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_baseTokenDetails", "type": "tuple", "components": [{"name": "decimals", "type": "uint8", "internalType": "uint8"}, {"name": "tokenAddress", "type": "address", "internalType": "address"}, {"name": "auctionMode", "type": "uint8", "internalType": "enum ITradePairs.AuctionMode"}, {"name": "srcChainId", "type": "uint32", "internalType": "uint32"}, {"name": "symbol", "type": "bytes32", "internalType": "bytes32"}, {"name": "symbolId", "type": "bytes32", "internalType": "bytes32"}, {"name": "sourceChainSymbol", "type": "bytes32", "internalType": "bytes32"}, {"name": "isVirtual", "type": "bool", "internalType": "bool"}], "internalType": "struct IPortfolio.TokenDetails"}, {"name": "_baseDisplayDecimals", "type": "uint8", "internalType": "uint8"}, {"name": "_quoteTokenDetails", "type": "tuple", "components": [{"name": "decimals", "type": "uint8", "internalType": "uint8"}, {"name": "tokenAddress", "type": "address", "internalType": "address"}, {"name": "auctionMode", "type": "uint8", "internalType": "enum ITradePairs.AuctionMode"}, {"name": "srcChainId", "type": "uint32", "internalType": "uint32"}, {"name": "symbol", "type": "bytes32", "internalType": "bytes32"}, {"name": "symbolId", "type": "bytes32", "internalType": "bytes32"}, {"name": "sourceChainSymbol", "type": "bytes32", "internalType": "bytes32"}, {"name": "isVirtual", "type": "bool", "internalType": "bool"}], "internalType": "struct IPortfolio.TokenDetails"}, {"name": "_quoteDisplayDecimals", "type": "uint8", "internalType": "uint8"}, {"name": "_minTradeAmount", "type": "uint256", "internalType": "uint256"}, {"name": "_maxTradeAmount", "type": "uint256", "internalType": "uint256"}, {"name": "_mode", "type": "uint8", "internalType": "enum ITradePairs.AuctionMode"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "cancelOrder", "type": "function", "inputs": [{"name": "_orderId", "type": "bytes32", "internalType": "bytes32"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "cancelOrderList", "type": "function", "inputs": [{"name": "_orderIds", "type": "bytes32[]", "internalType": "bytes32[]"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "cancelReplaceList", "type": "function", "inputs": [{"name": "_orderIds", "type": "bytes32[]", "internalType": "bytes32[]"}, {"name": "_clientOrderIds", "type": "bytes32[]", "internalType": "bytes32[]"}, {"name": "_prices", "type": "uint256[]", "internalType": "uint256[]"}, {"name": "_quantities", "type": "uint256[]", "internalType": "uint256[]"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "cancelReplaceOrder", "type": "function", "inputs": [{"name": "_orderId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_clientOrderId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_price", "type": "uint256", "internalType": "uint256"}, {"name": "_quantity", "type": "uint256", "internalType": "uint256"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "getAllowedOrderTypes", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}], "outputs": [{"name": "", "type": "uint256[]", "internalType": "uint256[]"}], "stateMutability": "view"}, {"name": "getBookId", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_side", "type": "uint8", "internalType": "enum ITradePairs.Side"}], "outputs": [{"name": "", "type": "bytes32", "internalType": "bytes32"}], "stateMutability": "view"}, {"name": "getNBook", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_side", "type": "uint8", "internalType": "enum ITradePairs.Side"}, {"name": "_nPrice", "type": "uint256", "internalType": "uint256"}, {"name": "_nOrder", "type": "uint256", "internalType": "uint256"}, {"name": "_lastPrice", "type": "uint256", "internalType": "uint256"}, {"name": "_lastOrder", "type": "bytes32", "internalType": "bytes32"}], "outputs": [{"name": "", "type": "uint256[]", "internalType": "uint256[]"}, {"name": "", "type": "uint256[]", "internalType": "uint256[]"}, {"name": "", "type": "uint256", "internalType": "uint256"}, {"name": "", "type": "bytes32", "internalType": "bytes32"}], "stateMutability": "view"}, {"name": "getOrder", "type": "function", "inputs": [{"name": "_orderId", "type": "bytes32", "internalType": "bytes32"}], "outputs": [{"name": "", "type": "tuple", "components": [{"name": "id", "type": "bytes32", "internalType": "bytes32"}, {"name": "clientOrderId", "type": "bytes32", "internalType": "bytes32"}, {"name": "tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "price", "type": "uint256", "internalType": "uint256"}, {"name": "totalAmount", "type": "uint256", "internalType": "uint256"}, {"name": "quantity", "type": "uint256", "internalType": "uint256"}, {"name": "quantityFilled", "type": "uint256", "internalType": "uint256"}, {"name": "totalFee", "type": "uint256", "internalType": "uint256"}, {"name": "traderaddress", "type": "address", "internalType": "address"}, {"name": "side", "type": "uint8", "internalType": "enum ITradePairs.Side"}, {"name": "type1", "type": "uint8", "internalType": "enum ITradePairs.Type1"}, {"name": "type2", "type": "uint8", "internalType": "enum ITradePairs.Type2"}, {"name": "status", "type": "uint8", "internalType": "enum ITradePairs.Status"}], "internalType": "struct ITradePairs.Order"}], "stateMutability": "view"}, {"name": "getOrderByClientOrderId", "type": "function", "inputs": [{"name": "_trader", "type": "address", "internalType": "address"}, {"name": "_clientOrderId", "type": "bytes32", "internalType": "bytes32"}], "outputs": [{"name": "", "type": "tuple", "components": [{"name": "id", "type": "bytes32", "internalType": "bytes32"}, {"name": "clientOrderId", "type": "bytes32", "internalType": "bytes32"}, {"name": "tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "price", "type": "uint256", "internalType": "uint256"}, {"name": "totalAmount", "type": "uint256", "internalType": "uint256"}, {"name": "quantity", "type": "uint256", "internalType": "uint256"}, {"name": "quantityFilled", "type": "uint256", "internalType": "uint256"}, {"name": "totalFee", "type": "uint256", "internalType": "uint256"}, {"name": "traderaddress", "type": "address", "internalType": "address"}, {"name": "side", "type": "uint8", "internalType": "enum ITradePairs.Side"}, {"name": "type1", "type": "uint8", "internalType": "enum ITradePairs.Type1"}, {"name": "type2", "type": "uint8", "internalType": "enum ITradePairs.Type2"}, {"name": "status", "type": "uint8", "internalType": "enum ITradePairs.Status"}], "internalType": "struct ITradePairs.Order"}], "stateMutability": "view"}, {"name": "getOrderRemainingQuantity", "type": "function", "inputs": [{"name": "_orderId", "type": "bytes32", "internalType": "bytes32"}], "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}], "stateMutability": "view"}, {"name": "getRoleAdmin", "type": "function", "inputs": [{"name": "role", "type": "bytes32", "internalType": "bytes32"}], "outputs": [{"name": "", "type": "bytes32", "internalType": "bytes32"}], "stateMutability": "view"}, {"name": "getRoleMember", "type": "function", "inputs": [{"name": "role", "type": "bytes32", "internalType": "bytes32"}, {"name": "index", "type": "uint256", "internalType": "uint256"}], "outputs": [{"name": "", "type": "address", "internalType": "address"}], "stateMutability": "view"}, {"name": "getRoleMemberCount", "type": "function", "inputs": [{"name": "role", "type": "bytes32", "internalType": "bytes32"}], "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}], "stateMutability": "view"}, {"name": "getTradePair", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}], "outputs": [{"name": "", "type": "tuple", "components": [{"name": "baseSymbol", "type": "bytes32", "internalType": "bytes32"}, {"name": "quoteSymbol", "type": "bytes32", "internalType": "bytes32"}, {"name": "buyBookId", "type": "bytes32", "internalType": "bytes32"}, {"name": "sellBookId", "type": "bytes32", "internalType": "bytes32"}, {"name": "minTradeAmount", "type": "uint256", "internalType": "uint256"}, {"name": "maxTradeAmount", "type": "uint256", "internalType": "uint256"}, {"name": "auctionPrice", "type": "uint256", "internalType": "uint256"}, {"name": "auctionMode", "type": "uint8", "internalType": "enum ITradePairs.AuctionMode"}, {"name": "makerRate", "type": "uint8", "internalType": "uint8"}, {"name": "takerRate", "type": "uint8", "internalType": "uint8"}, {"name": "baseDecimals", "type": "uint8", "internalType": "uint8"}, {"name": "baseDisplayDecimals", "type": "uint8", "internalType": "uint8"}, {"name": "quoteDecimals", "type": "uint8", "internalType": "uint8"}, {"name": "quoteDisplayDecimals", "type": "uint8", "internalType": "uint8"}, {"name": "allowedSlippagePercent", "type": "uint8", "internalType": "uint8"}, {"name": "addOrderPaused", "type": "bool", "internalType": "bool"}, {"name": "pairPaused", "type": "bool", "internalType": "bool"}, {"name": "postOnly", "type": "bool", "internalType": "bool"}], "internalType": "struct ITradePairs.TradePair"}], "stateMutability": "view"}, {"name": "getTradePairs", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "bytes32[]", "internalType": "bytes32[]"}], "stateMutability": "view"}, {"name": "grantRole", "type": "function", "inputs": [{"name": "role", "type": "bytes32", "internalType": "bytes32"}, {"name": "account", "type": "address", "internalType": "address"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "hasRole", "type": "function", "inputs": [{"name": "role", "type": "bytes32", "internalType": "bytes32"}, {"name": "account", "type": "address", "internalType": "address"}], "outputs": [{"name": "", "type": "bool", "internalType": "bool"}], "stateMutability": "view"}, {"name": "initialize", "type": "function", "inputs": [{"name": "_orderbooks", "type": "address", "internalType": "address"}, {"name": "_portfolio", "type": "address", "internalType": "address"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "matchAuctionOrder", "type": "function", "inputs": [{"name": "_takerOrderId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_maxNbrOfFills", "type": "uint256", "internalType": "uint256"}], "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}], "stateMutability": "nonpayable"}, {"name": "maxNbrOfFills", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "uint256", "internalType": "uint256"}], "stateMutability": "view"}, {"name": "pause", "type": "function", "inputs": [], "outputs": [], "stateMutability": "nonpayable"}, {"name": "pauseAddOrder", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_addOrderPause", "type": "bool", "internalType": "bool"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "pauseTradePair", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_tradePairPause", "type": "bool", "internalType": "bool"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "paused", "type": "function", "inputs": [], "outputs": [{"name": "", "type": "bool", "internalType": "bool"}], "stateMutability": "view"}, {"name": "postOnly", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_postOnly", "type": "bool", "internalType": "bool"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "removeOrderType", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_type", "type": "uint8", "internalType": "enum ITradePairs.Type1"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "removeTradePair", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "renounceRole", "type": "function", "inputs": [{"name": "role", "type": "bytes32", "internalType": "bytes32"}, {"name": "account", "type": "address", "internalType": "address"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "revokeRole", "type": "function", "inputs": [{"name": "role", "type": "bytes32", "internalType": "bytes32"}, {"name": "account", "type": "address", "internalType": "address"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "setAllowedSlippagePercent", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_allowedSlippagePercent", "type": "uint8", "internalType": "uint8"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "setAuctionMode", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_mode", "type": "uint8", "internalType": "enum ITradePairs.AuctionMode"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "setAuctionPrice", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_price", "type": "uint256", "internalType": "uint256"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "setDisplayDecimals", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_displayDecimals", "type": "uint8", "internalType": "uint8"}, {"name": "_isBase", "type": "bool", "internalType": "bool"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "setMaxNbrOfFills", "type": "function", "inputs": [{"name": "_maxNbrOfFills", "type": "uint256", "internalType": "uint256"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "setMaxTradeAmount", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_maxTradeAmount", "type": "uint256", "internalType": "uint256"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "setMinTradeAmount", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_minTradeAmount", "type": "uint256", "internalType": "uint256"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "supportsInterface", "type": "function", "inputs": [{"name": "interfaceId", "type": "bytes4", "internalType": "bytes4"}], "outputs": [{"name": "", "type": "bool", "internalType": "bool"}], "stateMutability": "view"}, {"name": "tradePairExists", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}], "outputs": [{"name": "", "type": "bool", "internalType": "bool"}], "stateMutability": "view"}, {"name": "unpause", "type": "function", "inputs": [], "outputs": [], "stateMutability": "nonpayable"}, {"name": "unsolicitedCancel", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_isBuyBook", "type": "bool", "internalType": "bool"}, {"name": "_maxCount", "type": "uint256", "internalType": "uint256"}], "outputs": [], "stateMutability": "nonpayable"}, {"name": "updateRate", "type": "function", "inputs": [{"name": "_tradePairId", "type": "bytes32", "internalType": "bytes32"}, {"name": "_rate", "type": "uint8", "internalType": "uint8"}, {"name": "_rateType", "type": "uint8", "internalType": "enum ITradePairs.RateType"}], "outputs": [], "stateMutability": "nonpayable"}]'

DEXALOT_TRADEPAIRS_ADDRESS = "0x09383137C1eEe3E1A8bc781228E4199f6b4A9bbf"


class DexalotClient:

    def __init__(
            self,
            dexalot_api_secret: str,
            connector,
    ):
        self._private_key = dexalot_api_secret
        self._connector = connector
        self.last_nonce = 0
        self.transaction_lock = Lock()

        self.account: LocalAccount = Account.from_key(dexalot_api_secret)

        self.provider = CONSTANTS.DEXALOT_SUBNET_RPC_URL
        self._w3 = Web3(Web3.HTTPProvider(self.provider))
        self.async_w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(self.provider))
        self.async_w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
        self.async_w3.eth.default_account = self.account.address
        self.async_w3.strict_bytes_type_checking = False

        self.trade_pairs_manager = self.async_w3.eth.contract(address=DEXALOT_TRADEPAIRS_ADDRESS,
                                                              abi=DEXALOT_TRADEPAIRS_ABI)

    async def add_order_list(self, order_list: List[GatewayInFlightOrder]):
        symbol = await self._connector.exchange_symbol_associated_to_pair(trading_pair=order_list[0].trading_pair)
        pairByte32 = HexBytes(symbol.encode('utf-8'))

        gas = len(order_list) * CONSTANTS.PLACE_ORDER_GAS_LIMIT
        client_order_id_list = []
        prices_list = []
        quantities_list = []
        sides_list = []
        type2s_list = []
        for order in order_list:
            trading_pair = order_list[0].trading_pair
            price = int(order.price * 10 ** self._connector._evm_params[trading_pair]["base_evmdecimals"])
            quantity = int(order.amount * 10 ** self._connector._evm_params[trading_pair]["quote_evmdecimals"])
            prices_list.append(price)
            quantities_list.append(quantity)
            sides_list.append(1 if order.trade_type == TradeType.SELL else 0)
            client_order_id_list.append(order.client_order_id)
            type2s_list.append(3 if order.order_type == OrderType.LIMIT_MAKER else 0)

        function = self.trade_pairs_manager.functions.addLimitOrderList(
            pairByte32,
            client_order_id_list,
            prices_list,
            quantities_list,
            sides_list,
            type2s_list
        )
        result = await self._build_and_send_tx(function, gas)
        return result

    async def cancel_order_list(self, orders_to_cancel: List[GatewayInFlightOrder]):
        cancel_order_list = [i.exchange_order_id for i in orders_to_cancel]
        gas = len(orders_to_cancel) * CONSTANTS.CANCEL_GAS_LIMIT
        function = self.trade_pairs_manager.functions.cancelOrderList(cancel_order_list)
        result = await self._build_and_send_tx(function, gas)
        return result

    async def _build_and_send_tx(self, function, gas):
        """
        Build and send a transaction.
        If gasPrice is not specified, the average price of the whole network is used by default

        """
        async with self.transaction_lock:
            for retry_attempt in range(CONSTANTS.TRANSACTION_REQUEST_ATTEMPTS):
                try:
                    current_nonce = await self.async_w3.eth.get_transaction_count(self.account.address)
                    tx_params = {
                        'nonce': current_nonce if current_nonce > self.last_nonce else self.last_nonce,
                        'gas': gas,
                    }
                    transaction = await function.build_transaction(tx_params)
                    signed_txn = self.async_w3.eth.account.sign_transaction(
                        transaction, private_key=self._private_key
                    )
                    result = await self.async_w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    return result.hex()
                except ValueError as e:
                    self._connector.logger().warning(
                        f"{str(e)} "
                        f"Attempt {function.abi['name']} {retry_attempt + 1}/{CONSTANTS.TRANSACTION_REQUEST_ATTEMPTS}"
                    )
                    arg = str(e)
                    self.last_nonce = int(arg[arg.find('next nonce ') + 11: arg.find(", tx nonce")])
                    await asyncio.sleep(CONSTANTS.RETRY_INTERVAL ** retry_attempt)
                    continue
