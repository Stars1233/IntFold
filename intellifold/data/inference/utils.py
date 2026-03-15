# Copyright (c) 2024 Jeremy Wohlwend, Gabriele Corso, Saro Passaro
#
# Licensed under the MIT License:
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import urllib.request
from pathlib import Path

from intellifold.data.tools.logger import init_logging, get_logger
logger = get_logger(__name__)
init_logging()

### Add Request Header
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
urllib.request.install_opener(opener)
HF_ENDPOINT = os.environ.get("HF_ENDPOINT", "huggingface.co")

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

_HF_REPO_BASE = f"https://huggingface.co/intelligenAI/intellifold/resolve/main"
_HF_MIRROR_BASE = "https://hf-mirror.com/intelligenAI/intellifold/resolve/main"


# #### huggingface offical URL
# CCD_URL = f"{_HF_REPO_BASE}/ccd_v2.pkl"
# MODEL_URL = (
#     f"{_HF_REPO_BASE}/intellifold_v0.1.0.pt"
# )
# V2_FLASH_MODEL_URL = (
#     f"{_HF_REPO_BASE}/intellifold_v2_flash.pt"
# )
# V2_MODEL_URL = (
#     f"{_HF_REPO_BASE}/intellifold_v2.pt"
# )
# PROTEIN_PDB_SEQUENCES_URL = f"{_HF_REPO_BASE}/unique_protein_sequences.fasta"
# RNA_PDB_SEQUENCES_URL = f"{_HF_REPO_BASE}/unique_nucleic_acid_sequences.fasta"
# PROTEIN_PDB_GROUPS_URL = f"{_HF_REPO_BASE}/protein_id_groups.json"
# RNA_PDB_GROUPS_URL = f"{_HF_REPO_BASE}/nucleic_acid_id_groups.json"
# PROTEIN_SEQRES_DATABASE_URL = f"{_HF_REPO_BASE}/pdb_seqres_2022_09_28.fasta"


# #### huggingface-mirror URL
# CCD_MIRROR_URL = f"{_HF_MIRROR_BASE}/ccd_v2.pkl"
# MODEL_MIRROR_URL = (
#     f"{_HF_MIRROR_BASE}/intellifold_v0.1.0.pt"
# )
# V2_FLASH_MODEL_MIRROR_URL = (
#     f"{_HF_MIRROR_BASE}/intellifold_v2_flash.pt"
# )
# V2_MODEL_MIRROR_URL = (
#     f"{_HF_MIRROR_BASE}/intellifold_v2.pt"
# )
# PROTEIN_PDB_SEQUENCES_MIRROR_URL = f"{_HF_MIRROR_BASE}/unique_protein_sequences.fasta"
# RNA_PDB_SEQUENCES_MIRROR_URL = f"{_HF_MIRROR_BASE}/unique_nucleic_acid_sequences.fasta"
# PROTEIN_PDB_GROUPS_MIRROR_URL = f"{_HF_MIRROR_BASE}/protein_id_groups.json"
# RNA_PDB_GROUPS_MIRROR_URL = f"{_HF_MIRROR_BASE}/nucleic_acid_id_groups.json"
# PROTEIN_SEQRES_DATABASE_MIRROR_URL = f"{_HF_MIRROR_BASE}/pdb_seqres_2022_09_28.fasta"
    

