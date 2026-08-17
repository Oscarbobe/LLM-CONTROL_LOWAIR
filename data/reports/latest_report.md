# LLM-CONTROL_LOWAIR Ubuntu 交付报告

生成时间：2026-08-16 16:59:51

## 1. 输入指令

飞到果园上方悬停两秒再降落

## 2. 地图与安全边界

- 地图文件：`data/maps/site_map.json`
- 地图名称：`demo_mountain_test_site`
- 坐标系：`local_meters`
- 可识别目标区域：果园、玉米地、水渠、起飞点
- 禁飞区：房屋、电线杆
- 飞行边界：x=[-6.0, 6.0], y=[-6.0, 6.0], z=[0.0, 3.0]

## 3. 动作校验

- 动作文件：`data/processed/instructions/map_last_actions.json`
- 校验结果：通过
- 需要人工确认：是

错误：

- 无

警告：

- 动作序列包含起飞、运动或模式切换，真机执行前必须人工确认

## 4. 动作序列与执行预览

| 步骤 | 动作 | 参数 | dry-run / pyparrot 预览 |
|---:|---|---|---|
| 1 | `pre_flight_check` | `{}` | `# check bluetooth, battery, area, manual confirmation` |
| 2 | `takeoff` | `{"duration_s": 5.0}` | `swing.safe_takeoff(5)` |
| 3 | `fly_left` | `{"duration_s": 0.5, "speed": 20.0}` | `swing.fly_direct(roll=-20, pitch=0, yaw=0, vertical_movement=0, duration=0.5)` |
| 4 | `fly_forward` | `{"duration_s": 3.0, "speed": 20.0}` | `swing.fly_direct(roll=0, pitch=20, yaw=0, vertical_movement=0, duration=3)` |
| 5 | `fly_right` | `{"duration_s": 0.5, "speed": 20.0}` | `swing.fly_direct(roll=20, pitch=0, yaw=0, vertical_movement=0, duration=0.5)` |
| 6 | `fly_forward` | `{"duration_s": 0.2, "speed": 20.0}` | `swing.fly_direct(roll=0, pitch=20, yaw=0, vertical_movement=0, duration=0.2)` |
| 7 | `fly_right` | `{"duration_s": 1.17, "speed": 20.0}` | `swing.fly_direct(roll=20, pitch=0, yaw=0, vertical_movement=0, duration=1.17)` |
| 8 | `fly_backward` | `{"duration_s": 0.2, "speed": 20.0}` | `swing.fly_direct(roll=0, pitch=-20, yaw=0, vertical_movement=0, duration=0.2)` |
| 9 | `fly_right` | `{"duration_s": 0.83, "speed": 20.0}` | `swing.fly_direct(roll=20, pitch=0, yaw=0, vertical_movement=0, duration=0.83)` |
| 10 | `hover` | `{"duration_s": 2.0}` | `swing.smart_sleep(2)` |
| 11 | `land` | `{"duration_s": 5.0}` | `swing.safe_land(5)` |

## 5. MATLAB/Simulink 仿真结果

- 仿真结论：`PASS`
- 总飞行时间：`18.400000000000002` 秒
- 末端位置：`[3, 2, 0]`

## 6. Ubuntu 可交付结论

Ubuntu 侧可完成中文指令解析、地图路径规划、动作安全校验、dry-run 预览、语音入口环境检查、日志与报告生成。MATLAB/Simulink GUI 实测建议在 Windows MATLAB 中完成，真机飞行作为可选安全验证。
