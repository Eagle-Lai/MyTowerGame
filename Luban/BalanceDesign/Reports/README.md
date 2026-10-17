# 数值与参考证据入口

八档共 160 关、3200 波；匹配真实运行 168/168 条、离线运行 960/960 条。
真实五星严格认证 41/160 关；其余关卡保留离线参考和待验证标记。

`reference_index.json` 的 `preferredFiveStarReference` 优先指向同版本、完整操作的真实五星；否则明确使用离线预测。
`coverage.json` 分别记录静态计划、离线与真实覆盖；`all_waves_3200.json` 为逐波完整数据，各档另有 JSON、CSV、地图、资源清单与可读 Markdown。

|预设|真实五星关卡|真实有效低星关卡|离线有效低星关卡|
|---|---:|---:|---:|
|D01 非常容易|3/20|1/20|20/20|
|D02 容易|3/20|1/20|20/20|
|D03 中等偏下|3/20|1/20|20/20|
|D04 中等|20/20|9/20|20/20|
|D05 中等偏上|3/20|2/20|20/20|
|D06 困难|3/20|2/20|20/20|
|D07 非常困难|3/20|3/20|20/20|
|D08 极度困难|3/20|2/20|20/20|

## D04 正式预设逐关参考

|关卡|参考覆盖|星|战斗/Par|操作|
|---:|---|---:|---:|---|
|1|Unity PlayMode|5|0.815|[operations](References/D04/L01-270262c0ebe4f3dde953f8a829b0a272ffe4ebbeb9ff5b04226e593ecaa30561/reference-normal-130b797a36684730887ecc058b304414-operations.json)|
|2|Unity PlayMode|5|0.897|[operations](References/D04/L02-4156e930460f120948237b05f016a0f5b64b556445f55d9ea0ff4531325b22d4/reference-normal-fb95429b7553417cb71ae9cd1c59c918-operations.json)|
|3|Unity PlayMode|5|0.671|[operations](References/D04/L03-3e22a850722b74c4991980e6847ad78ba4b8e6c870a598d867fbacd2a177b328/reference-normal-6d071e779f6043d492aa7d4c6390deb1-operations.json)|
|4|Unity PlayMode|5|0.803|[operations](References/D04/L04-ce4797bb10c34185aa56760312c52dfc6ca21044beadd6423bc08a3ac0055b7f/reference-mixed-9776e77ab4ca4a31a996583a34d6b51d-operations.json)|
|5|Unity PlayMode|5|0.601|[operations](References/D04/L05-d303daecd59ebe1630f3b3c81e810b0074cb72dce9b54fd5092537dafee3afc1/mixed-c00bff783e8b48e7945aed0c258a6e6b-operations.json)|
|6|Unity PlayMode|5|0.964|[operations](References/D04/L06-125cad8dede42cacbf35a9fe58e6531f1e5606549b9dcd61a45991a60182daa8/power-9060bc5a2f1449768e4662d0048d94d5-operations.json)|
|7|Unity PlayMode|5|0.963|[operations](References/D04/L07-18991c70e70e8405a0b297bd0e89e17a1a8ffbea3b7189e515db3ad987938dc7/reference-normal-da8ef5d59c184ae38cd09abadf0273fe-operations.json)|
|8|Unity PlayMode|5|0.779|[operations](References/D04/L08-d00277d1fc0341f7580d03518a9acf76fbf0eb754e25e0b2f13782d1fa610b24/reference-normal-504f58b4820b43c6ae05e233c55c1310-operations.json)|
|9|Unity PlayMode|5|0.591|[operations](References/D04/L09-c2e8dfbadab50017a80b400da9674a0bb4fb978daa1e9b942fa90572bb2c846b/optimized-1-c1dfab6f6daf45388ca1ea33304f81cd-operations.json)|
|10|Unity PlayMode|5|0.763|[operations](References/D04/L10-0c6ab82a1bdf76517f2faa94824b3cd695925758131c0bfcf11d832790fb67b1/reference-normal-73d11c848b304318adb12656cd3eedef-operations.json)|
|11|Unity PlayMode|5|0.612|[operations](References/D04/L11-4eecd7fbe69057ad313723267aa01c8b9aab5dab5372f00471a89ff455b3292c/reference-normal-ceb78040a81e4539a28d496e5444ec89-operations.json)|
|12|Unity PlayMode|5|0.601|[operations](References/D04/L12-a74842a7277464932190e0bcbf7de31e1ab0be568cce48d90dcd4057cb32513f/optimized-1-c97ef54c29b74fc6b125ad0d482d2b98-operations.json)|
|13|Unity PlayMode|5|0.570|[operations](References/D04/L13-b169fa0a059025afbd2f4e06cd1189b396bed6a515a0b63d74fd945d420acb8e/optimized-1-30296caa5460487287dec2926ef8fd32-operations.json)|
|14|Unity PlayMode|5|0.601|[operations](References/D04/L14-fad69bec09f0a6ae6b8b158b76de1fbdd814ad4f185474861069ecfeff3f66c4/optimized-1-1ece77cd6f7f4a52aed245f3b0797eb3-operations.json)|
|15|Unity PlayMode|5|0.624|[operations](References/D04/L15-ae05c87d52937edacf3a9e1418f97719b6537745411a5efe619456a5dfeabcbd/reference-normal-fd6c3835f3e0468f8362e818cc00f578-operations.json)|
|16|Unity PlayMode|5|0.611|[operations](References/D04/L16-7c565be7a6eabf1645db98eccb47570e48e7973736f21b9b7cc60e8cfc72eb81/optimized-1-64a0fb8a683a46b1a94f9724c2400250-operations.json)|
|17|Unity PlayMode|5|0.612|[operations](References/D04/L17-f24351dc13f6ffba32e6df8875818475a8aa0a4247789434111f13b58c9925f9/reference-mixed-3ed4b08498ca4352a98e33c8460a02ca-operations.json)|
|18|Unity PlayMode|5|0.620|[operations](References/D04/L18-98c126a8504574c893c150c550efe7a5633598eb25d3c812452983fcfb154055/reference-normal-b059de1d23e542dbaf5a3af40aa35b68-operations.json)|
|19|Unity PlayMode|5|0.628|[operations](References/D04/L19-fe0fd45eea6ce92077ae07f9f8b077458d8d99f23ba27466b866a838645e872f/reference-mixed-b6d17e8d3d0940aea3cc248c087c9fde-operations.json)|
|20|Unity PlayMode|5|0.743|[operations](References/D04/L20-7a6ff581cd39795f167a137a80fa3196385d7ea18e07657805cfc7da4d0ae64c/reference-mixed-8d938a121be24c73ad1197e97f6d5118-operations.json)|

真实操作的来源 sidecar 保留原始结果文件、记录索引、runId、完整 hash、完成状态与资金等待策略。
未完成或被拒绝的操作轨迹仍留在原始证据中，但不能成为五星参考。离线完整结果和 1—4 星/失败对照位于 `../Simulation/`。
