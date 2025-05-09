#!/usr/bin/env python3

from web3 import Web3, eth
from web3.middleware import geth_poa_middleware
import time
import os
import json
import argparse
from time import sleep
import requests
from pprint import pprint

# arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "-l", 
    "--local-rpc", 
    type=str, 
    help="Enter the private local rpc URL", 
    required=True
)
parser.add_argument(
    "-p", 
    "--public-rpc", 
    type=str, 
    help="Enter the public rpc URL", 
    required=True
)
parser.add_argument(
    "-d",
    "--debug",
    default=False,
    action="store_true",
    help="Debug where blocks stopped matching",
)

args = parser.parse_args()

poa_list = [137, 56]

def main():
    eth_rpc_url = args.local_rpc
    public_rpc_url = args.public_rpc
    # eth_rpc_url = input("Enter private Node URL: ")
    getChainId(eth_rpc_url, public_rpc_url)


def getChainId(eth_rpc_url, public_rpc_url):
    provider = Web3.HTTPProvider("%s" % (eth_rpc_url))
    web3 = Web3(provider)

    chain_id = web3.eth.chain_id

    provider = Web3.HTTPProvider("%s" % (public_rpc_url))
    web3 = Web3(provider)

    public_chain_id = web3.eth.chain_id
    print("Local ChainID: %s" % (chain_id))
    print("Public ChainID: %s" % (public_chain_id))
    if chain_id != public_chain_id:
        print("ChainID does not match")
        exit()
    else:  
        getBlockNumber(chain_id, eth_rpc_url, public_rpc_url)
    # getConfig(chain_id, eth_rpc_url)


def getBlockNumber(chain_id, eth_rpc_url, public_rpc_url):
    
    provider = Web3.HTTPProvider("%s" % (eth_rpc_url))
    web3 = Web3(provider)

    if chain_id in poa_list:       
        web3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    block_number = web3.eth.block_number - 1
    print(block_number)
    # block_number = 138596
    getBlockInfo(eth_rpc_url, public_rpc_url, block_number, chain_id)


def getBlockInfo(eth_rpc_url, public_rpc_url, block_number, chain_id):
    private_provider = Web3.HTTPProvider("%s" % (eth_rpc_url))
    private_web3 = Web3(private_provider)

    if chain_id in poa_list:
        private_web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    public_provider = Web3.HTTPProvider("%s" % (public_rpc_url))
    public_web3 = Web3(public_provider)

    if chain_id in poa_list:
        public_web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    private_block = private_web3.eth.get_block(block_number, full_transactions=True)
    public_block = public_web3.eth.get_block(block_number, full_transactions=True)

    print("Comparing block number %s" % (block_number))

    if private_block["hash"] == public_block["hash"]:
        print("Blocks are the same")
    else:
        print("Blocks are different")
        if args.debug:
            print("DEBUG: Using binary search to find where blocks diverge")
            sleep(1)
            find_divergence_point(eth_rpc_url, public_rpc_url, chain_id, 0, block_number)


def find_divergence_point(eth_rpc_url, public_rpc_url, chain_id, start, end):
    """
    Use binary search to find the exact point where blocks start to diverge
    """
    private_provider = Web3.HTTPProvider("%s" % (eth_rpc_url))
    private_web3 = Web3(private_provider)
    public_provider = Web3.HTTPProvider("%s" % (public_rpc_url))
    public_web3 = Web3(public_provider)

    if chain_id in poa_list:
        private_web3.middleware_onion.inject(geth_poa_middleware, layer=0)
        public_web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    while start <= end:
        mid = (start + end) // 2
        print(f"Checking block range: {start} - {end}, testing block {mid}")
        
        private_block = private_web3.eth.get_block(mid, full_transactions=True)
        public_block = public_web3.eth.get_block(mid, full_transactions=True)

        if private_block["hash"] == public_block["hash"]:
            # If this block matches, divergence must be after this point
            if mid == end:
                print(f"\nDivergence starts at block {mid + 1}")
                return mid + 1
            start = mid + 1
        else:
            # If this block doesn't match, divergence must be at or before this point
            if mid == start:
                print(f"\nDivergence starts at block {mid}")
                return mid
            end = mid - 1

    return start


def compareBlock(eth_rpc_url, public_rpc_url, block, chain_id):
    private_provider = Web3.HTTPProvider("%s" % (eth_rpc_url))
    private_web3 = Web3(private_provider)

    if chain_id in poa_list:
        private_web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    public_provider = Web3.HTTPProvider("%s" % (public_rpc_url))
    public_web3 = Web3(public_provider)

    if chain_id in poa_list:
        public_web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    private_block = private_web3.eth.get_block(block, full_transactions=True)
    public_block = public_web3.eth.get_block(block, full_transactions=True)

    return private_block["hash"] == public_block["hash"]


if __name__ == "__main__":
    main()
