# ascon-power-trace-framework
A Framework for ASCON Power Trace Generation and Analysis on the ChipWhisperer Platform
# A Framework for ASCON Power Trace Generation and Analysis on the ChipWhisperer Platform

## 1. Project Overview

This research project focuses on developing a framework for power-trace generation and analysis of the ASCON-128 lightweight authenticated encryption algorithm using the ChipWhisperer platform.

The project involves collecting power traces, performing first-order Correlation Power Analysis (CPA) on unmasked ASCON-128, and investigating second-order CPA techniques for masked ASCON-128 implementations.

The research aims to study the effectiveness of side-channel analysis techniques and evaluate key-recovery performance under different experimental conditions.

## 2. Problem Statement

Power consumption during cryptographic operations can depend on the intermediate values processed by the implementation. These variations can be analyzed using side-channel techniques to infer information about secret cryptographic keys.

Masking is a countermeasure that uses multiple shares to protect sensitive intermediate values. Although masking makes direct first-order leakage analysis more difficult, higher-order side-channel analysis may still reveal information by combining leakage from multiple shares.

This project aims to develop a systematic framework for generating and analyzing ASCON-128 power traces using ChipWhisperer, studying both unmasked and masked implementations, and evaluating suitable side-channel analysis techniques.

## 3. Objectives

1. Study the ASCON-128 lightweight authenticated encryption algorithm and its internal operations.
2. Understand power side-channel attacks and masking countermeasures.
3. Develop a workflow for collecting power traces using the ChipWhisperer platform.
4. Perform first-order CPA experiments on unmasked ASCON-128 power traces.
5. Investigate second-order CPA techniques for masked ASCON-128 implementations.
6. Study suitable selection functions, trace preprocessing, and correlation analysis.
7. Evaluate key-recovery performance at different trace counts.
8. Analyze the effectiveness and limitations of side-channel analysis techniques.

## 4. Research Methodology

The project follows these major stages:

1. **Algorithm Study:** Understand ASCON-128, its initialization, permutation, and key-dependent intermediate operations.
2. **Trace Generation:** Capture power traces during cryptographic operations using the ChipWhisperer measurement platform.
3. **Trace Examination:** Inspect trace samples and metadata, including key and nonce information required for controlled experiments.
4. **Unmasked CPA:** Apply first-order CPA to unmasked ASCON-128 traces to identify key-dependent leakage.
5. **Key Recovery Experiments:** Evaluate key-recovery performance using different numbers of power traces.
6. **Masked Implementation Study:** Examine the masked ASCON-128 implementation and understand its share-generation mechanism.
7. **Second-Order Analysis:** Investigate centered-product preprocessing and second-order correlation analysis using suitable selection functions.
8. **Evaluation:** Compare experimental results and study trace-count requirements and attack limitations.

## 5. Technologies and Tools

- **Cryptographic Algorithm:** ASCON-128
- **Programming Language:** Python
- **Side-Channel Measurement Platform:** ChipWhisperer
- **Hardware:** CW-Lite and CW308 with STM32-based target setup
- **Analysis Libraries:** NumPy
- **Development Environment:** Ubuntu Linux and Jupyter Notebook
- **Trace Data Format:** TRS
- **Version Control:** Git and GitHub

## 6. Trace Count and Key Recovery Results – Unmasked ASCON-128

Experiments were conducted using different numbers of power traces to evaluate the effectiveness of first-order Correlation Power Analysis (CPA) on the unmasked ASCON-128 implementation.

| Number of Traces | Experimental Observation |
|---:|---|
| 2,000 | Preliminary first-order CPA key-recovery experiment |
| 5,000 | Full 128-bit ASCON-128 key recovery achieved using first-order CPA on the unmasked implementation |

The full 128-bit key recovery achieved with 5,000 traces demonstrates the effectiveness of the evaluated first-order CPA setup under the experimental conditions.

**Note:** The reported trace count is specific to the evaluated unmasked implementation, dataset, and analysis configuration. It is not a universal trace requirement for ASCON-128.

## 7. Current Project Progress

### 7.1 Completed Work

- Studied the ASCON-128 algorithm and fundamentals of power side-channel analysis.
- Established a power-trace collection and analysis workflow using ChipWhisperer.
- Collected and examined unmasked ASCON-128 power-trace datasets.
- Implemented and evaluated first-order CPA on unmasked ASCON-128.
- Conducted key-recovery experiments using different trace counts.
- Achieved full 128-bit key recovery using 5,000 traces in the evaluated unmasked first-order CPA experiment.

### 7.2 Ongoing Work

- Analysis of the masked ASCON-128 implementation and its share-generation mechanism.
- Investigation of second-order CPA and centered-product trace preprocessing.
- Evaluation of selection functions and key-candidate correlation rankings.
- Study of trace-count requirements and reliability of masked side-channel analysis.
- Further evaluation and documentation of masked implementation results.

**Note:** Second-order CPA analysis on the masked implementation is ongoing. Successful masked-key recovery has not yet been established.

## 8. Expected Outcomes

- A documented workflow for generating and examining ASCON-128 power traces.
- An experimental framework for first-order CPA-based key-recovery analysis.
- Evaluation of key-recovery performance at different trace counts.
- An experimental study of second-order CPA techniques for masked ASCON-128.
- An understanding of the challenges and limitations of higher-order side-channel analysis.

## 9. Repository Contents

This repository is intended to contain:

- Power-trace collection scripts and notebooks.
- Analysis source code and scripts.
- Trace-processing and correlation-analysis utilities.
- Experimental configuration files.
- Documentation and result summaries.

Large raw trace datasets, generated checkpoints, and sensitive experimental data are not included in the repository.

## 10. Researcher Details

**Name:** Shravani.S.Pujari

**Programme:** REU — CIM Lab, Batch 2026–27

**Institution:** KLE Technological University, Hubballi

---

*This repository documents ongoing research on ASCON power-trace generation and analysis using the ChipWhisperer platform.*
