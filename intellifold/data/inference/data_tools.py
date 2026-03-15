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
import subprocess
import shutil
import pickle
import logging
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from intellifold.data import const
from intellifold.data.types import MSA, Manifest, Record
from intellifold.data.msa.mmseqs2 import run_mmseqs2
from intellifold.data.parse.a3m import parse_a3m
from intellifold.data.parse.csv import parse_csv
from intellifold.data.parse.yaml import parse_yaml
from runner.run_templates_search import run_template_search


logger = logging.getLogger(__name__)


def check_inputs(
    data: Path,
) -> list[Path]:
    """Check the input data and output directory.

    If the input data is a directory, it will be expanded
    to all files in this directory. Then, we check if there
    are any existing predictions and remove them from the
    list of input data, unless the override flag is set.

    Parameters
    ----------
    data : Path
        The input data.

    Returns
    -------
    list[Path]
        The list of input data.

    """
    logger.info("Checking input data.")

    # Check if data is a directory
    if data.is_dir():
        ### only for .yml, .yaml file types
        data = list(data.glob("*.yml")) + list(data.glob("*.yaml"))
    
    else:
        # Check if data is a file
        if not data.exists():
            msg = f"Input data {data} does not exist."
            raise FileNotFoundError(msg)            
        if data.suffix in (".yml", ".yaml"):
            data = [data]
        else:
            msg = (
                f"Unable to parse filetype {data.suffix}, "
                "please provide a .yaml file."
            )
            raise RuntimeError(msg)
                
    return data

def check_outputs(
    record: Record,
    struct_dir: Path,
    seed: int,
    num_diffusion_samples: int,
    output_format: str,
):
    """Check the predictions have been generated.
    Parameters
    ----------
    record : Record
        The record to check.
    struct_dir : Path
        The directory where the predictions are stored.
    seed : int
        The seed used for the predictions.
    num_diffusion_samples : int
        The number of diffusion samples.
    output_format : str
        The output format of the predictions.
    Returns
    -------
    bool
        True if the predictions have been generated, False otherwise.

    """
    if not struct_dir.exists():
        return False
    
    for i in range(num_diffusion_samples):
        outname = f"{record.id}_seed-{seed}_sample-{i}"
        if output_format == "pdb":
            struc_output_path = struct_dir / f"{outname}.pdb"
        else:
            struc_output_path = struct_dir / f"{outname}.cif"
        outname = f"{record.id}_seed-{seed}_sample-{i}_summary_confidences.json"
        summary_confidences_output_path = struct_dir / outname
        outname = f"{record.id}_seed-{seed}_sample-{i}_confidences.json"
        confidences_output_path = struct_dir / outname
        
        if struc_output_path.exists() and summary_confidences_output_path.exists() and confidences_output_path.exists():
            continue
        else:
            return False
        
    return True
    

