# Copyright 2024 ByteDance and/or its affiliates.
# Copyright 2026 IntelliGen-AI and/or its affiliates.
#
# This file includes modifications made by IntelliGen-AI.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import argparse
import pathlib
import shutil
import time
import logging
from pathlib import Path
from typing import Any, Optional

from intellifold.data.tools.search import HmmsearchConfig, run_hmmsearch_with_a3m
from intellifold.data.tools.logger import init_logging, get_logger
logger = get_logger(__name__)
init_logging()  


def ensure_ends_with_newline(s: str) -> str:
    """
    Ensure the string ends with a newline character.

    Args:
        s: The input string.

    Returns:
        The string with a trailing newline if it wasn't empty.
    """
    if not s.endswith("\n") and (len(s) > 0):
        s += "\n"
    return s


def run_template_search(
    msa_a3m_path_for_template_search: str,
    hmmsearch_a3m_save_path: str,
    hmmsearch_binary_path: Optional[str] = None,
    hmmbuild_binary_path: Optional[str] = None,
    seqres_database_path: Optional[str] = None,
) -> None:
    """
    Run template search using hmmsearch with a3m files.

    Args:
        msa_a3m_path_for_template_search: Path of containing MSA a3m/csv file for template search.
        hmmsearch_a3m_save_path: Path to save the hmmsearch a3m result, templates result.
        hmmsearch_binary_path: Path to hmmsearch binary.
        hmmbuild_binary_path: Path to hmmbuild binary.
        seqres_database_path: Path to sequence database.
    """
    # msa_a3m_path_for_template_search contains the paired/unpaired MSA files, used for template search
    assert msa_a3m_path_for_template_search is not None, "input msa dir should not be None"
    ## make sure the msa_a3m_path_for_template_search is a3m/csv formatted file, and read the content
    if not os.path.exists(msa_a3m_path_for_template_search):
        raise AssertionError(
            f"input msa  {msa_a3m_path_for_template_search} does not exist"
        )
    # Validate file extension: must be either .a3m or .csv
    if not (msa_a3m_path_for_template_search.endswith(".a3m") or msa_a3m_path_for_template_search.endswith(".csv")):
        raise AssertionError(
            f"input msa {msa_a3m_path_for_template_search} should be in a3m or csv format"
        )


    # hmmsearch_a3m_save_path is the output of hmmsearch, which contains the template search result, used for template modeling
    assert hmmsearch_a3m_save_path is not None, "hmmsearch a3m save path should not be None"
    

    if hmmsearch_binary_path is None:
        hmmsearch_binary_path = shutil.which("hmmsearch")
        if hmmsearch_binary_path is None:
            raise AssertionError(
                "hmmsearch binary path should not be None. You can install "
                "hmmer using: apt install hmmer or conda install -c bioconda hmmer"
            )
    else:
        if not os.path.exists(hmmsearch_binary_path):
            raise AssertionError(
                f"hmmsearch binary path {hmmsearch_binary_path} does not exist"
            )

    if hmmbuild_binary_path is None:
        hmmbuild_binary_path = shutil.which("hmmbuild")
        if hmmbuild_binary_path is None:
            raise AssertionError(
                "hmmbuild binary path should not be None. You can install "
                "hmmer using: apt install hmmer or conda install -c bioconda hmmer"
            )
    else:
        if not os.path.exists(hmmbuild_binary_path):
            raise AssertionError(
                f"hmmbuild binary path {hmmbuild_binary_path} does not exist"
            )

    if seqres_database_path is None:
        _HOME_DIR = pathlib.Path(os.environ.get("INTELLIFOLD_CACHE", str(Path.home())))
        _SEQRES_DATABASE_PATH = (
            _HOME_DIR / "search_database" / "pdb_seqres_2022_09_28.fasta"
        )
        seqres_database_path = _SEQRES_DATABASE_PATH.as_posix()
    
    if not os.path.exists(seqres_database_path):
        from intellifold.data.inference.utils import download_pdb_sequence_database
        # check the INTELLIFOLD_CACHE environment variable
        cache_dir = os.environ.get("INTELLIFOLD_CACHE")
        if cache_dir is None:
            raise AssertionError(
                "INTELLIFOLD_CACHE environment variable is not set. Please set it to a directory to store the cache data, including the template search database."
            )
        download_pdb_sequence_database(cache_dir)

    logger.info("Template search start!")
    template_start_time = time.time()
    hmmsearch_config = HmmsearchConfig(
        hmmsearch_binary_path=hmmsearch_binary_path,
        hmmbuild_binary_path=hmmbuild_binary_path,
        filter_f1=0.1,
        filter_f2=0.1,
        filter_f3=0.1,
        e_value=100,
        inc_e=100,
        dom_e=100,
        incdom_e=100,
        alphabet="amino",
    )
    max_a3m_query_sequences = 300
    
    if msa_a3m_path_for_template_search.endswith(".a3m"):
        with open(msa_a3m_path_for_template_search, "r") as f:
            msa_a3m = f.read()
    else:
        import pandas as pd
        msa_df = pd.read_csv(msa_a3m_path_for_template_search)
        msa_a3m = ''
        for _, row in msa_df.iterrows():
            seq_id = row['key']
            sequence = row['sequence']
            msa_a3m += f">{seq_id}\n{sequence}\n"
        
    msa_a3m = ensure_ends_with_newline(msa_a3m)
    hmmsearch_a3m = run_hmmsearch_with_a3m(
        database_path=seqres_database_path,
        hmmsearch_config=hmmsearch_config,
        max_a3m_query_sequences=max_a3m_query_sequences,
        a3m=msa_a3m,
    )

    with open(hmmsearch_a3m_save_path, "w") as f:
        f.write(hmmsearch_a3m)
    template_end_time = time.time()
    logger.info(
        f"Template search done!, using {template_end_time - template_start_time}"
    )
    logger.info(
        f"Template result is saved at: {hmmsearch_a3m_save_path}"
    )


