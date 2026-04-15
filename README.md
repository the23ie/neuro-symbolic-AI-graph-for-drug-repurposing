# Neuro-Symbolic AI Graph for Drug Repurposing

A project for exploring and applying neuro-symbolic artificial intelligence (AI) and graph-based methods to the field of drug repurposing. The main goal is to leverage the strengths of neural and symbolic AI alongside graph-based data structures to discover and recommend new uses for existing drugs.

## Features

- **Graph Construction**: Builds comprehensive graphs of drug-protein-disease interactions.
- **Neuro-Symbolic Reasoning**: Combines symbolic logic rules with neural learning for improved AI inference.
- **Automated Drug Repurposing**: Suggests possible repurposing candidates using graph-based algorithms and AI reasoning.
- **Data Integration**: Integrates biomedical datasets into graph representations suitable for neuro-symbolic analysis.
- **Visualization**: Tools and scripts for visual exploration of the drug-disease-protein relationship network.

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/the23ie/neuro-symbolic-AI-graph-for-drug-repurposing.git
   cd neuro-symbolic-AI-graph-for-drug-repurposing
   ```

2. **Install the requirements**

   ```
   pip install -r requirements.txt
   ```
   *(Make sure to check or create `requirements.txt` listing your dependencies.)*

3. **Download and prepare data**
   - Add steps here for sourcing and formatting the required dataset(s), if any.

## Usage

1. **Prepare data:**
   - Place or preprocess biomedical datasets as described in the `/data` folder.

2. **Build the neuro-symbolic graph:**
   ```bash
   python scripts/build_graph.py
   ```

3. **Run drug repurposing analysis:**
   ```bash
   python scripts/repurposing_analysis.py
   ```

4. **View results:**
   - Outputs or visualizations will be in the `/results` or `/output` directory.


## Contact

Project maintained by [the23ie](https://github.com/the23ie).
