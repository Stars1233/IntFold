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

from collections.abc import Mapping


def realign_hit_to_structure(
    *,
    hit_sequence: str,
    hit_start_index: int,
    hit_end_index: int,
    full_length: int,
    structure_sequence: str,
    query_to_hit_mapping: Mapping[int, int],
) -> Mapping[int, int]:
    """Realigns the hit sequence to the Structure sequence.

    Args:
      hit_sequence: Subsequence of the full seqres hit sequence, without gaps.
      hit_start_index: Inclusive start index of hit_sequence in the full seqres.
      hit_end_index: Exclusive end index of hit_sequence in the full seqres.
      full_length: Length of the full seqres sequence.
      structure_sequence: Sequence actually observed in the structure.
      query_to_hit_mapping: Mapping from query index to hit_sequence index.

    Returns:
      Mapping from query index to structure_sequence index.

    Raises:
      AlignmentError: if the input lengths are inconsistent.
    """
    if len(structure_sequence) > full_length:
        raise ValueError(
            "Invalid sequence lengths for remapping: "
            f"structure length={len(structure_sequence)} exceeds "
            f"full template length={full_length}.\n"
            f"structure_sequence={structure_sequence}\n"
            f"hit_sequence={hit_sequence}"
        )

    expected_hit_len = hit_end_index - hit_start_index
    if len(hit_sequence) != expected_hit_len:
        raise ValueError(
            "Inconsistent hit span: "
            f"hit_end_index - hit_start_index = {expected_hit_len}, "
            f"but len(hit_sequence) = {len(hit_sequence)}."
        )

    total_missing = full_length - len(structure_sequence)

    max_prefix_missing = min(hit_start_index, total_missing)

    best_score = None
    best_prefix_missing = 0
    best_local_mapping: dict[int, int] = {}

    for prefix_missing in range(max_prefix_missing + 1):
        structure_subseq_start = hit_start_index - prefix_missing
        structure_subseq_end = hit_end_index - prefix_missing
        structure_subseq = structure_sequence[structure_subseq_start:structure_subseq_end]

        local_hit_to_structure, score = _build_hit_to_structure_index_map(
            hit_seq=hit_sequence,
            structure_subseq=structure_subseq,
            max_skips=total_missing - prefix_missing,
        )

        remapped_query = {}
        for query_idx, hit_idx in query_to_hit_mapping.items():
            structure_local_idx = local_hit_to_structure.get(hit_idx)
            if structure_local_idx is not None:
                remapped_query[query_idx] = structure_local_idx

        if best_score is None or score >= best_score:
            best_score = score
            best_prefix_missing = prefix_missing
            best_local_mapping = remapped_query

    structure_offset = hit_start_index - best_prefix_missing
    return {q: s + structure_offset for q, s in best_local_mapping.items()}


def _build_hit_to_structure_index_map(
    *,
    hit_seq: str,
    structure_subseq: str,
    max_skips: int,
) -> tuple[dict[int, int], int]:
    """Constructs hit_subseq_index -> structure_subseq_index mapping.

    This uses a simple greedy realignment:
    - walk through hit_seq and structure_subseq together
    - when residues mismatch, try skipping some residues in hit_seq
      (up to max_skips left) until the current structure residue can align
    - matched or not, once aligned, record the current pair and advance both

    Args:
      hit_seq: Hit subsequence from seqres.
      structure_subseq: Candidate aligned window from structure_sequence.
      max_skips: Maximum number of residues that may be skipped in hit_seq.

    Returns:
      (mapping, score)
        mapping: hit index -> structure index
        score: number of exact residue matches along the chosen alignment
    """
    hit_to_structure: dict[int, int] = {}
    score = 0

    hit_i = 0
    struc_i = 0
    skips_left = max_skips

    while hit_i < len(hit_seq) and struc_i < len(structure_subseq):
        if hit_seq[hit_i] != structure_subseq[struc_i]:
            shift = _find_next_alignable_hit_offset(
                hit_seq=hit_seq,
                hit_index=hit_i,
                target_residue=structure_subseq[struc_i],
                max_offset=skips_left,
            )
            hit_i += shift
            skips_left -= shift

            if hit_i >= len(hit_seq):
                break

        hit_to_structure[hit_i] = struc_i
        if hit_seq[hit_i] == structure_subseq[struc_i]:
            score += 1

        hit_i += 1
        struc_i += 1

    return hit_to_structure, score


def _find_next_alignable_hit_offset(
    *,
    hit_seq: str,
    hit_index: int,
    target_residue: str,
    max_offset: int,
) -> int:
    """Finds how many residues to skip in hit_seq so current residue can align.

    Returns the smallest offset in [0, max_offset] such that:
      hit_seq[hit_index + offset] == target_residue
    If none is found, returns 0.
    """
    upper = min(len(hit_seq) - hit_index - 1, max_offset)
    for offset in range(upper + 1):
        if hit_seq[hit_index + offset] == target_residue:
            return offset
    return 0