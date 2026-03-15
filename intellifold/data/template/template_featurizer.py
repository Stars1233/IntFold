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

import dataclasses
import time
from datetime import datetime, timedelta
from os.path import exists as opexists, join as opjoin
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np
from typing_extensions import Self, TypeAlias

from intellifold.data.const import (
    DNA_CHAIN,
    LIGAND_CHAIN_TYPES,
    PROTEIN_CHAIN,
    RNA_CHAIN,
)
from intellifold.data.template.template_parser import HHRParser, HmmsearchA3MParser
from intellifold.data.template.template_utils import (
    DAYS_BEFORE_QUERY_DATE,
    DistogramFeaturesConfig,
    TEMPLATE_FEATURES,
    TemplateFeatures,
    TemplateHitFeaturizer,
)

from intellifold.data.tools.logger import init_logging, get_logger
logger = get_logger(__name__)
init_logging()


BatchDict: TypeAlias = dict[str, np.ndarray]
FeatureDict: TypeAlias = Mapping[str, np.ndarray]


def map_to_standard(
    asym_ids: np.ndarray, res_ids: np.ndarray, meta: Mapping[int, Mapping[str, Any]]
) -> np.ndarray:
    """
    Maps residue indices to a standardized MSA coordinate system.

    Args:
        asym_ids: Array of asymmetric IDs.
        res_ids: Array of residue IDs.
        meta: Metadata dictionary containing chain info and sequences.

    Returns:
        Array of standardized indices.
    """
    uids = [f"{a}-{b}" for a, b in zip(asym_ids, res_ids)]
    std_uids = []
    for aid, info in meta.items():
        std_uids.extend([f"{aid}-{x}" for x in range(1, len(info["sequence"]) + 1)])

    lookup = {uid: i for i, uid in enumerate(std_uids)}
    return np.array(
        [lookup.get(u, lookup.get(f"{u.split('-')[0]}-1", -1)) for u in uids],
        dtype=np.int32,
    )
    
def pad_to(arr: np.ndarray, shape: tuple, **kwargs) -> np.ndarray:
    """Pads an array to a given shape. Wrapper around np.pad().

    Args:
      arr: numpy array to pad
      shape: target shape, use None for axes that should stay the same
      **kwargs: additional args for np.pad, e.g. constant_values=-1

    Returns:
      the padded array

    Raises:
      ValueError if arr and shape have a different number of axes.
    """
    if arr.ndim != len(shape):
        raise ValueError(
            f"arr and shape have different number of axes. {arr.shape=}, {shape=}"
        )

    num_pad = []
    for axis, width in enumerate(shape):
        if width is None:
            num_pad.append((0, 0))
        else:
            if width >= arr.shape[axis]:
                num_pad.append((0, width - arr.shape[axis]))
            else:
                raise ValueError(
                    f"Can not pad to a smaller shape. {arr.shape=}, {shape=}"
                )
    padded_arr = np.pad(arr, pad_width=num_pad, **kwargs)
    return padded_arr


