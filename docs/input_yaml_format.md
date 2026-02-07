## YAML format(Recommended)

The YAML format is more flexible and allows for more complex inputs, particularly around covalent bonds. The schema of the YAML is the following:

```yaml
sequences:
    - ENTITY_TYPE:
        id: CHAIN_ID 
        sequence: SEQUENCE    # only for protein, dna, rna
        smiles: 'SMILES'        # only for ligand, exclusive with ccd
        ccd: CCD              # only for ligand, exclusive with smiles
        msa: MSA_PATH         # only for protein
        modifications:
          - position: RES_IDX   # index of residue, starting from 1
            ccd: CCD            # CCD code of the modified residue

    - ENTITY_TYPE:
        id: [CHAIN_ID, CHAIN_ID]    # multiple ids in case of multiple identical entities
        ...

```
`sequences` has one entry for every unique chain/molecule in the input. Each polymer entity as a `ENTITY_TYPE`  either `protein`, `dna` or `rna` and have a `sequence` attribute. Non-polymer entities are indicated by `ENTITY_TYPE` equal to `ligand` and have a `smiles` or `ccd` attribute. `CHAIN_ID` is the unique identifier for each chain/molecule, and it should be set as a list in case of multiple identical entities in the structure. For proteins, the `msa` key is required by default but can be omited by passing the `--use_msa_server` flag which will auto-generate the MSA using the mmseqs2 server. If you wish to use a precomputed MSA, use the `msa` attribute with `MSA_PATH` indicating the path to the `.a3m` file containing the MSA for that protein. If you wish to explicitly run single sequence mode (which is generally advised against as it will hurt model performance), you may do so by using the special keyword `empty` for that protein (ex: `msa: empty`). For custom MSA, you may wish to indicate pairing keys to the model. You can do so by using a CSV format instead of a3m with two columns: `sequence` with the protein sequences and `key` which is a unique identifier indicating matching rows across CSV files of each protein chain.

The `modifications` field is an optional field that allows you to specify modified residues in the polymer (`protein`, `dna` or`rna`). The `position` field specifies the index (starting from 1) of the residue, and `ccd` is the CCD code of the modified residue. This field is currently only supported for CCD ligands. 