def compute_msa(
    data: dict[str, str],
    generate_template: dict[str, bool],
    target_id: str,
    msa_dir: Path,
    msa_server_url: str,
    msa_pairing_strategy: str,
    use_pairing=True,
    use_template=False,
) -> None:
    """Compute the MSA for the input data.

    Parameters
    ----------
    data : dict[str, str]
        The input protein sequences.
    generate_template : dict[str, bool]
        Whether to generate template for each sequence.
    target_id : str
        The target id.
    msa_dir : Path
        The msa directory.
    msa_server_url : str
        The MSA server URL.
    msa_pairing_strategy : str
        The MSA pairing strategy.

    """
    if len(data) > 1 and use_pairing:
        paired_msas = run_mmseqs2(
            list(data.values()),
            msa_dir / f"{target_id}_paired_tmp",
            use_env=True,
            use_pairing=True,
            host_url=msa_server_url,
            pairing_strategy=msa_pairing_strategy,
        )
    else:
        paired_msas = [""] * len(data)

    unpaired_msa = run_mmseqs2(
        list(data.values()),
        msa_dir / f"{target_id}_unpaired_tmp",
        use_env=True,
        use_pairing=False,
        host_url=msa_server_url,
        pairing_strategy=msa_pairing_strategy,
    )

    for idx, name in enumerate(data):
        # Get paired sequences
        paired = paired_msas[idx].strip().splitlines()
        paired = paired[1::2]  # ignore headers
        paired = paired[: const.max_paired_seqs]

        # Set key per row and remove empty sequences
        keys = [idx for idx, s in enumerate(paired) if s != "-" * len(s)]
        paired = [s for s in paired if s != "-" * len(s)]

        # Combine paired-unpaired sequences
        unpaired = unpaired_msa[idx].strip().splitlines()
        ### save unpaired sequences to a3m format
        a3m_msa_path = msa_dir / f"{name}_unpaired.a3m"
        with a3m_msa_path.open("w") as f:
            f.write(unpaired_msa[idx])
        unpaired = unpaired[1::2]
        unpaired = unpaired[: (const.max_msa_seqs - len(paired))]
        
        if paired:
            unpaired = unpaired[1:]  # ignore query is already present

        # Combine
        seqs = paired + unpaired
        keys = keys + [-1] * len(unpaired)

        # Dump MSA
        csv_str = ["key,sequence"] + [f"{key},{seq}" for key, seq in zip(keys, seqs)]

        msa_path = msa_dir / f"{name}.csv"
        with msa_path.open("w") as f:
            f.write("\n".join(csv_str))
            
        ## run templates search for hmmsearch.a3m
        if use_template:
            if generate_template[name]:
                hmmsearch_a3m_path = msa_dir / f"{name}_hmmsearch.a3m"
                run_template_search(
                    msa_a3m_path_for_template_search = str(a3m_msa_path),
                    hmmsearch_a3m_save_path = str(hmmsearch_a3m_path)
                )


def parse_m8(
    m8_result_path: str,
    processed_simirity_sequence_dir: Path,
    pdb_groups_json_path: Path,
) -> None:
    import pandas as pd
    import json
    df_m8 = pd.read_csv(
        m8_result_path,
        sep='\t', 
        names=['query','target','target_sequence','evalue','fident','alnlen','mismatch','qcov','tcov']
        )
    
    groups = json.load(open(pdb_groups_json_path))
    # Use list comprehension for efficiency and clarity
    targets = [','.join(groups.get(row['target'], [])) for _, row in df_m8.iterrows()]
    df_m8['target'] = targets
    
    ## unique query
    unique_queries = df_m8['query'].unique()
    for query in unique_queries:
        ### query: input_id-chain_id
        chain_id = query.split('-')[-1]
        input_name = query[:-len(f'-{chain_id}')]
        # Save top-100 similar sequences for each query to a CSV file
        df_ = df_m8[df_m8['query'] == query].reset_index(drop=True)[:100]
        output_dir = processed_simirity_sequence_dir / input_name
        output_path = output_dir / f'{query}.csv'
        output_dir.mkdir(parents=True, exist_ok=True)
        df_.to_csv(output_path, index=False)
        
        
def check_mmseqs2():
    """Check if mmseqs2 is installed and available in the PATH."""
    if shutil.which("mmseqs") is None:
        msg = "MMSeqs2 is not installed or not available in the PATH. Please install MMSeqs2 manually."
        msg += "\nYou can install it using conda:\n"
        msg += "conda install -c conda-forge -c bioconda mmseqs2\n"
        msg += "Or visit https://github.com/soedinglab/MMseqs2\n"
        msg += "Or just rerun the inference script without `--return_similar_seq` flag."
        raise RuntimeError(msg)
    else:
        logger.info("MMSeqs2 is available.")
        