def download(
    cache: Path, 
    model: str,
    use_template: bool = False) -> None:
    """Download all the required data.

    Parameters
    ----------
    cache : Path
        The cache directory.

    """
    _SELECTED_BASE_URL = _HF_REPO_BASE 


    # Download CCD
    ccd = cache / "ccd_v2.pkl"
    CCD_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/ccd_v2.pkl"
    
    if not ccd.exists():
        print(
            f"Downloading the CCD dictionary to {ccd}. You may "
            "change the cache directory with the --cache flag."
        )
        try:
            urllib.request.urlretrieve(CCD_DOWNLOAD_URL, str(ccd), reporthook=progress_callback) 
        except:
            ### use hf-mirror.com
            _SELECTED_BASE_URL = (_HF_MIRROR_BASE if _SELECTED_BASE_URL == _HF_REPO_BASE else _HF_REPO_BASE)
            CCD_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/ccd_v2.pkl"
            urllib.request.urlretrieve(CCD_DOWNLOAD_URL, str(ccd), reporthook=progress_callback)
            
    # Download model
    if model == "v1":
        MODEL_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/intellifold_v0.1.0.pt"
        model = cache / "intellifold_v0.1.0.pt"
        if not model.exists():
            print(
                f"Downloading the model weights to {model}. You may "
                "change the cache directory with the --cache flag."
            )
            try:
                urllib.request.urlretrieve(MODEL_DOWNLOAD_URL, str(model), reporthook=progress_callback)
            except:
                _SELECTED_BASE_URL = (_HF_MIRROR_BASE if _SELECTED_BASE_URL == _HF_REPO_BASE else _HF_REPO_BASE)
                MODEL_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/intellifold_v0.1.0.pt"
                urllib.request.urlretrieve(MODEL_DOWNLOAD_URL, str(model), reporthook=progress_callback)
                
    elif model == "v2-flash":
        # Download v2 flash model
        V2_FLASH_MODEL_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/intellifold_v2_flash.pt"
        v2_flash_model = cache / "intellifold_v2_flash.pt"
        if not v2_flash_model.exists():
            print(
                f"Downloading the v2 flash model weights to {v2_flash_model}. You may "
                "change the cache directory with the --cache flag."
            )
            try:
                urllib.request.urlretrieve(V2_FLASH_MODEL_DOWNLOAD_URL, str(v2_flash_model), reporthook=progress_callback) 
            except:
                _SELECTED_BASE_URL = (_HF_MIRROR_BASE if _SELECTED_BASE_URL == _HF_REPO_BASE else _HF_REPO_BASE)
                V2_FLASH_MODEL_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/intellifold_v2_flash.pt"
                urllib.request.urlretrieve(V2_FLASH_MODEL_DOWNLOAD_URL, str(v2_flash_model), reporthook=progress_callback)
    elif model == "v2":
        # Download v2 model
        V2_MODEL_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/intellifold_v2.pt"
        v2_model = cache / "intellifold_v2.pt"
        if not v2_model.exists():
            print(
                f"Downloading the v2 model weights to {v2_model}. You may "
                "change the cache directory with the --cache flag."
            )
            try:
                urllib.request.urlretrieve(V2_MODEL_DOWNLOAD_URL, str(v2_model), reporthook=progress_callback)
            except:
                _SELECTED_BASE_URL = (_HF_MIRROR_BASE if _SELECTED_BASE_URL == _HF_REPO_BASE else _HF_REPO_BASE)
                V2_MODEL_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/intellifold_v2.pt"
                urllib.request.urlretrieve(V2_MODEL_DOWNLOAD_URL, str(v2_model), reporthook=progress_callback)
    else:
        raise ValueError(f"Invalid model: {model} for downloading model weights.")
            
    # Download Protein Sequences database
    PROTEIN_PDB_SEQUENCES_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/unique_protein_sequences.fasta"
    protein_sequences = cache / "unique_protein_sequences.fasta"
    if not protein_sequences.exists():
        print(
            f"Downloading the protein sequences to {protein_sequences}. You may "
            "change the cache directory with the --cache flag."
        )
        try:
            urllib.request.urlretrieve(PROTEIN_PDB_SEQUENCES_DOWNLOAD_URL, str(protein_sequences), reporthook=progress_callback)
        except:
            _SELECTED_BASE_URL = (_HF_MIRROR_BASE if _SELECTED_BASE_URL == _HF_REPO_BASE else _HF_REPO_BASE)
            PROTEIN_PDB_SEQUENCES_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/unique_protein_sequences.fasta"
            urllib.request.urlretrieve(PROTEIN_PDB_SEQUENCES_DOWNLOAD_URL, str(protein_sequences), reporthook=progress_callback)
            
    # Download RNA Sequences database
    RNA_PDB_SEQUENCES_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/unique_nucleic_acid_sequences.fasta"
    rna_sequences = cache / "unique_nucleic_acid_sequences.fasta"
    if not rna_sequences.exists():
        print(
            f"Downloading the RNA sequences to {rna_sequences}. You may "
            "change the cache directory with the --cache flag."
        )
        try:
            urllib.request.urlretrieve(RNA_PDB_SEQUENCES_DOWNLOAD_URL, str(rna_sequences), reporthook=progress_callback)
        except:
            _SELECTED_BASE_URL = (_HF_MIRROR_BASE if _SELECTED_BASE_URL == _HF_REPO_BASE else _HF_REPO_BASE)
            RNA_PDB_SEQUENCES_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/unique_nucleic_acid_sequences.fasta"
            urllib.request.urlretrieve(RNA_PDB_SEQUENCES_DOWNLOAD_URL, str(rna_sequences), reporthook=progress_callback)
            
    # Download protein id groups
    PROTEIN_PDB_GROUPS_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/protein_id_groups.json"
    protein_groups = cache / "protein_id_groups.json"
    if not protein_groups.exists():
        print(
            f"Downloading the protein id groups to {protein_groups}. You may "
            "change the cache directory with the --cache flag."
        )
        try:
            urllib.request.urlretrieve(PROTEIN_PDB_GROUPS_DOWNLOAD_URL, str(protein_groups), reporthook=progress_callback)
        except:
            _SELECTED_BASE_URL = (_HF_MIRROR_BASE if _SELECTED_BASE_URL == _HF_REPO_BASE else _HF_REPO_BASE)
            PROTEIN_PDB_GROUPS_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/protein_id_groups.json"
            urllib.request.urlretrieve(PROTEIN_PDB_GROUPS_DOWNLOAD_URL, str(protein_groups), reporthook=progress_callback)
            
    # Download RNA id groups
    RNA_PDB_GROUPS_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/nucleic_acid_id_groups.json"
    rna_groups = cache / "nucleic_acid_id_groups.json"
    if not rna_groups.exists():
        print(
            f"Downloading the RNA id groups to {rna_groups}. You may "
            "change the cache directory with the --cache flag."
        )
        try:
            urllib.request.urlretrieve(RNA_PDB_GROUPS_DOWNLOAD_URL, str(rna_groups), reporthook=progress_callback)
        except:
            _SELECTED_BASE_URL = (_HF_MIRROR_BASE if _SELECTED_BASE_URL == _HF_REPO_BASE else _HF_REPO_BASE)
            RNA_PDB_GROUPS_DOWNLOAD_URL = f"{_SELECTED_BASE_URL}/nucleic_acid_id_groups.json"
            urllib.request.urlretrieve(RNA_PDB_GROUPS_DOWNLOAD_URL, str(rna_groups), reporthook=progress_callback)
            
    if use_template:
        download_template_data(str(cache))


