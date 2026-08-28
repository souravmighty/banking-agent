"""Sync and convert ADK evalset files into canonical EvaluationDataset format for agents-cli."""

import json
from pathlib import Path

from agentplatform._genai.types.common import EvaluationDataset


def convert_evalset_file(source_path: str) -> list[dict]:
    with open(source_path, encoding="utf-8") as f:
        adk_data = json.load(f)

    eval_cases = []
    set_name = adk_data.get("eval_set_id") or Path(source_path).stem
    raw_cases = adk_data.get("eval_cases", [])

    for idx, case in enumerate(raw_cases):
        eval_id = case.get("eval_id") or f"{set_name}_case_{idx + 1}"
        conversations = case.get("conversation", [])
        if not conversations:
            continue

        first_conv = conversations[0]
        user_content = first_conv.get("user_content", {})
        final_resp = first_conv.get("final_response", {})
        events = first_conv.get("intermediate_data", {}).get("invocation_events", [])

        turn_events = []
        turn_events.append({"author": "user", "content": user_content})
        for ev in events:
            turn_events.append(
                {"author": ev.get("author", "model"), "content": ev.get("content", {})}
            )
        turn_events.append({"author": "model", "content": final_resp})

        eval_case = {
            "eval_case_id": eval_id,
            "prompt": user_content,
            "responses": [{"response": final_resp}],
            "reference": {"response": final_resp},
            "agent_data": {"turns": [{"turn_index": 0, "events": turn_events}]},
        }
        eval_cases.append(eval_case)

    return eval_cases


def sync_all_golden_datasets():
    base_dir = Path(__file__).resolve().parent.parent.parent
    app_dir = base_dir / "app"
    datasets_dir = base_dir / "tests" / "eval" / "datasets"
    datasets_dir.mkdir(parents=True, exist_ok=True)

    all_cases = []
    evalset_files = list(app_dir.glob("*.evalset.json"))

    print(f"Found {len(evalset_files)} evalset file(s) in {app_dir}:")
    for file in sorted(evalset_files):
        cases = convert_evalset_file(str(file))
        if not cases:
            continue

        ds = EvaluationDataset.model_validate({"eval_cases": cases})
        dest_file = datasets_dir / f"{file.stem.replace('.evalset', '')}.json"

        with open(dest_file, "w", encoding="utf-8") as out:
            out.write(ds.model_dump_json(indent=2, exclude_none=True, by_alias=True))

        print(f"  ✓ {file.name} -> {dest_file.name} ({len(cases)} case(s))")
        all_cases.extend(cases)

    if all_cases:
        suite_ds = EvaluationDataset.model_validate({"eval_cases": all_cases})
        suite_path = datasets_dir / "golden_suite.json"
        with open(suite_path, "w", encoding="utf-8") as out:
            out.write(
                suite_ds.model_dump_json(indent=2, exclude_none=True, by_alias=True)
            )
        print(
            f"Created unified golden suite: {suite_path.name} with {len(all_cases)} total cases."
        )


if __name__ == "__main__":
    sync_all_golden_datasets()