def compute_similar_sequence(
    out_dir: Path,
    processed_polymer_fasta_dir: Path,
    cache_dir: Path,
) -> None:
    
    protein_path = processed_polymer_fasta_dir / "protein.fasta"
    nucleotide_path = processed_polymer_fasta_dir / "nucleotide.fasta"
    
    #### DataBase(Training PDB Sequence)
    protein_pdb_db_path = cache_dir / "unique_protein_sequences.fasta"
    nucleotide_pdb_db_path = cache_dir / "unique_nucleic_acid_sequences.fasta"
    protein_pdb_groups = cache_dir / "protein_id_groups.json"
    nucleotide_pdb_groups = cache_dir / "nucleic_acid_id_groups.json"
    
    processed_simirity_sequence_dir =  out_dir / "similar_sequences"
    processed_simirity_sequence_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = f'{processed_simirity_sequence_dir}/tmp'
    
    if protein_path.exists():
        cmd = ['mmseqs', 
               'easy-search', 
               f'{protein_path}',  
               f'{protein_pdb_db_path}', 
               f'{processed_simirity_sequence_dir}/protein_results.m8', 
               f'{tmp_path}', 
               f'--threads', '16', 
               '--dbtype', '0', 
               '--format-output', 'query,target,tseq,evalue,fident,alnlen,mismatch,qcov,tcov']
        result = subprocess.run(cmd, capture_output=True, text=True) 
        
        if os.path.exists(f'{processed_simirity_sequence_dir}/protein_results.m8'): 
            parse_m8(
                m8_result_path=f'{processed_simirity_sequence_dir}/protein_results.m8',
                processed_simirity_sequence_dir=processed_simirity_sequence_dir,
                pdb_groups_json_path=protein_pdb_groups)    
            
    if nucleotide_path.exists():
        cmd = ['mmseqs', 
               'easy-search', 
               f'{nucleotide_path}',  
               f'{nucleotide_pdb_db_path}', 
               f'{processed_simirity_sequence_dir}/nucleotide_results.m8', 
               f'{tmp_path}', 
               f'--threads', '16', 
               '--dbtype', '2', 
               '--search-type', '3', 
               '--format-output', 'query,target,tseq,evalue,fident,alnlen,mismatch,qcov,tcov']
        result = subprocess.run(cmd, capture_output=True, text=True) 
        
        if os.path.exists(f'{processed_simirity_sequence_dir}/nucleotide_results.m8'): 
            parse_m8(
                    m8_result_path=f'{processed_simirity_sequence_dir}/nucleotide_results.m8',
                    processed_simirity_sequence_dir=processed_simirity_sequence_dir,
                    pdb_groups_json_path=nucleotide_pdb_groups)
        
    if os.path.exists(f'{processed_simirity_sequence_dir}/protein_results.m8') or os.path.exists(f'{processed_simirity_sequence_dir}/nucleotide_results.m8'):
        msg = "Similar sequences from Our Training PDB have been computed and saved."
        msg += f"Results are saved in {processed_simirity_sequence_dir}"
        logger.info(msg)
        
    if os.path.exists(tmp_path):
        import shutil
        shutil.rmtree(tmp_path)
        ## remove the m8 files
        if os.path.exists(f'{processed_simirity_sequence_dir}/protein_results.m8'):
            os.remove(f'{processed_simirity_sequence_dir}/protein_results.m8')
        if os.path.exists(f'{processed_simirity_sequence_dir}/nucleotide_results.m8'):
            os.remove(f'{processed_simirity_sequence_dir}/nucleotide_results.m8')
        