def get_cache_path() -> str:
    """Determine the cache path, prioritising the INTELLIFOLD_CACHE environment variable.

    Returns
    -------
    str: Path
        Path to use for intellifold cache location.

    """
    env_cache = os.environ.get("INTELLIFOLD_CACHE")
    if env_cache:
        resolved_cache = Path(env_cache).expanduser().resolve()
        if not resolved_cache.is_absolute():
            raise ValueError(f"INTELLIFOLD_CACHE must be an absolute path, got: {env_cache}")
        return str(resolved_cache)

    return str(Path("~/.intellifold").expanduser())


def download_template_data(cache_dir: str) -> None:
    """Download the template data.

    Parameters
    ----------
    cache : str
        The cache directory.

    """
    URL = {
        "obsolete_pdbs_path": "https://protenix.tos-cn-beijing.volces.com/common/obsolete_to_successor.json", ## 85KB
        "release_dates_path": "https://protenix.tos-cn-beijing.volces.com/common/release_date_cache.json",    ## 13MB
        "mmcif_dir": "https://protenix.tos-cn-beijing.volces.com/mmcif.tar.gz"                                ## 83GB, after extraction, it will be 283GB
    }
    for cache_name in (
            "obsolete_pdbs_path",
            "release_dates_path",
        ):
            cur_cache_fpath = os.path.join(cache_dir, "common", os.path.basename(URL[cache_name]))
            if not os.path.exists(cur_cache_fpath):
                os.makedirs(os.path.dirname(cur_cache_fpath), exist_ok=True)
                tos_url = URL[cache_name]
                assert os.path.basename(tos_url) == os.path.basename(cur_cache_fpath), (
                    f"{cache_name} file name is incorrect, `{tos_url}` and "
                    f"`{cur_cache_fpath}`. Please check and try again."
                )
                logger.info(
                    f"Downloading data cache \n to {cur_cache_fpath}"
                )
                download_from_url(tos_url, cur_cache_fpath)
                
            else:
                logger.info(f"{cache_name} already exists at {cur_cache_fpath}")
                
    ## download mmcif dir
    mmcif_dir = os.path.join(cache_dir, "mmcif")
    if not os.path.exists(mmcif_dir):
        ros_url = URL["mmcif_dir"]
        cur_cache_fpath = os.path.join(cache_dir, "mmcif.tar.gz")
        logger.info(
            f"Downloading mmcif.tar.gz \n to {cur_cache_fpath}"
        )
        download_from_url(ros_url, cur_cache_fpath)
        if os.path.exists(cur_cache_fpath):
            logger.info(f"Extracting mmcif.tar.gz to {mmcif_dir}...")
            os.system(f"tar -xzf {cur_cache_fpath} -C {cache_dir}")
            ## remove the tar.gz file after extraction
            os.remove(cur_cache_fpath)
        else:
            logger.error(f"Failed to download mmcif.tar.gz from {ros_url}. Please try downloading it manually and placing it at {cur_cache_fpath} before extracting.")
    else:
        logger.info(f"mmcif directory already exists at {mmcif_dir}")
      
    ## download pdb_seqres database
    download_pdb_sequence_database(cache_dir)
        
        