> **Note**: Although our model supports the template feature, this repository does not currently provide template support due to the design of the inference data pipeline (adapted from [Boltz-1](https://github.com/jwohlwend/boltz)). **As a result, predictions are generated without template inputs, which may lead to a slight drop in performance—especially for targets with strong available templates.**


As an example:

```yaml
version: 1
sequences:
  - protein:
      id: [A, B]
      sequence: MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPADSGELARRLDCDARAMRVLLDALYAYDVIDRIHDTNGFRYLLSAEARECLLPGTLFSLVGKFMHDINVAWPAWRNLAEVVRHGARDTSGAESPNGIAQEDYESLVGGINFWAPPIVTTLSRKLRASGRSGDATASVLDVGCGTGLYSQLLLREFPRWTATGLDVERIATLANAQALRLGVEERFATRAGDFWRGGWGTGYDLVLFANIFHLQTPASAVRLMRHAAACLAPDGLVAVVDQIVDADREPKTPQDRFALLFAASMTNTGGGDAYTFQEYEEWFTAAGLQRIETLDTPMHRILLARRATEPSAVPEGQASENLYFQ
      msa: ./examples/msa/seq1.a3m
  - ligand:
      id: [C, D]
      ccd: SAH
  - ligand:
      id: [E, F]
      smiles: 'N[C@@H](Cc1ccc(O)cc1)C(=O)O'
```


## Fasta format

The fasta format is a little simpler, and should contain entries as follows:

```
>CHAIN_ID|ENTITY_TYPE|MSA_PATH
SEQUENCE
```

The `CHAIN_ID` is a unique identifier for each input chain. The `ENTITY_TYPE` can be one of `protein`, `dna`, `rna`, `smiles`, `ccd` (note that we support both smiles and CCD code for ligands). The `MSA_PATH` is only applicable to proteins. By default, MSA's are required, but they can be omited by passing the `--use_msa_server` flag which will auto-generate the MSA using the mmseqs2 server. If you wish to use a custom MSA, use it to set the path to the `.a3m` file containing a pre-computed MSA for this protein. If you wish to explicitly run single sequence mode (which is generally advised against as it will hurt model performance), you may do so by using the special keyword `empty` for that protein (ex: `>A|protein|empty`). For custom MSA, you may wish to indicate pairing keys to the model. You can do so by using a CSV format instead of a3m with two columns: `sequence` with the protein sequences and `key` which is a unique identifier indicating matching rows across CSV files of each protein chain.

For each of these cases, the corresponding `SEQUENCE` will contain an amino acid sequence (e.g. `EFKEAFSLF`), a sequence of nucleotide bases (e.g. `ATCG`), a smiles string (e.g. `CC1=CC=CC=C1`), or a CCD code (e.g. `ATP`), depending on the entity.

As an example:

```yaml
>A|protein|./examples/msa/seq1.a3m
MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPADSGELARRLDCDARAMRVLLDALYAYDVIDRIHDTNGFRYLLSAEARECLLPGTLFSLVGKFMHDINVAWPAWRNLAEVVRHGARDTSGAESPNGIAQEDYESLVGGINFWAPPIVTTLSRKLRASGRSGDATASVLDVGCGTGLYSQLLLREFPRWTATGLDVERIATLANAQALRLGVEERFATRAGDFWRGGWGTGYDLVLFANIFHLQTPASAVRLMRHAAACLAPDGLVAVVDQIVDADREPKTPQDRFALLFAASMTNTGGGDAYTFQEYEEWFTAAGLQRIETLDTPMHRILLARRATEPSAVPEGQASENLYFQ
>B|protein|./examples/msa/seq1.a3m
MVTPEGNVSLVDESLLVGVTDEDRAVRSAHQFYERLIGLWAPAVMEAAHELGVFAALAEAPADSGELARRLDCDARAMRVLLDALYAYDVIDRIHDTNGFRYLLSAEARECLLPGTLFSLVGKFMHDINVAWPAWRNLAEVVRHGARDTSGAESPNGIAQEDYESLVGGINFWAPPIVTTLSRKLRASGRSGDATASVLDVGCGTGLYSQLLLREFPRWTATGLDVERIATLANAQALRLGVEERFATRAGDFWRGGWGTGYDLVLFANIFHLQTPASAVRLMRHAAACLAPDGLVAVVDQIVDADREPKTPQDRFALLFAASMTNTGGGDAYTFQEYEEWFTAAGLQRIETLDTPMHRILLARRATEPSAVPEGQASENLYFQ
>C|ccd
SAH
>D|ccd
SAH
>E|smiles
N[C@@H](Cc1ccc(O)cc1)C(=O)O
>F|smiles
N[C@@H](Cc1ccc(O)cc1)C(=O)O
```



## Output format

After running the model, the generated outputs are organized into the output directory following the structure below:
```
out_dir/
├── predictions/                                               # Contains the model's predictions
    ├── [input_file1]/
        ├── [input_file1]_seed-[seed]-sample-[diffusion_samples-index].cif                          # The predicted structure in CIF/PDB format, with the inclusion of per token pLDDT scores
        ├── [input_file1]_seed-[seed]-sample-[diffusion_samples-index]_summary_confidences.json     # The summary confidence scores (chain_plddt, chain_pair_plddt, chain_iptm, chain_pair_iptm, chain_ptm, fraction_disordered, has_clash, plddt, iptm, ptm, ranking_score, num_recycles)
        ├── [input_file1]_seed-[seed]-sample-[diffusion_samples-index]_confidences.json             # The full token confidence scores (atom_chain_ids, atom_plddts, pae, token_chain_ids, token_res_ids)
        ...
        └── [input_file1]_seed-[seed]-sample-[diffusion_samples-index].cif                          # The predicted structure in CIF/PDB format
        ...
    └── [input_file2]/
        ...
├── errors/                                                   # Contains any errors encountered during execution
    ├── [input_file1].txt                                     # Error log for input_file1
    ├── [input_file2].txt                                     # Error log for input_file2
    ...
├── processed/                                                 # Processed data used during execution 
└── similar_sequences/                                           # Contains similar sequences found during inference
    ├── [input_file1]                  # Similar sequences for input_file1
        ├── [input_file1]-[chain_id].csv  # Similar sequences for chain_id in input_file1
        ├── [input_file1]-[chain_id2].csv # Similar sequences for another chain_id in input_file1
    ├── [input_file2]                  # Similar sequences for input_file2
        ├── [input_file2]-[chain_id].csv  # Similar sequences for chain_id in input_file2
        ...
    ...
```
The `predictions` folder contains a unique folder for each input file. The input folders contain `diffusion_samples` predictions saved in the output_format ordered by confidence score as well as additional files containing the predictions of the confidence model. The `processed` folder contains the processed input files that are used by the model during inference.

The contents of each output file are as follows:
- `[input_file1]_seed-[seed]-sample-*.cif` - A CIF format text file containing the predicted structure
- `[input_file1]_seed-[seed]-sample-*_summary_confidences.json` - A JSON format text file containing various confidence scores for assessing the reliability of predictions. Here’s a description of each score:

    - `chain_plddt` - pLDDT scores calculated for individual chains with the shape of [N_chains].
    - `chain_pair_plddt` - Pairwise pLDDT scores for chain pairs with the shape of [N_chains, N_chains].
    - `chain_iptm` - Average ipTM scores for each chain with the shape of [N_chains].
    - `chain_pair_iptm`: Pairwise interface pTM scores between chain pairs with the shape of [N_chains, N_chains], indicating the reliability of specific chain-chain interactions.
    - `chain_ptm` - pTM score calculated for individual chains with the shape of [N_chains], indicating the reliability of specific chain structure.
    - `fraction_disordered` - Predicted regions of intrinsic disorder within the protein, highlighting residues that may be flexible or unstructured.
    - `has_clash` - 0/1 Binary score indicating if there are steric clashes in the predicted structure.
    - `plddt` - Predicted Local Distance Difference Test (pLDDT) score. Higher values indicate greater confidence.
    - `iptm` - Interface Predicted TM-score, used to estimate the accuracy of interfaces between chains. Values closer to 1 indicate greater confidence.
    - `ptm` - Predicted TM-score (pTM). Values closer to 1 indicate greater confidence.
    - `ranking_score` - Predicted confidence score for ranking complexes. Higher values indicate greater confidence.
    - `num_recycles`: Number of recycling steps used during inference.

- `[input_file1]_seed-[seed]-sample-*_confidences.json` - A JSON format text file containing Atom pLDDT and PAE confidence scores for assessing the reliability of predictions. Here’s a description of each score:
    - `atom_chain_ids` - Chain IDs for each atom in the predicted structure with the shape of [N_atoms].
    - `atom_plddts` - Predicted Local Distance Difference Test (pLDDT) scores for each atom. Higher values indicate greater confidence, with the shape of [N_atoms].
    - `pae` - Predicted Alignment Error (PAE) scores for each atom, indicating the predicted distance error between pairs of residues, with the shape of [N_tokens, N_tokens].
    - `token_chain_ids` - Chain IDs for each token in the predicted structure, with the shape of [N_tokens].
    - `token_res_ids` - Residue IDs for each token in the predicted structure, with the shape of [N_tokens].

The `similar_sequences` folder contains CSV files with similar sequences(The Top-100 evalues) found during inference. Each input file has its own subfolder, and within that subfolder, there are CSV files for each chain ID in the input file. The naming convention for these files is as follows:
- `[input_file1]` - The name of the input yaml file
- `[chain_id]` - The chain ID of the sequence in the input file
- `[input_file1]-[chain_id].csv` - A CSV file containing similar sequences found during inference for the chain with `chain_id` in `input_file1`. The CSV contains columns `query`, `target`, `target_sequence`, `evalue`, `fident`, `alnlen`, `mismatch`, `qcov`, and `tcov`. Here’s a description of each column:
    - `query` - The query identifier, which is the chain ID of the input file.
    - `target` - The target identifier, which is the pdbid-chain ID of the similar sequence found in the training dataset.
    - `target_sequence` - The sequence of the target.
    - `evalue` - The e-value of the alignment, lower values indicate more significant alignments.
    - `fident` - The fraction of identical residues in the alignment.
    - `alnlen` - The length of the alignment.
    - `mismatch` - The number of mismatches in the alignment.
    - `qcov` - The coverage of the query sequence in the alignment.
    - `tcov` - The coverage of the target sequence in the alignment.