class TemplateSourceManager:
    """
    Manages template data retrieval and loading from multiple sources.

    Args:
        raw_paths: List of base paths for template storage.
        indexing_methods: List of indexing methods (e.g., 'sequence' or 'pdb_id').
        mappings: Dictionary mapping source index to its respective lookup table.
        enabled: Whether template loading is enabled.
    """

    def __init__(
        self,
        raw_paths: Sequence[str],
        indexing_methods: Sequence[str],
        mappings: Dict[int, Dict[str, Any]],
        enabled: bool = True,
    ) -> None:
        self.raw_paths = raw_paths
        self.indexing_methods = indexing_methods
        self.mappings = mappings
        self.enabled = enabled

    def fetch_template_paths(
        self, pdb_id: str, query_sequence: str, chain_entity_type: str
    ) -> List[str]:
        """
        Fetches template file paths from the configured sources.

        Args:
            pdb_id: PDB identifier of the query.
            query_sequence: Query sequence.
            chain_entity_type: Type of the chain (e.g., PROTEIN_CHAIN).

        Returns:
            A list of paths to found template files (.a3m or .hhr).
        """
        if not self.enabled or chain_entity_type != PROTEIN_CHAIN:
            return []

        template_paths = []
        for i, (path, method) in enumerate(zip(self.raw_paths, self.indexing_methods)):
            mapping = self.mappings.get(i, {})
            key = pdb_id if method == "pdb_id" else query_sequence

            if key not in mapping:
                continue

            dir_path = opjoin(path, str(mapping[key]))
            # Check for multiple possible template filenames
            possible_subpaths = [
                "hmmsearch.a3m",
                "concat.hhr",
            ]
            for subpath in possible_subpaths:
                full_path = opjoin(dir_path, subpath)
                if opexists(full_path):
                    template_paths.append(full_path)
        return template_paths


class TemplateFeatureAssemblyLine:
    """
    Orchestrates the conversion of raw templates into finalized Protenix features.

    Args:
        max_templates: Maximum number of templates to include in the features.
    """

    def __init__(self, max_templates: int = 4) -> None:
        self.max_templates = max_templates

    def assemble(
        self,
        bioassembly: Mapping[int, Mapping[str, Any]],
        standard_token_idxs: np.ndarray,
    ) -> "Templates":
        """
        Executes the complete feature assembly pipeline.

        Args:
            bioassembly: Mapping of asymmetric IDs to chain information.
            standard_token_idxs: Array of standardized residue indices.

        Returns:
            An assembled Templates object.
        """
        np_chains_list = []
        polymer_entity_features = {True: {}, False: {}}
        # Identify entities where template features can be safely copied (same sequence)
        safe_entity_ids = get_safe_entity_id_for_template_copy(bioassembly)
        for asym_id, info in bioassembly.items():
            entity_id = info["entity_id"]
            chain_type = info["chain_entity_type"]
            num_tokens = len(info["sequence"])

            # Templates are currently only supported for protein chains with sufficient length
            skip_chain = chain_type != PROTEIN_CHAIN or num_tokens <= 4

            if (entity_id not in polymer_entity_features[skip_chain]) or (
                entity_id not in safe_entity_ids
            ):
                templates = info["templates"]
                if skip_chain or not templates:
                    template_features = TemplateFeatures.empty_template_features(
                        num_tokens
                    )
                else:
                    # Package and fix template features
                    template_features = TemplateFeatures.package_template_features(
                        hit_features=templates
                    )
                    template_features = TemplateFeatures.fix_template_features(
                        template_features=template_features,
                        num_res=num_tokens,
                    )
                # Reduce to requested maximum number of templates
                template_features = _reduce_template_features(
                    template_features, self.max_templates
                )
                if entity_id in safe_entity_ids:
                    polymer_entity_features[skip_chain][entity_id] = template_features

            if entity_id in safe_entity_ids:
                feats = polymer_entity_features[skip_chain][entity_id].copy()
            else:
                feats = template_features

            np_chains_list.append(feats)

        # Pad the number of templates to max_templates for each chain to allow concatenation
        for chain in np_chains_list:
            chain["template_aatype"] = pad_to(
                chain["template_aatype"], (self.max_templates, None)
            )
            chain["template_atom_positions"] = pad_to(
                chain["template_atom_positions"],
                (self.max_templates, None, None, None),
            )
            chain["template_atom_mask"] = pad_to(
                chain["template_atom_mask"], (self.max_templates, None, None)
            )

        # Concatenate features along the residue dimension
        merged_example = {
            ft: np.concatenate([c[ft] for c in np_chains_list], axis=1)
            for ft in np_chains_list[0]
            if ft in TEMPLATE_FEATURES
        }

        # Crop/index merged features using standard token indices
        for feature_name, v in merged_example.items():
            merged_example[feature_name] = v[
                : self.max_templates, standard_token_idxs, ...
            ]

        return Templates(
            aatype=merged_example["template_aatype"],
            atom_positions=merged_example["template_atom_positions"],
            atom_mask=merged_example["template_atom_mask"].astype(bool),
        )


