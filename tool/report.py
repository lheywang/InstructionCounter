#!/bin/env python3
# ========================================================================================
# file : report.py
# author : l.heywang
# date : 09/11/2025
# 
# brief :   Parse a JSON output file (generated from parser.py) to create a nice report 
#           (markdown formatted) and output some stats !
# ========================================================================================

import argparse
import json
from pathlib import Path
import datetime

def calculate_total_instructions(data : dict) -> dict:
    """
        Calculate the total number of instructions that has been executed.
        Need a dict with some blocks and calls functions !

            -> We iterate over the calls, and make the pondered sum !
    """

    # Iterate over the keys
    total_instr = 0
    for key in data["calls"].keys():

        # Sum the instructions within the same call
        funct_instr = 0
        for instr in data["blocks"][key].keys():
            funct_instr += data["blocks"][key][instr]

        # Ponderate with the right call numbers
        total_instr += funct_instr * data["calls"][key]["count"]

    data["output"]["instructions"] = total_instr
    return data

def calculate_biggest_calls(data: dict) -> dict:
    """
        Calculate the biggest functions that have been executed.
        Used to optimize away the largest !
    """

        # Iterate over the keys
    function_counts = {}
    for addr, call_info in data["calls"].items():
        name = call_info["name"]
        count = call_info["count"]
        block_instrs = sum(data["blocks"][addr].values()) if addr in data["blocks"] else 0
        total = count * block_instrs
        
        if name not in function_counts:
            function_counts[name] = 0
        function_counts[name] += total

    # Sort and store the largest functions calls
    function_counts = sorted(function_counts.items(), key=lambda x: x[1], reverse=True)
    data["output"]["func_calls"] = function_counts

    return data


def read_json(source : Path) -> dict:
    """
        Read the JSON file, and produce a python accessible dict
    """

    ret = dict()
    with open(str(source), "r") as file:
        ret = json.load(file)

    return ret

if __name__ == "__main__" :
    # Argparse config
    parser = argparse.ArgumentParser(
        description="Parse a json file, produced from the base parser and compute some elements on it !"
    )
    parser.add_argument("input", help="Input .log file")
    parser.add_argument("-o", "--output", default="report/", help="Output report folder")
    args = parser.parse_args()

    # Path generation : 
    input = Path(args.input)
    output = Path(args.output) / Path("report.md")

    data = read_json(input)

    # Append the output dict to the data dict !
    data["output"] = dict()

    # Perform the different calculations
    data = calculate_total_instructions(data)
    data = calculate_biggest_calls(data)

    print(data["output"])
    
