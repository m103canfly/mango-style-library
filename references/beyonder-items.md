# 配方：神秘道具（22 途径 + 泛神秘物件）

诡秘之主专属类别。用户说"出 X 途径的道具"或"随机出几件神秘道具"时按本文件走。图标配方结构同 props-ui.md（`one <物品> item icon` + 通用后缀），差别在**母题库**。所有 prompt 用英文。

## 目录

- 用法与随机生成规则
- 22 途径母题表
- 主序列完整示例（占卜家/学徒/偷盗者/观众）
- 泛神秘物件（封印物/魔药/符咒/仪式材料）
- 验收清单
- 修方

## 用法与随机生成规则

1. 从母题表取该途径 2-3 个母题组合成一件道具（如占卜家 = 灵摆 + 黄水晶 → `one citrine crystal pendulum on a silver chain`）
2. 配色按途径主色（表内），prompt 里写死
3. 神秘感靠**微发光**描述：`faintly glowing`、`subtle mystical shimmer`、`eerie light`——克制，不要糊满特效
4. "随机出 N 件"：跨途径随机选 N 个不同途径，各取 1-2 母题组合，逐张验收
5. 导出统一 `icon` 类别（32×32）

## 22 途径母题表

| 途径（起始序列） | 主色 | 视觉母题 |
|---|---|---|
| 愚者·占卜家 | 灰雾灰/黄水晶黄 | 灵摆、水晶球、塔罗牌、星象图、黄水晶 |
| 门·学徒 | 星光蓝/银 | 星光钥匙、青铜门、星轨罗盘、怀表 |
| 错误·偷盗者 | 鸦黑/暗金 | 黑手套、乌鸦羽、面具、沙漏 |
| 空想家·观众 | 竖瞳金/米白 | 金色竖瞳坠饰、银镜、心理记录本、怀表链 |
| 太阳·歌颂者 | 日金/白 | 太阳徽章、金杯、圣歌集、日冕杖 |
| 白塔·阅读者 | 书卷棕/靛蓝 | 厚典籍、羽毛笔、圆框眼镜、卷轴匣 |
| 暴君·水手 | 风暴蓝/铅灰 | 三叉戟坠、船锚、雷云纹章、海螺 |
| 倒吊人·秘祈人 | 暗紫/锁链银 | 倒十字、铁锁链、黑曜石、暗烛 |
| 黑暗·不眠者 | 夜黑/月白 | 月牙坠、黑纱、静谧花、夜烛 |
| 死神·收尸人 | 骨白/冥黑 | 白骨指环、黑棺钉、引魂灯、裹尸布扣 |
| 黄昏巨人·战士 | 晨曦橙/铁灰 | 巨剑、纹章盾、晨光石、铁护腕 |
| 红祭司·猎人 | 焰红/铁黑 | 火焰纹章、长枪、猎刀、军徽 |
| 魔女·刺客 | 黑玫瑰红/镜银 | 淬毒匕首、黑玫瑰、手镜、蛛丝坠 |
| 母亲·耕种者 | 麦金/沃土棕 | 麦穗束、丰饶角、种子袋、大地石 |
| 月亮·药师 | 绯红/药绿 | 药瓶组、绯红月坠、草药包、研钵 |
| 黑皇帝·律师 | 黑金/深紫 | 天平坠、法典、黑金权戒、规则卷轴 |
| 审判者·仲裁人 | 银白/铁灰 | 审判之剑、天平、铁徽章、锁链卷 |
| 被缚者·囚犯 | 镣铐灰/怨绿 | 镣铐、怨灵面具、缚灵索、灰雾珠 |
| 深渊·罪犯 | 血赤/黑焰 | 恶魔角坠、血石、黑焰灯、骨刃 |
| 隐者·窥秘人 | 隐秘紫/星银 | 全视之眼坠、星象仪、秘卷、隐纹杖 |
| 完美者·通识者 | 齿轮铜/蒸汽白 | 精密齿轮组、蒸汽阀、蓝图卷、黄铜目镜 |
| 命运之轮·怪物 | 命运银/黯青 | 骰子、衔尾蛇环、轮盘坠、命运线轴 |

## 主序列完整示例

- 占卜家（愚者途径）：`one citrine crystal pendulum item icon, golden-yellow crystal on a delicate silver chain, faintly glowing, mystical shimmer`
- 占卜家备选：`one crystal ball item icon, swirling grey mist inside, brass stand with star engravings, faintly glowing`
- 学徒（门途径）：`one starlight bronze key item icon, cosmic blue glow in the key head, tiny star trail sparks`
- 偷盗者（错误途径）：`one black leather glove item icon with a raven feather, dark gold trim, eerie subtle shimmer`
- 观众（空想家途径）：`one golden pendant item icon with a vertical pupil gem, milky gold glow, hypnotic spiral engraving`

## 泛神秘物件（封印物/魔药/符咒/仪式材料）

- 封印物：`one sealed artifact container, dark brass box with engraved chains and a wax seal marked '<编号>', ominous faint glow from the seams`
- 魔药：`one small potion vial with <途径主色> bubbling liquid, cork stopper, faint glow`
- 符咒：`one engraved metal charm tablet, <途径主色> runes on dark iron, subtle shimmer`
- 仪式材料：`one black ritual candle with silver runes`、`one silver ritual dagger with a wavy blade`、`one small dish of blessed salt`
- 通用规则：封印物/符咒要编号或符文时**不要写文字**，用 `engravings / runes / markings` 描述纹理，文字进引擎叠

## 验收清单

- [ ] 母题与途径表一致（观众不出三叉戟这类错配即串途径，重跑）
- [ ] 途径主色命中
- [ ] 发光克制（微光，不是满屏特效）
- [ ] 图标居中、透明底、32×32 导出后仍一眼可辨
- [ ] 无 AI 乱写的文字/符文串（符文应是抽象纹理）

## 修方

- **特效糊满**：删 `glowing aura`，只留 `faintly glowing <部位>`
- **道具像现代物品**：补 `Victorian era, mystical, handcrafted`
- **随机批量风格漂移**：同批共用 approved props/UI Gold Anchor，固定途径主色用 `--special beyonder` 显式登记；地区 Scene Bible 只能补充地域材质
