# Copyright 2026 IntelliGen-AI and/or its affiliates.
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

#######################################################################################################################
####### This is a demo script to run the IntelliFold prediction
#
#
# Arguments Summary (for 'intellifold pred' or 'run_intellifold.py'):
# * `--out_dir` (`PATH`, default: `./`)  
#   The path where to save the predictions.
# * `--cache` (`PATH`, default: `~/.intellifold`)  
#   The directory where to download the data and model. Will use environment variable `INTELLIFOLD_CACHE` as an absolute path if set.
# * `--num_workers` (`INTEGER`, default: `4`)  
#   The number of dataloader workers to use for prediction.
# * `--precision` (`str`, default: `bf16`)  
#   Sets precision, lower precision improves runtime.
# * `--seed` (`INTEGER`, default: `42`)  
#   Random seed (single int or multiple ints separated by comma, e.g., '42' or '42,43').
# * `--recycling_iters` (`INTEGER`, default: `10`)  
#   Number of recycling iterations.
# * `--num_diffusion_samples` (`INTEGER`, default: `5`)  
#   The number of diffusion samples.
# * `--sampling_steps` (`INTEGER`, default: `200`)  
#   The number of diffusion sampling steps to use.
# * `--output_format` (`[pdb,mmcif]`, default: `mmcif`)  
#   The output format to use for the predictions (pdb or mmcif).
# * `--override` (`FLAG`, default: `False`)  
#   Whether to override existing found predictions.
# * `--use_msa_server` (`FLAG`, default: `False`)  
#   Whether to use the MMSeqs2 server for MSA generation.
# * `--msa_server_url` (`str`, default: `https://api.colabfold.com`)  
#   MSA server url. Used only if `--use_msa_server` is set.
# * `--msa_pairing_strategy` (`str`, default: `complete`)  
#   Pairing strategy to use. Used only if `--use_msa_server` is set. Options are 'greedy' and 'complete'.
# * `--no_pairing` (`FLAG`, default: `False`)  
#   Whether to use pairing for Protein Multimer MSA generation.
# * `--use_template` (`FLAG`, default: `False`)  
#   Whether to use template information for prediction. If set, the model will use the template features in the input YAML file (if provided) or search for templates online (if `--use_msa_server` is set).
# * `--only_run_data_process` (`FLAG`, default: `False`)  
#   Whether to only run data processing, and not run the model.
# * `--return_similar_seq` (`FLAG`, default: `False`)
#   Whether to return sequences similar to those in the training PDB dataset during inference. You can use these similar sequences and its PDB ids to do further analysis, such as a reference structure.
#   > Before using this option, please make sure the mmseqs2 tool is installed, you can install it by running `conda install -c conda-forge -c bioconda mmseqs2`
# * `--model` (`[v1, v2, v2-flash]`, default: `v2-flash`)  
#   The model to use for prediction. Options are 'v1', 'v2', and 'v2-flash'. 'v2-flash' is the default and recommended model, which is faster and more accurate than 'v1' and 'v2'. 'v1' is the original model used in the IntelliFold paper, and 'v2' is an improved version of the model with better performance but slower inference speed than 'v2-flash'. You can choose the model based on your needs and computational resources.


#!/bin/bash
# export LAYERNORM_TYPE=fast_layernorm
# export USE_DEEPSPEED_EVO_ATTENTION=true
#### CUTLASS_PATH example
# export CUTLASS_PATH=.../path/to/cutlass


PYTHON_FILE=./run_intellifold.py


INPUT_DATA=./examples/5S8I_A.yaml
OUTPUT_DIR=./output
SEED=42
NUM_DIFFUSION_SAMPLES=5
CACHE_DATA_DIR=./cache_data

python $PYTHON_FILE \
$INPUT_DATA \
--seed $SEED \
--out_dir $OUTPUT_DIR \
--num_diffusion_samples $NUM_DIFFUSION_SAMPLES \
--cache $CACHE_DATA_DIR



# # The following is a demo to use Accelerate to run the script on a single machine with multiple GPUs.
# INPUT_DATA=./examples
# OUTPUT_DIR=./output
# SEED=42,66
# NUM_DIFFUSION_SAMPLES=5
# CACHE_DATA_DIR=./cache_data

# accelerate launch \
# --multi_gpu \
# --num_processes 2 \
# --num_machines 1 \
# --main_process_port 20472 \
# $PYTHON_FILE \
# $INPUT_DATA \
# --seed $SEED \
# --out_dir $OUTPUT_DIR \
# --num_diffusion_samples $NUM_DIFFUSION_SAMPLES \
# --cache $CACHE_DATA_DIR


# # The following is a demo to use Accelerate with Config file to run the script on a single machine with multiple GPUs.
# ## You can modify the config file to set the number of GPUs or number of Machines and other parameters.
# ACCELERATE_CONFIG_FILE=./accelerator_single_machine.json
# INPUT_DATA=./examples
# OUTPUT_DIR=./output
# SEED=42,66
# # SEED=42,66,88,101,2025
# NUM_DIFFUSION_SAMPLES=5
# CACHE_DATA_DIR=./cache_data

# accelerate launch \
# --config_file $ACCELERATE_CONFIG_FILE \
# $PYTHON_FILE \
# $INPUT_DATA \
# --seed $SEED \
# --out_dir $OUTPUT_DIR \
# --num_diffusion_samples $NUM_DIFFUSION_SAMPLES \
# --cache $CACHE_DATA_DIR


