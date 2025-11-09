#!/bin/env python3
# ========================================================================================
# file : report.py
# author : l.heywang
# date : 09/11/2025
#
# brief :   Perform computations on the parsed log file (.json temp data).
# ========================================================================================

import argparse
import json
from pathlib import Path
import tomllib
import datetime


def count_instructions(data: dict) -> dict:
    """
    Calculate the total number of instructions that has been executed.
    Need a dict with some blocks and calls functions !
    Also returns a list, sorted per function names

        -> We iterate over the calls, and make the pondered sum !
    """

    # Iterate over the keys
    total_instr = 0
    function_counts = dict()
    instr_counts = dict()
    functions_instr = dict()

    for key in data["calls"].keys():

        name = data["calls"][key]["name"]

        # Sum the instructions within the same call
        funct_instr = 0
        for instr in data["blocks"][key].keys():
            funct_instr += data["blocks"][key][instr]

            # Check if we need to initialize some variables
            if instr not in instr_counts.keys():
                instr_counts[instr] = 0

            if name not in functions_instr.keys():
                functions_instr[name] = dict()

            if instr not in functions_instr[name].keys():
                functions_instr[name][instr] = 0

            # Add to the variables
            instr_counts[instr] += data["blocks"][key][instr]
            functions_instr[name][instr] += data["blocks"][key][instr]

        # Ponderate with the right call numbers
        block_instr = funct_instr * data["calls"][key]["count"]
        
        # Append for later :
        if name not in function_counts:
            function_counts[name] = 0
        function_counts[name] += block_instr

        total_instr += block_instr

    # Sort and store the largest functions calls
    function_counts = sorted(function_counts.items(), key=lambda x: x[1], reverse=True)
    data["output"]["instructions"] = total_instr
    data["output"]["instructions_counts"] = instr_counts
    data["output"]["func_calls_instr"] = dict(function_counts)
    data["output"]["func_used_instr"] = functions_instr
    return data


def count_cycles(data: dict) -> dict:
    """
    Estimate the number of cycles in total, and per block.
    Also return a list of the longest functions, in time
    """

    # First, load the config file
    cfg = dict()
    with open("config/instructions.toml", "rb") as file:
        tmp = tomllib.load(file)
        for key in tmp.keys():
            cfg = cfg | tmp[key]  # This flatten the dict, as we won't use it by after !

    # Iterate over the keys
    total_cycles = 0
    function_counts = dict()
    cycles_counts = dict()

    for key in data["calls"].keys():

        # Sum the instructions within the same call
        funct_cycle = 0
        for instr in data["blocks"][key].keys():
            funct_cycle += data["blocks"][key][instr] * cfg[instr.upper()]

            if instr not in cycles_counts.keys():
                cycles_counts[instr] = 0
            cycles_counts[instr] += funct_cycle

        # Ponderate with the right call numbers
        block_cycle = funct_cycle * data["calls"][key]["count"]
        name = data["calls"][key]["name"]

        # Append for later :
        if name not in function_counts:
            function_counts[name] = 0
        function_counts[name] += block_cycle

        total_cycles += block_cycle

    # Sort and store the largest functions calls
    function_counts = sorted(function_counts.items(), key=lambda x: x[1], reverse=True)
    data["output"]["cycles"] = total_cycles
    data["output"]["cycles_count"] = cycles_counts
    data["output"]["func_calls_cycles"] = dict(function_counts)
    return data


def compute_cpi(data: dict) -> dict:
    """
    Compute the global CPI, and the per functions CPI !
    """
    # Compute the global CPI
    cpi = data["output"]["cycles"] / data["output"]["instructions"]

    # Create output target
    func_cpi = dict()

    # Compute the per function CPI : 
    for func in data["output"]["func_calls_cycles"].keys():
        func_cpi[func] = data["output"]["func_calls_cycles"][func] / data["output"]["func_calls_instr"][func]

    # Sorting the func cpi list
    func_cpi = dict(sorted(func_cpi.items(), key=lambda x: x[1], reverse=True))

    # Store outputs
    data["output"]["cpi"] = cpi
    data["output"]["func_cpi"] = func_cpi
        
    return data


def compute_densities(data: dict) -> dict:
    """
    Compute various instructions densities, to get a view of the most used ones,
    and their proportions.
    """
    return data


def read_json(source: Path) -> dict:
    """
    Read the JSON file, and produce a python accessible dict
    """

    ret = dict()
    with open(str(source), "r") as file:
        ret = json.load(file)

    return ret


def write_json(target: Path, data: dict) -> None:
    """
    Write the data as JSON format.
    """

    with open(str(target), "w+") as file:
        json.dump(data, file, indent=4)

    return


if __name__ == "__main__":
    # Argparse config
    parser = argparse.ArgumentParser(
        description="Parse a json file, produced from the base parser and compute some elements on it !"
    )
    parser.add_argument("input", help="Input .log file")
    parser.add_argument(
        "-o", "--output", default="computed.json", help="Output json file"
    )
    args = parser.parse_args()

    # Path generation :
    input = Path(args.input)
    output = Path(args.output)

    data = read_json(input)

    # Append the output dict to the data dict !
    data["output"] = dict()

    # Perform the different calculations
    data = count_instructions(data)
    data = count_cycles(data)

    # Perform more advanced maths :
    data = compute_cpi(data)
    data = compute_densities(data)

    # Create the output file :
    write_json(output, data["output"])
