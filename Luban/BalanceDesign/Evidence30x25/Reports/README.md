# 数值与参考证据入口

八档共 240 关、6000 波；匹配真实运行 114/114 条、离线运行 1222/1222 条。
真实五星严格认证 58/240 关；其余关卡保留离线参考和待验证标记。

`reference_index.json` 的 `preferredFiveStarReference` 优先指向同版本、完整操作的真实五星；否则明确使用离线预测。
`coverage.json` 分别记录静态计划、离线与真实覆盖；all_waves 文件为逐波完整数据，各档另有 JSON、CSV、地图、资源清单与可读 Markdown。

|预设|真实五星关卡|真实有效低星关卡|离线有效低星关卡|
|---|---:|---:|---:|
|D01 非常容易|4/30|0/30|8/30|
|D02 容易|4/30|0/30|10/30|
|D03 中等偏下|4/30|0/30|16/30|
|D04 中等|30/30|2/30|30/30|
|D05 中等偏上|4/30|0/30|19/30|
|D06 困难|4/30|0/30|24/30|
|D07 非常困难|4/30|0/30|25/30|
|D08 极度困难|4/30|0/30|21/30|

## D04 正式预设逐关参考

|关卡|参考覆盖|星|战斗/Par|操作|
|---:|---|---:|---:|---|
|1|Unity PlayMode|5|0.758|[operations](References/D04/L01-71cfb240594186b951d9575a98a53788d0e8c9c98d363f19694032be34b0318d/low-finite-best-4c218179210742ae9a42c4387c730afb-operations.json)|
|2|Unity PlayMode|5|0.941|[operations](References/D04/L02-68939f5111b46bf6c26fc167c45659ca90f2c8346ee9c5dc45a03a463a621dbd/maze-8883f5558ac4493ba13daa181d58e557-operations.json)|
|3|Unity PlayMode|5|0.938|[operations](References/D04/L03-9092ec7746dd7912687719e49cf32fa5dbdcd519d0560722e0a6a60b8f9c80f1/maze-1aa2c9f3f51748e7b8f598ab49d5074d-operations.json)|
|4|Unity PlayMode|5|0.942|[operations](References/D04/L04-7af491d308eb68238a32b60e132e3008d1c2cca7f68648a634483b345db2ccfb/maze-160604327c254385be7a6785c22bec8d-operations.json)|
|5|Unity PlayMode|5|0.943|[operations](References/D04/L05-397b54d3e1fce770fb3b03909727c9fe4cd14dd3563bb5c44cfad25352d45a6f/maze-f4dcc8e683a1497d8c02535009c80c05-operations.json)|
|6|Unity PlayMode|5|0.941|[operations](References/D04/L06-8b226230de1a341237298e0a1d83318abdb1914397d036fcff072499d6c796d1/maze-64503b9a5ce04d8baa6605cbf3ed5448-operations.json)|
|7|Unity PlayMode|5|0.793|[operations](References/D04/L07-cbc8cc3beb0cc9bd4ee77e007a81f47f8dd4d916b70d5ee582cf7fc32d6a20dc/low-finite-best-877e898e3bb64b05bf92f4d2c6b090cd-operations.json)|
|8|Unity PlayMode|5|0.940|[operations](References/D04/L08-f5c3c69eeab80619bb094e92a15b1a21bea2d282597045b5129f1cd4f1a19246/maze-7ba4208d67ac4d858d11bc297f553b0c-operations.json)|
|9|Unity PlayMode|5|0.943|[operations](References/D04/L09-14e5aab5c08db2dff25c5547c49ff200c91abe45560addf6f1af1ab6a0d236b0/maze-615e3386dd8543438837d64ff0c1c84a-operations.json)|
|10|Unity PlayMode|5|0.785|[operations](References/D04/L10-8d07b1b872860bd31d90bdb132d5467a2b28b2557425bbae294dea9cd49025d0/low-finite-best-cd8579da3a1a4ce68b0007e9fa47ae64-operations.json)|
|11|Unity PlayMode|5|0.941|[operations](References/D04/L11-88c1efbee1727105b307488043ac6afdda78944ec3dec582e6c801160db0e498/maze-c91449720d624f17a80035231fc2c116-operations.json)|
|12|Unity PlayMode|5|0.942|[operations](References/D04/L12-296710daa3cc802caa294f550117ed0e44bdb1b41cb2094d8f8b88f4cab21e39/maze-886edbc03c8a41d4a492d3ea8aaf78d6-operations.json)|
|13|Unity PlayMode|5|0.942|[operations](References/D04/L13-434b7dcf79b7ce0b434a7359661c06153ed9a84bec557a59e8361c54a29958d3/maze-58473501138a43e5bba7e936b0f23a5b-operations.json)|
|14|Unity PlayMode|5|0.943|[operations](References/D04/L14-03351d469611a5c205ed79b310a18b114becba0064af80a8733b83cb4450a78a/maze-eb54c9ebda3f4f27ba153ff6a284d906-operations.json)|
|15|Unity PlayMode|5|0.940|[operations](References/D04/L15-63a857af4df7d34857698976e11398bf900064ffc445a1c9a78b2e02fabdf42d/maze-a7ebd369e7134b238b84912868d30242-operations.json)|
|16|Unity PlayMode|5|0.940|[operations](References/D04/L16-60e317a75fe77525be21fa0606236dc4b7d54ba0ce5a551a2dc5663d33b439d2/maze-ba1342079ef74350a97d3dcbf46c4de0-operations.json)|
|17|Unity PlayMode|5|0.942|[operations](References/D04/L17-f75eb61bf5823e5fce625900b13cc91e4c23d01de38bf7c3fac185b6634bef43/maze-44f4de489c6942cc8146ca3e65d62b9e-operations.json)|
|18|Unity PlayMode|5|0.940|[operations](References/D04/L18-ef560680f9a0a8f55ecc28bc146521ea26c804f54714c59a9781008ee8e169ad/maze-515f1aa4b74d4a938f89a27baf0e7802-operations.json)|
|19|Unity PlayMode|5|0.943|[operations](References/D04/L19-cb1a11696bfea4ffc1dd756b0fe4bd5fd569a1b3f16cc298853b66982728467d/maze-844eaad985a844ec9305f9a865532f05-operations.json)|
|20|Unity PlayMode|5|0.817|[operations](References/D04/L20-0c675a9ce5dc120e6bd33000d1c651c4daa1808b622d531009823e080026d486/low-finite-best-5475ea83d12a487a8e3ceabee0569340-operations.json)|
|21|Unity PlayMode|5|0.943|[operations](References/D04/L21-ea647c48e1b0651e410f9119c7194642658f5612b975beefa184a4d371863056/maze-0c655475937e453ba5caba5c81d0e572-operations.json)|
|22|Unity PlayMode|5|0.942|[operations](References/D04/L22-b12a871f1b79ee4a6617392b549a42e922236864ae301624f5f584af70f48307/maze-e7548cc488f64b819a2b7d2bf8d969a0-operations.json)|
|23|Unity PlayMode|5|0.941|[operations](References/D04/L23-6e253ef51fa7a5e89a0264d25f7796f048dc9d9b4bb5d24c92063a588dc15a13/maze-aab42c77472245e7a85b551d974a9379-operations.json)|
|24|Unity PlayMode|5|0.941|[operations](References/D04/L24-59746fa126bb8c263debf2d606f165c08a5d84e9fc0d25b1e4a4adcf9961aa0d/maze-5a41b923cf5d4f18bae1f4bf70d86ae6-operations.json)|
|25|Unity PlayMode|5|0.942|[operations](References/D04/L25-8261d4fb66cd05674bd376242184594da3ebf3a5f0b1832d75c6f61420b3e2f2/maze-58237ec7a4c440dda99343d713a036ff-operations.json)|
|26|Unity PlayMode|5|0.943|[operations](References/D04/L26-53d4580491569c01da7231510f2a363604b83bfa5626b0c81683ec29eed53262/maze-f3431b9b92df4f68843fb21d7ed64674-operations.json)|
|27|Unity PlayMode|5|0.942|[operations](References/D04/L27-ac0976c466e0468476646c0c040fc39aea8e925e4c060a01b9ff935fd5d6806e/maze-425bf47fe37647219ea4436ab17881d3-operations.json)|
|28|Unity PlayMode|5|0.942|[operations](References/D04/L28-6623107cce4b851ef1637dd53dcc0fc22ad0f01569aaa4833f0a2b253a8baa33/maze-1600abdcffe54fe7a75401d12b70b526-operations.json)|
|29|Unity PlayMode|5|0.941|[operations](References/D04/L29-5d730736393ac3f1e1fd0be0f47fbe0b4467ed3c7da1a6a15ea9cfaef1390f73/maze-a82edde3f56d4a90bb4d6540a852a891-operations.json)|
|30|Unity PlayMode|5|0.850|[operations](References/D04/L30-5bb2b1d681acba6f9a7dca608c85c9142120975e39eb8755b4cbb81927a96c56/low-finite-best-ee6ba6f310164e82b7d2fb2a3b1464e4-operations.json)|

真实操作的来源 sidecar 保留原始结果文件、记录索引、runId、完整 hash、完成状态与资金等待策略。
未完成或被拒绝的操作轨迹仍留在原始证据中，但不能成为五星参考。离线完整结果和 1—4 星/失败对照位于 `../Simulation/`。
