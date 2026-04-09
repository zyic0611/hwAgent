# 环卫业务分析小抄 (Business Logic)

## 1. 数据字典映射 (必须严格转换代码与含义)
* **ProjectType (项目类别)**: 1=清扫保洁, 2=环卫一体化, 3=垃圾收转运, 4=垃圾分类, 5=农村垃圾治理, 6=公厕管养, 7=中转站养护, 8=城市管家及大市政养护, 9=绿化养护, 10=水域保洁, 11=市容管理, 12=智能清扫, 13=餐厨垃圾, 14=第三方监管, 15=建筑垃圾, 16=垃圾处理, 17=环卫装备, 18=特许经营, 19=垃圾桶, 20=移动公厕, 21=垃圾车, 22=清洗车, 23=洒水车, 24=洗扫车, 25=压缩车, 26=抑尘车, 27=吸污车, 28=雾炮车, 29=扫路车, 30=厨余收运车, 31=雪车, 32=钩臂车, 33=垃圾分类设备, 34=垃圾箱(站), 35=其他环卫车。
* **EnterprisesType (企业性质)**: 1=国企, 2=民企, 3=国企物企, 4=民企物企。
* **ModeOfOperation (运作模式)**: 1=PPP, 2=特许经营, 3=其他。

## 2. 地域关联表 (Join Tables)
查询地名必须关联以下维度表获取名称：
* 省份：`JOIN t_rankprovice pr ON t_projectinfo.Provinces = pr.ProviceId` -> 过滤 `pr.ProviceName`
* 城市：`JOIN t_rankcity c ON t_projectinfo.City = c.CityId` -> 过滤 `c.CityName`
* 特别注意：北京、上海、天津、重庆（含“市”）必须关联 `t_rankprovice`（视为省份）。

## 3. 核心业务计算公式
* **合同总额补全**：若 `ContractsCanBe` 为空，计算公式为：`AnnualAmount * (CAST(LengthOfService AS SIGNED) + CAST(IFNULL(REPLACE(Month, '月', ''), 0) AS SIGNED) / 12.0)`。
* **预计到期时间**：使用 `DATE_ADD` 嵌套 `Date`、`LengthOfService` 年份和 `Month` 月份进行推算。

## 4. 高级分析场景 SQL 模板
* **打折率分析**：将 `ProjectStatus=1`（预算）与 `ProjectStatus=2`（中标）的项目按 `ProjectNo` 连接。
* **打折率过滤**：计算结果必须在 30% 到 110% 之间方为有效数据。
* **阵营分析**：1、3 为“国资阵营”；2、4 为“民营阵营”。