@dataclasses.dataclass(frozen=True)
class Templates:
    """Dataclass containing template features."""

    # aatype: [num_templates, num_res]
    aatype: np.ndarray
    # atom_positions: [num_templates, num_res, 24, 3]
    atom_positions: np.ndarray
    # atom_mask: [num_templates, num_res, 24]
    atom_mask: np.ndarray

    @classmethod
    def from_data_dict(cls, batch: BatchDict) -> Self:
        """Construct instance from a data dictionary."""
        return cls(
            aatype=batch["template_aatype"],
            atom_positions=batch["template_atom_positions"],
            atom_mask=batch["template_atom_mask"],
        )

    def as_data_dict(self) -> BatchDict:
        """Convert to a standard data dictionary."""
        return {
            "template_aatype": self.aatype,
            "template_atom_positions": self.atom_positions,
            "template_atom_mask": self.atom_mask,
        }

    def as_dict(self) -> BatchDict:
        """Compute additional features and return a dictionary."""
        features = self.as_data_dict()
        dgrams, pb_masks = [], []
        unit_vectors, bb_masks = [], []

        num_templates = self.aatype.shape[0]
        for i in range(num_templates):
            aatype = self.aatype[i]
            mask = self.atom_mask[i]
            pos = self.atom_positions[i] * mask[..., None]

            # Compute pseudo-beta positions and mask
            pb_pos, pb_mask = TemplateFeatures.pseudo_beta_fn(aatype, pos, mask)
            pb_mask_2d = pb_mask[:, None] * pb_mask[None, :]

            # Compute distogram
            dgram = TemplateFeatures.dgram_from_positions(
                pb_pos,
                config=DistogramFeaturesConfig(
                    min_bin=3.25, max_bin=50.75, num_bins=39
                ),
            )
            dgrams.append(dgram * pb_mask_2d[..., None])
            # pb_masks.append(pb_mask_2d)
            pb_masks.append(pb_mask)   ## we using 1d mask for input

            # Compute normalized unit vectors between residues
            uv, bb_mask_2d, bb_mask = TemplateFeatures.compute_template_unit_vector(
                aatype, pos, mask
            )
            unit_vectors.append(uv * bb_mask_2d[..., None])
            # bb_masks.append(bb_mask_2d)
            bb_masks.append(bb_mask)   ## we using 1d mask for input

        features.update(
            {
                "template_pseudo_beta_mask": np.stack(pb_masks),
                "template_distogram": np.stack(dgrams),
                "template_unit_vector": np.stack(unit_vectors),
                "template_backbone_frame_mask": np.stack(bb_masks),
            }
        )
        return features


def _reduce_template_features(
    template_features: FeatureDict, max_templates: int
) -> FeatureDict:
    """Reduces templates to the requested maximum number."""
    num_t = template_features["template_aatype"].shape[0]
    keep_mask = np.arange(num_t) < max_templates
    fields = TEMPLATE_FEATURES + ("template_release_timestamp",)
    return {k: v[keep_mask] for k, v in template_features.items() if k in fields}


def get_safe_entity_id_for_template_copy(
    bioassembly: Mapping[int, Mapping[str, Any]],
) -> List[str]:
    """Identifies entity IDs that have consistent sequences across all chains."""
    eid_to_seqs = {}
    for aid, info in bioassembly.items():
        eid = info["entity_id"]
        seq = info["sequence"]
        eid_to_seqs.setdefault(eid, set()).add(seq)
    return [eid for eid, seqs in eid_to_seqs.items() if len(seqs) == 1]
