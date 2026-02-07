## ⚙️ Installation
>To more complete installation instructions and usage, please refer below.

1. **Clone the repository**
    ```bash
    git clone https://github.com/IntelliGen-AI/IntelliFold.git
    cd IntelliFold
    ```

2. **Create and activate the environment(recommended)**
    ```bash
    conda env create -f environment.yaml
    conda activate intellifold
    ```

3. **Install the package**
    - From PyPI (recommended):
      ```bash
      pip install intellifold
      ```
    - From local wheel:
      ```bash
      pip install pypi/intellifold-2.0.0-py3-none-any.whl
      ```
    - Editable install:
      ```bash
      pip install -e .
      ```

4. **(Optional) Download IntelliFold Cache Data Manually**<br>
    By default, model weights and CCD data are downloaded automatically(the directory is `~/.intellifold`) when you run the inference. But you can also download by yourself.
    To download manually from [Our HuggingFace Repository](https://huggingface.co/intelligenAI/intellifold):  

    You can use `HF_ENDPOINT=huggingface.co` or `HF_ENDPOINT=hf-mirror.com` depending on your network.  

    ```bash
    HF_ENDPOINT=huggingface.co bash download_cache_data.sh
    ```

    Your directory should look like:
    ```
    cache_data/
    |---intellifold_v2_flash.pt
    |---intellifold_v2.pt
    ├── intellifold_v0.1.0.pt
    ├── ccd.pkl
    ├── unique_protein_sequences.fasta
    ├── unique_nucleic_acid_sequences.fasta
    ├── protein_id_groups.json
    └── nucleic_acid_id_groups.json
    ```
    Place the downloaded files in the `cache_data/` directory before running inference.