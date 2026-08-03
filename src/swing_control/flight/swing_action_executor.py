"""Execute validated Swing actions with pyparrot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from swing_control.logging_utils import JsonlRunLogger
from swing_control.safety.action_validator import validate_action_sequence


SwingFactory = Callable[[str], Any]


@dataclass
class ExecutionResult:
    ok: bool
    executed_tools: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    log_path: str | None = None


class SwingActionExecutor:
    """Run a validated action sequence on a Parrot Swing."""

    def __init__(
        self,
        addr: str,
        *,
        retries: int = 3,
        swing_factory: SwingFactory | None = None,
        auto_land_on_error: bool = True,
        logger: JsonlRunLogger | None = None,
    ) -> None:
        self.addr = addr
        self.retries = retries
        self.swing_factory = swing_factory or self._default_swing_factory
        self.auto_land_on_error = auto_land_on_error
        self.logger = logger
        self.swing: Any | None = None
        self.airborne = False

    @staticmethod
    def _default_swing_factory(addr: str) -> Any:
        from pyparrot.Minidrone import Swing

        return Swing(addr)

    def connect(self) -> bool:
        self.swing = self.swing_factory(self.addr)
        print("trying to connect")
        self._log("connect_start", addr=self.addr, retries=self.retries)
        success = self.swing.connect(num_retries=self.retries)
        print(f"connected: {success}")
        self._log("connect_result", success=bool(success))
        return bool(success)

    def disconnect(self) -> None:
        if self.swing is None:
            return
        print("disconnect")
        self._log("disconnect_start")
        self.swing.disconnect()
        self._log("disconnect_done")
        self.swing = None

    def execute(self, actions: list[dict[str, Any]], *, validate: bool = True) -> ExecutionResult:
        """Validate, connect, execute, and disconnect."""
        self._log("execution_requested", actions=actions, validate=validate)
        if validate:
            validation = validate_action_sequence(actions)
            self._log("validation_result", result=validation)
            if not validation.ok:
                return ExecutionResult(False, errors=validation.errors, log_path=self._log_path())

        result = ExecutionResult(ok=False, log_path=self._log_path())
        connected = False

        try:
            connected = self.connect()
            if not connected:
                result.errors.append("无人机连接失败")
                self._log("execution_failed", errors=result.errors)
                return result

            for action in actions:
                tool = action["tool"]
                if tool == "error":
                    result.errors.append(action.get("parameters", {}).get("message", "动作序列包含 error"))
                    self._log("execution_failed", errors=result.errors)
                    return result

                self._log("action_start", tool=tool, parameters=action.get("parameters", {}))
                self.execute_action(action)
                result.executed_tools.append(tool)
                self._log("action_done", tool=tool)

            result.ok = True
            self._log("execution_done", executed_tools=result.executed_tools)
            return result

        except Exception as exc:
            result.errors.append(f"执行失败: {type(exc).__name__}: {exc}")
            self._log("execution_exception", error=result.errors[-1], airborne=self.airborne)
            if self.auto_land_on_error and self.airborne and self.swing is not None:
                try:
                    print("执行异常，尝试安全降落")
                    self._log("auto_land_start")
                    self.swing.safe_land(5)
                    self.airborne = False
                    result.executed_tools.append("auto_land_on_error")
                    self._log("auto_land_done")
                except Exception as land_exc:
                    result.errors.append(f"异常降落失败: {type(land_exc).__name__}: {land_exc}")
                    self._log("auto_land_failed", error=result.errors[-1])
            return result

        finally:
            if connected:
                self.disconnect()

    def execute_action(self, action: dict[str, Any]) -> None:
        """Execute one already validated action."""
        if self.swing is None:
            raise RuntimeError("Swing is not connected")

        tool = action["tool"]
        params = action.get("parameters", {})

        if tool == "pre_flight_check":
            print("执行: 起飞前检查")
            self.swing.ask_for_state_update()
            self.swing.smart_sleep(1)
            return

        if tool == "get_status":
            print("执行: 获取状态")
            self.swing.ask_for_state_update()
            self.swing.smart_sleep(1)
            return

        if tool == "takeoff":
            duration = _float(params, "duration_s")
            print(f"执行: 安全起飞 {duration:g}s")
            self.swing.safe_takeoff(duration)
            self.airborne = True
            return

        if tool == "land":
            duration = _float(params, "duration_s")
            print(f"执行: 安全降落 {duration:g}s")
            self.swing.safe_land(duration)
            self.airborne = False
            return

        if tool == "hover":
            duration = _float(params, "duration_s")
            print(f"执行: 悬停 {duration:g}s")
            self.swing.smart_sleep(duration)
            return

        if tool in {"fly_forward", "fly_backward", "fly_left", "fly_right"}:
            duration = _float(params, "duration_s")
            speed = _float(params, "speed")
            roll, pitch = _roll_pitch_for_motion(tool, speed)
            print(f"执行: {tool} duration={duration:g}, speed={speed:g}")
            self.swing.fly_direct(
                roll=roll,
                pitch=pitch,
                yaw=0,
                vertical_movement=0,
                duration=duration,
            )
            self.swing.smart_sleep(0.2)
            return

        if tool in {"turn_left", "turn_right"}:
            duration = _float(params, "duration_s")
            yaw = _float(params, "yaw")
            signed_yaw = -yaw if tool == "turn_left" else yaw
            print(f"执行: {tool} duration={duration:g}, yaw={yaw:g}")
            self.swing.fly_direct(
                roll=0,
                pitch=0,
                yaw=signed_yaw,
                vertical_movement=0,
                duration=duration,
            )
            self.swing.smart_sleep(0.2)
            return

        if tool in {"fly_up", "fly_down"}:
            duration = _float(params, "duration_s")
            vertical = _float(params, "vertical_movement")
            signed_vertical = vertical if tool == "fly_up" else -vertical
            print(f"执行: {tool} duration={duration:g}, vertical={vertical:g}")
            self.swing.fly_direct(
                roll=0,
                pitch=0,
                yaw=0,
                vertical_movement=signed_vertical,
                duration=duration,
            )
            self.swing.smart_sleep(0.2)
            return

        if tool == "switch_plane_forward":
            print("执行: 切换到固定翼前飞模式")
            self.swing.set_flying_mode("plane_forward")
            self.swing.smart_sleep(1)
            return

        if tool == "switch_quadricopter":
            print("执行: 切换到四旋翼模式")
            self.swing.set_flying_mode("quadricopter")
            self.swing.smart_sleep(1)
            return

        raise ValueError(f"unsupported action tool: {tool}")

    def _log(self, event: str, **fields: Any) -> None:
        if self.logger is not None:
            self.logger.log(event, **fields)

    def _log_path(self) -> str | None:
        if self.logger is None:
            return None
        return str(self.logger.path)


def _float(params: dict[str, Any], name: str) -> float:
    return float(params[name])


def _roll_pitch_for_motion(tool: str, speed: float) -> tuple[float, float]:
    if tool == "fly_forward":
        return 0.0, speed
    if tool == "fly_backward":
        return 0.0, -speed
    if tool == "fly_left":
        return -speed, 0.0
    if tool == "fly_right":
        return speed, 0.0
    raise ValueError(f"unsupported motion tool: {tool}")
