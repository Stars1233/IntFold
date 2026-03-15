set -e

# if HF_ENDPOINT is not set, use huggingface.co
if [ -z "$HF_ENDPOINT" ]; then
    HF_ENDPOINT="huggingface.co"
fi

# if cache_dir is not set, use "./cache_dir" by default
if [ -z "$cache_dir" ]; then
    cache_dir="./cache_data"
fi
mkdir -p "$cache_dir"

# if aria2 exists, use aria2 to download
if command -v aria2c &> /dev/null; then
    aria2c -c -x 10 -s 10 -k 1M -o $cache_dir/intellifold_v0.1.0.pt https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/intellifold_v0.1.0.pt
    aria2c -c -x 10 -s 10 -k 1M -o $cache_dir/intellifold_v2.pt https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/intellifold_v2.pt
    aria2c -c -x 10 -s 10 -k 1M -o $cache_dir/intellifold_v2_flash.pt https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/intellifold_v2_flash.pt
    aria2c -c -x 10 -s 10 -k 1M -o $cache_dir/ccd_v2.pkl https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/ccd_v2.pkl
    aria2c -c -x 10 -s 10 -k 1M -o $cache_dir/unique_protein_sequences.fasta https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/unique_protein_sequences.fasta
    aria2c -c -x 10 -s 10 -k 1M -o $cache_dir/unique_nucleic_acid_sequences.fasta https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/unique_nucleic_acid_sequences.fasta
    aria2c -c -x 10 -s 10 -k 1M -o $cache_dir/protein_id_groups.json https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/protein_id_groups.json
    aria2c -c -x 10 -s 10 -k 1M -o $cache_dir/nucleic_acid_id_groups.json https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/nucleic_acid_id_groups.json
    aria2c -c -x 10 -s 10 -k 1M -o $cache_dir/search_database/pdb_seqres_2022_09_28.fasta https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/pdb_seqres_2022_09_28.fasta
    
else
    wget -P $cache_dir https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/intellifold_v0.1.0.pt
    wget -P $cache_dir https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/intellifold_v2.pt
    wget -P $cache_dir https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/intellifold_v2_flash.pt
    wget -P $cache_dir https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/ccd_v2.pkl
    wget -P $cache_dir https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/unique_protein_sequences.fasta
    wget -P $cache_dir https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/unique_nucleic_acid_sequences.fasta
    wget -P $cache_dir https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/protein_id_groups.json
    wget -P $cache_dir https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/nucleic_acid_id_groups.json
    wget -P $cache_dir/search_database https://${HF_ENDPOINT}/intelligenAI/intellifold/resolve/main/pdb_seqres_2022_09_28.fasta
fi

