from traceback import format_exc
import threading
import hivemind
from flask import jsonify, request
import time
import config
from app import app, models
from utils import safe_decode
import re

from web3 import Web3
import json

logger = hivemind.get_logger(__file__)

contract_abi = json.loads('[{"inputs":[{"internalType":"address","name":"_sltTokenAddress","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"user","type":"address"},{"indexed":false,"internalType":"string","name":"serverId","type":"string"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"FundsTransferred","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"orchestrator","type":"address"}],"name":"OrchestratorAdded","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"orchestrator","type":"address"}],"name":"OrchestratorRemoved","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"string","name":"serverId","type":"string"},{"indexed":false,"internalType":"address","name":"serverAddress","type":"address"}],"name":"ServerBound","type":"event"},{"inputs":[{"internalType":"address","name":"_orchestrator","type":"address"}],"name":"addOrchestrator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"serverId","type":"string"},{"internalType":"address","name":"serverAddress","type":"address"}],"name":"bindServer","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"isOrchestrator","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_orchestrator","type":"address"}],"name":"removeOrchestrator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"","type":"string"}],"name":"servers","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"sltToken","outputs":[{"internalType":"contract IERC20","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"user","type":"address"},{"internalType":"string[]","name":"serverIds","type":"string[]"},{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"name":"transferFunds","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]')

def send_funds(user_address, server_id):
    node_url = 'https://sepolia-rollup.arbitrum.io/rpc'
    web3 = Web3(Web3.HTTPProvider(node_url))
    contract_address = Web3.to_checksum_address('0x1b1a2A4276E73c074134bB01069F16F44fA6049e')
    # user_address = Web3.to_checksum_address(user_address)
    orchestrator_private_key = '0xd35b2cb7ddc13d8fe5407df97a6e50e5b5311d84090e43a5666f0aba06471ad4'
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    orchestrator_address = web3.eth.account.from_key(orchestrator_private_key).address

    nonce = web3.eth.get_transaction_count(orchestrator_address)
    tx = contract.functions.transferFunds(
    user_address,
    [server_id],  # server_id should be in a list
    [web3.to_wei(1, 'ether')]  # Amount should also be in a list
    ).build_transaction({
        'chainId': 421614,  # Make sure this matches the chain you are working with
        'gas': 2000000,
        'gasPrice': web3.to_wei('50', 'gwei'),
        'nonce': nonce,
    })
    
    signed_tx = web3.eth.account.sign_transaction(tx, orchestrator_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt


# Create an async function to perform additional tasks


def get_last_line(filename):
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
            if lines:
                last_line = lines[-1].strip()
                return last_line
            else:
                return "File is empty"
    except FileNotFoundError:
        return "File not found"

def extract_peer_id(text):
    # Use a regular expression to extract the content after "libp2p.peer.id.ID"
    match = re.search(r'libp2p\.peer\.id\.ID\s*\(([^)]+)\)', text)

    if match:
        extracted_text = match.group(1)
        return extracted_text
    else:
        return None

# Define an asynchronous task
def additional_task(user_address, peerID):
    logger.info(f"Pinging For async after return: {peerID}")
    send_funds(user_address,peerID)
    logger.info("Async task completed.")

@app.post("/api/v1/generate")
def http_api_generate():
    try:
        model_name = get_typed_arg("model", str)
        inputs = request.values.get("inputs")
        do_sample = get_typed_arg("do_sample", int, False)
        temperature = get_typed_arg("temperature", float)
        top_k = get_typed_arg("top_k", int)
        top_p = get_typed_arg("top_p", float)
        user_address = get_typed_arg("useraddr",str)
        repetition_penalty = get_typed_arg("repetition_penalty", float)
        max_length = get_typed_arg("max_length", int)
        max_new_tokens = get_typed_arg("max_new_tokens", int)
        logger.info(f"generate(), {model_name=}, {inputs=}")

        model, tokenizer, backend_config = models[model_name]
        if not backend_config.public_api:
            raise ValueError(f"We do not provide public API for {model_name} due to license restrictions")

        if inputs is not None:
            inputs = tokenizer(inputs, return_tensors="pt")["input_ids"].to(config.DEVICE)
            n_input_tokens = inputs.shape[1]
        else:
            n_input_tokens = 0

        outputs = model.generate(
            inputs=inputs,
            do_sample=do_sample,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            max_length=max_length,
            max_new_tokens=max_new_tokens,
        )
        outputs = safe_decode(tokenizer, outputs[0, n_input_tokens:])
        logger.info(f"generate(), outputs={repr(outputs)}")

        # Replace 'your_file.txt' with the path to the file you want to read.
        filename = 'currentPeerList.txt'
        last_line = get_last_line(filename)
        print("Last Line:", last_line)
        peerID = extract_peer_id(last_line)
        logger.info(f"Extracted Peer ID: {peerID}")


        # Create a separate thread to run the asynchronous task
        async_thread = threading.Thread(target=additional_task, args=(user_address, peerID))
        async_thread.start()
        logger.info(f"Returned Content to User: {peerID}")
        return jsonify(ok=True, outputs=outputs)
    except Exception:
        return jsonify(ok=False, traceback=format_exc())


def get_typed_arg(name, expected_type, default=None):
    value = request.values.get(name)
    return expected_type(value) if value is not None else default