if __name__ == "__main__":
    
    argparse = argparse.ArgumentParser(description="Run template search using hmmsearch with a3m files.")
    argparse.add_argument(
        "--input_msa",
        type=str,
        required=True,
        help="Path of containing MSA a3m/csv file for template search.",
    )
    argparse.add_argument(
        "--output_template",
        type=str,
        required=True,
        help="Path to save the hmmsearch a3m result, templates result.",
    )
    argparse.add_argument(
        "--hmmsearch_binary_path",
        type=str,
        default=None,
        help="Path to hmmsearch binary. If not provided, will try to find it in the system PATH.",
    )
    argparse.add_argument(
        "--hmmbuild_binary_path",
        type=str,
        default=None,
        help="Path to hmmbuild binary. If not provided, will try to find it in the system PATH.",
    )
    argparse.add_argument(
        "--seqres_database_path",
        type=str,
        default=None,
        help="Path to sequence database. If not provided, will use the default pdb_seqres_2022_09_28.fasta database in the cache directory.",
    )
    args = argparse.parse_args()
    
    
    run_template_search(
        msa_a3m_path_for_template_search=args.input_msa,
        hmmsearch_a3m_save_path=args.output_template,
        hmmsearch_binary_path=args.hmmsearch_binary_path,
        hmmbuild_binary_path=args.hmmbuild_binary_path,
        seqres_database_path=args.seqres_database_path,
    )
    
    # run_template_search(
    #     msa_a3m_path_for_template_search="./output/1csb_prot/msa/1csb_prot_0_unpaired.a3m",
    #     hmmsearch_a3m_save_path="./output/1csb_prot/msa/1csb_prot_0_unpaired_hmmsearch.a3m",
    #     # msa_a3m_path_for_template_search="./output/1csb_prot/msa/1csb_prot_0.csv",
    #     # hmmsearch_a3m_save_path="./output/1csb_prot/msa/1csb_prot_0_unpaired_hmmsearch_2.a3m",
    # )
