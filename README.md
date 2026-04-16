# ProteinDance

ProteinDance is an AI-integrated, structure-based pipeline for end-to-end drug discovery, combining protein structure analysis, generative modeling, and automated decision-making into a unified workflow.

## 📄 Paper

- PDF: https://github.com/MarvinCui/proteindance/blob/main/ProteinDance.pdf

The paper introduces a modular pipeline that integrates target identification, protein structure retrieval, pocket prediction, ligand discovery, and generative molecule design into a single automated framework  [oai_citation:1‡ProteinDance.pdf](sediment://file_00000000f3fc71f5a94bc0ed90ad10fd)

## 🤖 Open-source Model

- Hugging Face: https://huggingface.co/ProteinDance/ProteinSkier

ProteinSkier is the core generative model in this project. It is a Transformer-based autoregressive model trained on SMILES sequences and further optimized using reinforcement-style fine-tuning to balance novelty and drug-likeness  [oai_citation:2‡ProteinDance.pdf](sediment://file_00000000f3fc71f5a94bc0ed90ad10fd)

## 🚀 Overview

ProteinDance implements a full drug discovery pipeline covering key stages:

- Target identification with AI-guided selection  
- Protein 3D structure retrieval (PDB or AlphaFold)  
- Binding pocket detection  
- Ligand retrieval and AI-based molecule generation  
- Lead optimization and ADMET evaluation  

The system integrates AI reasoning at each step, enabling automated progression from disease input to candidate drug molecules  [oai_citation:3‡ProteinDance.pdf](sediment://file_00000000f3fc71f5a94bc0ed90ad10fd)

## 🧠 Key Features

- Structure-based workflow centered on protein 3D geometry  
- Transformer-based generative model for molecule design  
- Reinforcement-style optimization using novelty and QED scoring  
- End-to-end integration from target discovery to lead generation  
