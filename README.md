# ascon-power-trace-framework
A Framework for ASCON Power Trace Generation and Analysis on the ChipWhisperer Platform
# A Framework for ASCON Power Trace Generation and Analysis on the ChipWhisperer Platform

**Researcher:** Shravani.S.Pujari  
**Institution:** KLE Technological University, Hubballi  
**Programme:** Research Experience for Undergraduates (REU)  
**Laboratory:** CIM Lab  
**Batch:** 2026–27

## 1. Project Overview

This project focuses on generating and analysing power traces of the ASCON-128 lightweight authenticated encryption algorithm using the ChipWhisperer platform.

The work includes unmasked power-trace collection, first-order Correlation Power Analysis (CPA), and investigations into masked implementations using second-order CPA techniques.

The objective is to study side-channel leakage and evaluate key-recovery behaviour under different trace-count conditions.

## 2. Problem Statement

Power consumption during cryptographic operations can reveal information about internal computations and secret-dependent intermediate values. Side-channel analysis techniques such as CPA use these variations to investigate potential information leakage.

This project establishes a practical framework for collecting and analysing ASCON power traces and studying the effectiveness of first-order and second-order analysis approaches.

## 3. Objectives

- Set up the ChipWhisperer environment for ASCON power-trace collection.
- Collect power traces from unmasked and masked ASCON implementations.
- Perform first-order CPA on unmasked ASCON traces.
- Evaluate key-recovery accuracy at different trace counts.
- Investigate second-order CPA approaches for masked ASCON traces.
- Analyse and compare experimental results using plots and summary data.

## 4. Hardware and Software

**Hardware platform**
- ChipWhisperer CW-Lite
- ChipWhisperer CW308 target platform
- STM32F3-series target microcontroller (STM32F303)

**Software and tools**
- Python
- Jupyter Notebook
- ChipWhisperer software
- NumPy and Pandas
- Matplotlib
- Git

## 5. Repository Structure

```text
ascon-power-trace-framework/
│
├── notebooks/
│   ├── unmasked/
│   │   └── ascon_unmasked.ipynb
│   └── masked/
│       └── ascon_masked.ipynb
│
├── firmware/
│   ├── unmasked/
│   └── masked/
│
├── python_scripts/
│   ├── first_order_cpa/
│   └── second_order_cpa/
│
├── analysis_scripts/
│   ├── comparison/
│   ├── correlation_analysis/
│   └── key_recovery/
│
├── results/
│   ├── unmasked_first_order_cpa/
│   ├── masked_second_order_cpa/
│   └── comparison/
│
├── .gitignore
└── README.md
```

## 6. Experimental Results

### 6.1 Unmasked ASCON — First-Order CPA

The first-order CPA experiments were evaluated at trace counts of 1,000, 2,000, 5,000, 10,000 and 15,000.

The recorded results are:

| Trace count | X1 accuracy | X2 accuracy |
|---:|---:|---:|
| 1,000 | 87.50% | 85.94% |
| 2,000 | 93.75% | 90.625% |
| 5,000 | 100% | 100% |
| 10,000 | 100% | 100% |
| 15,000 | 100% | 100% |

At 5,000 traces, both evaluated 64-bit targets reached 64 correct bits out of 64 in the experiment summary.

**Interpretation:** These are results for the separately evaluated X1 and X2 targets. The X2 configuration uses a previously supplied X1 value. These results should not be interpreted as proof of simultaneous or independent full 128-bit key recovery.

The detailed public summary is available in:

`results/unmasked_first_order_cpa/key_recovery_summary_public.csv`

### 6.2 Masked ASCON — Second-Order CPA

The masked ASCON implementation is being investigated using second-order CPA techniques.

The repository includes analysis scripts, comparison data and expected-rank plots for the evaluated configurations. Further investigation is required; successful masked key recovery is not claimed.

## 7. Current Project Progress

- ChipWhisperer platform setup and ASCON trace collection.
- Unmasked ASCON power-trace collection.
- First-order CPA implementation and evaluation.
- Key-recovery accuracy evaluation at multiple trace counts.
- Masked ASCON power-trace collection.
- Second-order CPA investigation and result comparison.

## 8. Repository Contents and Data

This repository contains source code, notebooks, firmware, analysis scripts and selected experimental results.

Raw power-trace datasets and temporary files are not included in the public repository. The notebooks may require the ChipWhisperer hardware platform and the corresponding software environment to reproduce the measurements.

## 9. Researcher

**Shravani.S.Pujari**  
Electronics and Communication Engineering  
KLE Technological University, Hubballi  
CIM Lab — REU Batch 2026–27