def download_pdb_sequence_database(cache_dir: str) -> None:
    """Download the pdb sequence database.

    Parameters
    ----------
    cache : str
        The cache directory.

    """
    search_database_dir = os.path.join(cache_dir, "search_database")
    os.makedirs(search_database_dir, exist_ok=True)
    pdb_seqres_fpath = os.path.join(search_database_dir, "pdb_seqres_2022_09_28.fasta")
    if not os.path.exists(pdb_seqres_fpath):
        try:
            # tos_url = PROTEIN_SEQRES_DATABASE_URL
            tos_url = f'{_HF_REPO_BASE}/pdb_seqres_2022_09_28.fasta'
            logger.info(
                f"Downloading pdb_seqres database \n to {pdb_seqres_fpath}"
            )
            urllib.request.urlretrieve(tos_url, pdb_seqres_fpath, reporthook=progress_callback)
        except Exception as e:
            ## use hf-mirror.com
            # tos_url = PROTEIN_SEQRES_DATABASE_MIRROR_URL
            tos_url = f'{_HF_MIRROR_BASE}/pdb_seqres_2022_09_28.fasta'
            try:
                urllib.request.urlretrieve(tos_url, pdb_seqres_fpath, reporthook=progress_callback)
            except Exception as e:
                raise RuntimeError(
                    f"Download pdb_seqres database failed: {e}. Please download "
                    f"manually with: wget {tos_url} -O {pdb_seqres_fpath}"
                ) from e
    else:
        logger.info(f"pdb_seqres database already exists at {pdb_seqres_fpath}")
        
# def progress_callback(block_num: int, block_size: int, total_size: int) -> None:
#     """Callback for tracking download progress."""
#     downloaded = block_num * block_size
#     percent = min(100, downloaded * 100 / total_size)
#     bar_length = 30
#     filled_length = int(bar_length * percent // 100)
#     bar = "=" * filled_length + "-" * (bar_length - filled_length)

#     status = f"\r[{bar}] {percent:.1f}%"
#     print(status, end="", flush=True)

#     if downloaded >= total_size:
#         print()

def progress_callback(block_num: int, block_size: int, total_size: int) -> None:
    downloaded = block_num * block_size
    bar_length = 30

    if total_size is None or total_size <= 0:
        print(f"\rDownloaded {downloaded / 1024:.1f} KB", end="", flush=True)
        return

    percent = min(100.0, downloaded * 100.0 / total_size)
    filled_length = int(bar_length * percent / 100)
    bar = "=" * filled_length + "-" * (bar_length - filled_length)

    print(f"\r[{bar}] {percent:.1f}%", end="", flush=True)

    if downloaded >= total_size:
        print()
                          
def download_from_url(
    tos_url: str, tgt_path: str
) -> None:
    """Internal helper to download from URL"""
    try:
        urllib.request.urlretrieve(tos_url, tgt_path, reporthook=progress_callback)
    except Exception as e:
        raise RuntimeError(
                f"Download model checkpoint failed: {e}. Please download "
                f"manually with: wget {tos_url} -O {tgt_path}"
            ) from e