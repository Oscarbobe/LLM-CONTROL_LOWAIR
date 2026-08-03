"""Manual confirmation gate for actions that may move the drone."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


CONFIRM_PHRASE = "确认执行"
CANCEL_WORDS = {"q", "quit", "cancel", "取消", "不执行", "no", "n"}


@dataclass
class ConfirmationResult:
    confirmed: bool
    message: str


def build_confirmation_summary(step_descriptions: Iterable[str]) -> str:
    """Build a compact human-readable summary before execution."""
    lines = ["即将执行以下动作："]
    for index, description in enumerate(step_descriptions, start=1):
        lines.append(f"{index}. {description}")
    lines.append("")
    lines.append(f"如确认真机执行，请输入：{CONFIRM_PHRASE}")
    lines.append("取消请输入：q")
    return "\n".join(lines)


def request_manual_confirmation(
    step_descriptions: Iterable[str],
    *,
    input_func=input,
    output_func=print,
) -> ConfirmationResult:
    """Ask the user to explicitly confirm before real drone execution."""
    output_func(build_confirmation_summary(step_descriptions))
    answer = input_func("> ").strip()

    if answer == CONFIRM_PHRASE:
        return ConfirmationResult(True, "用户已确认执行")

    if answer.lower() in CANCEL_WORDS:
        return ConfirmationResult(False, "用户取消执行")

    return ConfirmationResult(False, f"确认文本不匹配，已拒绝执行：{answer}")

