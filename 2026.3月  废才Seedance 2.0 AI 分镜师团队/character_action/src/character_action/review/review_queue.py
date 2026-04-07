from __future__ import annotations

from ..ids import build_review_task_id
from ..models import CharacterRecord, ReviewTaskRecord


def build_review_tasks(
    run_id: str,
    characters: list[CharacterRecord],
    ambiguous_aliases: list[dict[str, object]],
) -> list[ReviewTaskRecord]:
    tasks: list[ReviewTaskRecord] = []
    task_index = 1
    for character in characters:
        if character.confidence < 0.6:
            tasks.append(
                ReviewTaskRecord(
                    task_id=build_review_task_id(task_index),
                    run_id=run_id,
                    task_type="low_confidence_character",
                    target_id=character.character_id,
                    reason_codes=["LOW_CONFIDENCE"],
                    status="open",
                    review_patch={"suggested_canonical_name": character.canonical_name},
                )
            )
            task_index += 1
    for item in ambiguous_aliases:
        tasks.append(
            ReviewTaskRecord(
                task_id=build_review_task_id(task_index),
                run_id=run_id,
                task_type="ambiguous_alias_merge",
                target_id=str(item["alias"]),
                reason_codes=["AMBIGUOUS_ALIAS"],
                status="open",
                review_patch={"canonical_candidates": item["canonical_candidates"]},
            )
        )
        task_index += 1
    return tasks