def process_inputs(  # noqa: C901, PLR0912, PLR0915
    args,
    data: list[Path],
    out_dir: Path,
    ccd_path: Path,
    msa_server_url: str,
    msa_pairing_strategy: str,
    max_msa_seqs: int = 4096,
    use_msa_server: bool = False,
    use_pairing: bool = True,
    use_template: bool = False,
) -> None:
    """Process the input data and output directory.

    Parameters
    ----------
    data : list[Path]
        The input data.
    out_dir : Path
        The output directory.
    ccd_path : Path
        The path to the CCD dictionary.
    max_msa_seqs : int, optional
        Max number of MSA sequences, by default 4096.
    use_msa_server : bool, optional
        Whether to use the MMSeqs2 server for MSA generation, by default False.
    use_template : bool, optional
        Whether to use Protein templates for prediction, by default False.

    Returns
    -------
    BoltzProcessedInput
        The processed input data.

    """
    logger.info("Processing input data.")
    existing_records = None

    # Check if manifest exists at output path
    manifest_path = out_dir / "processed" / "manifest.json"
    if manifest_path.exists():
        logger.info(
            f"Found a manifest file at output directory: {out_dir}"
        )

        manifest: Manifest = Manifest.load(manifest_path)
        input_ids = [d.stem for d in data]
        existing_records = [
            record for record in manifest.records if record.id in input_ids
        ]
        processed_ids = [record.id for record in existing_records]

        # Check how many examples need to be processed
        missing = len(input_ids) - len(processed_ids)
        if not missing:
            logger.info("All examples in data are processed. Updating the manifest")
            # Dump updated manifest
            updated_manifest = Manifest(existing_records)
            updated_manifest.dump(out_dir / "processed" / "manifest.json")
            return

        logger.info(f"{missing} missing ids. Preprocessing these ids")
        missing_ids = list(set(input_ids).difference(set(processed_ids)))
        data = [d for d in data if d.stem in missing_ids]
        assert len(data) == len(missing_ids)

    # Create output directories
    msa_dir = out_dir / "msa"
    structure_dir = out_dir / "processed" / "structures"
    processed_msa_dir = out_dir / "processed" / "msa"
    processed_template_dir = out_dir / "processed" / "templates"
    processed_constraints_dir = out_dir / "processed" / "constraints"
    processed_polymer_fasta_dir = out_dir / "processed" / "fastas"
    predictions_dir = out_dir / "predictions"
    temp_dir = out_dir / "temp"

    out_dir.mkdir(parents=True, exist_ok=True)
    msa_dir.mkdir(parents=True, exist_ok=True)
    structure_dir.mkdir(parents=True, exist_ok=True)
    processed_msa_dir.mkdir(parents=True, exist_ok=True)
    processed_template_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    # processed_constraints_dir.mkdir(parents=True, exist_ok=True)   ### TODO: will be used in the future
    if args.return_similar_seq:
        check_mmseqs2()
        processed_polymer_fasta_dir.mkdir(parents=True, exist_ok=True)
    predictions_dir.mkdir(parents=True, exist_ok=True)

    # Load CCD
    with ccd_path.open("rb") as file:
        ccd = pickle.load(file)  # noqa: S301

    if existing_records is not None:
        logger.info(
            f"Found {len(existing_records)} records. Adding them to records"
        )

    # Parse input data
    records: list[Record] = existing_records if existing_records is not None else []
    protein_seqs = []
    nucleotide_seqs = []
    for path in tqdm(data, desc=f"Data Preprocessing"):
        try:
            # Parse data
            if path.suffix in (".yml", ".yaml"):
                target = parse_yaml(path, ccd)
            elif path.is_dir():
                msg = f"Found directory {path} instead of .yaml, skipping."
                raise RuntimeError(msg)
            else:
                msg = (
                    f"Unable to parse filetype {path.suffix}, "
                    "please provide a .yaml file."
                )
                raise RuntimeError(msg)

            # Get target id
            target_id = target.record.id

            #### save each polymer chain seqs
            if args.return_similar_seq:
                prot_id = const.chain_type_ids["PROTEIN"]
                rna_id = const.chain_type_ids["RNA"]
                dna_id = const.chain_type_ids["DNA"]
                exists_protein_entity_ids = []
                exists_nucleotide_entity_ids = []
                for chain in target.record.chains:
                    ### protein polymer
                    if (chain.mol_type == prot_id):
                        entity_id = chain.entity_id
                        if entity_id not in exists_protein_entity_ids:
                            protein_seqs.append(f'>{target_id}-{chain.chain_name}')
                            protein_seqs.append(f'{target.sequences[entity_id]}')
                            exists_protein_entity_ids.append(entity_id)
                    if chain.mol_type == rna_id or chain.mol_type == dna_id:
                        entity_id = chain.entity_id
                        if entity_id not in exists_nucleotide_entity_ids:
                            nucleotide_seqs.append(f'>{target_id}-{chain.chain_name}')
                            nucleotide_seqs.append(f'{target.sequences[entity_id]}')
                            exists_nucleotide_entity_ids.append(entity_id)            

            # Get all MSA ids and decide whether to generate MSA
            to_generate = {}
            generate_template = {}
            to_generate_template = {}
            prot_id = const.chain_type_ids["PROTEIN"]
            for chain in target.record.chains:
                # Add to generate list, assigning entity id
                # if (chain.mol_type == prot_id) and (chain.msa_id == 0):
                if chain.mol_type == prot_id:
                    ### MSA And template will only be generated for protein chains without MSA/template provided in the input yaml
                    if chain.msa_id == 0 and chain.template_id == 0:
                        entity_id = chain.entity_id
                        msa_id = f"{target_id}_{entity_id}"
                        to_generate[msa_id] = target.sequences[entity_id]
                        generate_template[msa_id] = False
                        chain.msa_id = msa_dir / f"{msa_id}.csv"
                        if use_template:
                            chain.template_id = msa_dir / f"{msa_id}_hmmsearch.a3m"
                            generate_template[msa_id] = True
                    ## If MSA provided but no template provided, will generate template based on the MSA if use_template is True
                    elif chain.msa_id != 0 and chain.template_id == 0:
                        if use_template:
                            msa_id = chain.msa_id
                            entity_id = chain.entity_id
                            template_id = temp_dir / f"{target_id}_{entity_id}_hmmsearch.a3m"
                            chain.template_id = template_id
                            to_generate_template[entity_id] = msa_id
                    ## If no MSA provided but template provided, we will only generate MSA, and use template provided in the input yaml
                    elif chain.msa_id == 0 and chain.template_id != 0:
                        entity_id = chain.entity_id
                        msa_id = f"{target_id}_{entity_id}"
                        to_generate[msa_id] = target.sequences[entity_id]
                        generate_template[msa_id] = False
                        chain.msa_id = msa_dir / f"{msa_id}.csv"
 
                # We do not support msa generation for non-protein chains
                elif chain.msa_id == 0:
                    chain.msa_id = -1
                    chain.template_id = -1

            # Generate MSA
            if to_generate and not use_msa_server:
                msg = "Missing MSA's in input and --use_msa_server flag not set."
                raise RuntimeError(msg)

            if to_generate:
                msg = f"Generating MSA for {path} with {len(to_generate)} protein entities."
                logger.info(msg)
                compute_msa(
                    data=to_generate,
                    generate_template=generate_template,
                    target_id=target_id,
                    msa_dir=msa_dir,
                    msa_server_url=msa_server_url,
                    msa_pairing_strategy=msa_pairing_strategy,
                    use_pairing=use_pairing,
                    use_template=use_template,
                )
                
            if to_generate_template and use_template:
                msg = f"Generating templates for {path} with {len(to_generate_template)} protein entities based on provided MSA."
                logger.info(msg)
                for entity_id, msa_id in to_generate_template.items():
                    msa_a3m_path_for_template_search = msa_id
                    temp_msa_a3m_path_for_template_search = temp_dir / f"{target_id}_{entity_id}_for_template_search.a3m"
                    reother_msa(input_msa_path=msa_a3m_path_for_template_search, output_msa_path=temp_msa_a3m_path_for_template_search)
                    hmmsearch_a3m_save_path = temp_dir / f"{target_id}_{entity_id}_hmmsearch.a3m"
                    run_template_search(
                        msa_a3m_path_for_template_search=str(temp_msa_a3m_path_for_template_search),
                        hmmsearch_a3m_save_path=str(hmmsearch_a3m_save_path)
                    )
            # Parse MSA data
            msas = sorted({c.msa_id for c in target.record.chains if c.msa_id != -1})
            templates = sorted({c.template_id for c in target.record.chains if c.template_id != -1})
            msa_id_map = {}
            for msa_idx, msa_id in enumerate(msas):
                # Check that raw MSA exists
                msa_path = Path(msa_id)
                if not msa_path.exists():
                    msg = f"MSA file {msa_path} not found."
                    raise FileNotFoundError(msg)

                # Dump processed MSA
                processed = processed_msa_dir / f"{target_id}_{msa_idx}.npz"
                msa_id_map[msa_id] = f"{target_id}_{msa_idx}"
                if not processed.exists():
                    # Parse A3M
                    if msa_path.suffix == ".a3m":
                        msa: MSA = parse_a3m(
                            msa_path,
                            taxonomy=None,
                            max_seqs=max_msa_seqs,
                        )
                    elif msa_path.suffix == ".csv":
                        msa: MSA = parse_csv(msa_path, max_seqs=max_msa_seqs)
                    else:
                        msg = f"MSA file {msa_path} not supported, only a3m or csv."
                        raise RuntimeError(msg)

                    msa.dump(processed)
                ## move the hmmsearch a3m to processed msa dir for template search
                if use_template:
                    template_id = templates[msa_idx]
                    template_path = Path(template_id)
                    template_idx = msa_idx
                    processed = processed_template_dir / f"{target_id}_{template_idx}_hmmsearch.a3m"
                    shutil.copy(template_path, processed)
            # Modify records to point to processed MSA
            for c in target.record.chains:
                if (c.msa_id != -1) and (c.msa_id in msa_id_map):
                    c.msa_id = msa_id_map[c.msa_id]
                    if use_template and c.template_id != -1:
                        c.template_id = c.msa_id
            # Keep record
            records.append(target.record)

            # Dump structure
            struct_path = structure_dir / f"{target.record.id}.npz"
            target.structure.dump(struct_path)

            # # Dump constraints
            # constraints_path = processed_constraints_dir / f"{target.record.id}.npz"
            # target.residue_constraints.dump(constraints_path)

        except Exception as e:
            if len(data) > 1:
                logger.warning(
                    f"Failed to process {path}. Skipping. Error: {e}."
                )
            else:
                raise e

    # Dump manifest
    manifest = Manifest(records)
    manifest.dump(out_dir / "processed" / "manifest.json")
    
    # remove the temporary directory
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        
    if args.return_similar_seq:
        if len(protein_seqs) > 0:
            output_path = processed_polymer_fasta_dir / "protein.fasta"
            with output_path.open("w") as f:
                f.write('\n'.join(protein_seqs))
        if len(nucleotide_seqs) > 0:
            output_path = processed_polymer_fasta_dir / "nucleotide.fasta"
            with output_path.open("w") as f:
                f.write('\n'.join(nucleotide_seqs))
                
                
