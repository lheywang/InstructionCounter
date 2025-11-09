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
            instr_counts[instr] += (
                data["blocks"][key][instr] * data["calls"][key]["count"]
            )
            functions_instr[name][instr] += data["blocks"][key][instr]

        # Ponderate with the right call numbers
        block_instr = funct_instr * data["calls"][key]["count"]

        # Append for later :
        if name not in function_counts:
            function_counts[name] = 0
        function_counts[name] += block_instr

        total_instr += block_instr

    # Count unique instructions
    uniques = 0
    for values in functions_instr.values():
        for count in values.values():
            uniques += count

    # Sort and store the largest functions calls
    function_counts = dict(
        sorted(function_counts.items(), key=lambda x: x[1], reverse=True)
    )

    data["output"]["instructions"] = total_instr
    data["output"]["unique_instructions"] = uniques
    data["output"]["instructions_counts"] = instr_counts
    data["output"]["func_calls_instr"] = function_counts
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
    function_counts = dict(
        sorted(function_counts.items(), key=lambda x: x[1], reverse=True)
    )

    data["output"]["cycles"] = total_cycles
    data["output"]["cycles_count"] = cycles_counts
    data["output"]["func_calls_cycles"] = function_counts
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
        func_cpi[func] = (
            data["output"]["func_calls_cycles"][func]
            / data["output"]["func_calls_instr"][func]
        )

    # Sorting the func cpi list
    func_cpi = dict(sorted(func_cpi.items(), key=lambda x: x[1], reverse=True))

    # Store outputs
    data["output"]["cpi"] = cpi
    data["output"]["ipc"] = 1 / cpi
    data["output"]["func_cpi"] = func_cpi

    return data


def get_density(instr_dict: dict, cfg_dict: dict) -> dict:
    """
    Return densities of instruction from a defined set of instructions, depending on their type.
    Used to identify the bottlenecks for each sets.

    In order, it returns :
        - jumps
        - conditions
        - standard
        - muldiv
        - memory
        - specials (CSR)
    """

    # Prepare outputs and keys
    instr_types = [0, 0, 0, 0, 0, 0]
    instr_percents = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    names = ["jumps", "conditions", "arithmetic", "muldiv", "memory", "special"]

    # Filter the instruction, by their types
    for instr in instr_dict.keys():
        for index, name in enumerate(names):
            if instr.upper() in cfg_dict[name].keys():
                instr_types[index] += instr_dict[instr]

    # Compute the proportions
    total = sum(instr_types)
    for index, value in enumerate(instr_types):
        instr_percents[index] = value * 100 / total

    # Compute some regroupements
    branch_count = instr_types[0] + instr_types[1]
    arithmetic_count = instr_types[2] + instr_types[3]

    branch_percent = branch_count * 100 / total
    arithmetic_percent = arithmetic_count * 100 / total

    # set the output data
    outdict = dict()
    outdict["percents"] = dict(zip(names, instr_percents))
    outdict["counts"] = dict(zip(names, instr_types))

    outdict["branch_densities"] = branch_percent
    outdict["arithmetic_densities"] = arithmetic_percent
    outdict["memory_densities"] = instr_percents[4]
    outdict["special_densities"] = instr_percents[5]

    # Return the data
    return outdict


def compute_densities(data: dict) -> dict:
    """
    Compute various instructions densities, to get a view of the most used ones,
    and their proportions.
    """

    # First, load the config file
    cfg = dict()
    with open("config/instructions.toml", "rb") as file:
        cfg = tomllib.load(file)

    # First, get the whole density namings
    densities = get_density(data["output"]["instructions_counts"], cfg)
    func_densities = dict()

    # Then, compute the per functions densities
    for func, values in data["output"]["func_used_instr"].items():
        func_densities[func] = get_density(values, cfg)

    # Output data
    data["output"]["densities"] = densities
    data["output"]["func_densities"] = func_densities

    # Return
    return data


def compute_averages(data: dict) -> dict:
    """
    Compute some averages to be added, that can give us some infos about
    dfferent behaviors
    """
    func_nb = len(data["output"]["func_used_instr"])

    # Count the functions numbers
    data["output"]["averages"] = dict()
    data["output"]["averages"]["func_number"] = func_nb

    data["output"]["averages"]["instr_per_func"] = (
        data["output"]["unique_instructions"] / func_nb
    )

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
    data = compute_densities(data)
    data = compute_averages(data)
    data = compute_cpi(data)

    # Create the output file :
    write_json(output, data["output"])