def reother_msa(input_msa_path, output_msa_path):
    """
    Reorder the MSA file to put Uniref sequences at the top, which can help the template search to find better templates.
    Parameters    ----------
    input_msa_path : str
        The path to the input MSA file, which can be in a3m or csv format.
    output_msa_path : str
        The path to the output MSA file, which will be in a3m format.
    """
    if not (input_msa_path.endswith(".a3m") or input_msa_path.endswith(".csv")):
        raise AssertionError(
            f"input msa {input_msa_path} should be in a3m or csv format"
        )
    
    if input_msa_path.endswith(".a3m"):
        with open(input_msa_path, "r") as f:
            msa_a3m = f.read().strip()
        ## extract Uniref MSA from the a3m file, which is in the format of >seq_id\nsequence\n
        msa_lines = msa_a3m.split("\n")
        uniref_msa_lines = []
        other_msa_lines = []
        uniref_msa_lines.append(msa_lines[0])  # add the query sequence at the top
        uniref_msa_lines.append(msa_lines[1])
        for i in range(2, len(msa_lines), 2):
            desc = msa_lines[i]
            seq = msa_lines[i+1]
            if desc.lower().startswith(">uniref"):
                uniref_msa_lines.append(desc)
                uniref_msa_lines.append(seq)
            else:
                other_msa_lines.append(desc)
                other_msa_lines.append(seq)
        msa_a3m = "\n".join(uniref_msa_lines + other_msa_lines)
    else:
        msa_df = pd.read_csv(input_msa_path)
        msa_df = msa_df[msa_df['key'] == -1]
        msa_lines = []
        index = 0
        for _, row in enumerate(msa_df.iterrows()):
            sequence = row['sequence']
            msa_lines.append(f">{index}")
            msa_lines.append(sequence)
            index += 1
        msa_a3m = "\n".join(msa_lines)
            
    msa_a3m = msa_a3m.strip()
    with open(output_msa_path, "w") as f:
        f.write(msa_a3m)
        