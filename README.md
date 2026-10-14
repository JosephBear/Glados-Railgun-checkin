# Glados自动签到

## 食用方式：

### 注册一个GLaDOS的账号([注册地址](https://glados.space/landing/0A58E-NV28S-6U3QV-33VMG))

#### 我的邀请码：([0A58E-NV28S-6U3QV-33VMG](https://0a58e-nv28s-6u3qv-33vmg.glados.space)) 

#### 我的优惠码（9折）：([DEVILSTORE](https://0a58e-nv28s-6u3qv-33vmg.glados.space)) 

### **Fork**本仓库

![图片加载失败](imgs/1.png)

### 添加**secret**

1. 跳转至自己的仓库的`Settings`->`Secrets and variables`->`Action`

2. 添加1个`repository secret`，命名为`GLADOS_COOKIES`，其值对应GLaDOS账号的cookie值中的有效部分（获取方式如下）

- 在GLaDOS的签到页面按`F12`

- 切换到`Network`页面下，刷新

![图片加载失败](imgs/2.png)

- 选择当前已登录网站的 `/api/user/status` 等账户请求，在 `Request Headers` 下找到 `Cookie`，复制它的值（不包含 `Cookie:` 字段名）

  > 参考格式：koa:sess=eyJ1c2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxAwMH0=; koa:sess.sig=xJkOxxxxxxxxxxxxxxxtnM;

![图片加载失败](imgs/3.png)

- 多账号请在 `GLADOS_COOKIES` 中添加多个 Cookie，中间使用 `&` 连接。（例如：`c1&c2&c3`）单个账号直接填写完整 Cookie 值。

3. 配置积分兑换策略（非必须，默认关闭自动兑换）

- 默认只签到，不兑换积分。已有的 `GLADOS_EXCHANGE_PLAN` 不会自动开启兑换。
- 确认需要自动兑换后，在仓库 `Settings` → `Secrets and variables` → `Actions` → `Variables` 添加变量 `GLADOS_AUTO_EXCHANGE`，值设为 `true`。删除该变量或改为 `false` 可关闭。
- 只有当前域名签到成功（或当天已签到）且积分达到要求时，才会尝试兑换。

- 添加1个`repository secret`，命名为`GLADOS_EXCHANGE_PLAN`，配置自动兑换积分策略：

| 值 | 积分要求 | 兑换天数 |
|---|---------|---------|
| `plan100` | 100 积分 | 10 天 |
| `plan200` | 200 积分 | 30 天 |
| `plan500` | 500 积分 | 100 天 (默认) |

> 开启自动兑换后，不配置兑换策略时使用 `plan500`，即积分达到 500 时兑换 100 天。

4. 手机推送（非必须）

- 添加1个`repository secret`，命名为`PUSHDEER_SENDKEY`，其值对应 PushDeer key: ([获取地址](https://www.pushdeer.com/product.html))。

### **star**自己的仓库

![图片加载失败](imgs/4.png)

## 文件结构

```shell
│  checkin.py	# 签到脚本
│
├─.github
│  └─workflows
│          gladosCheck.yml	# Actions 配置文件
```

## 更新日志

- **2026-01**: 重构代码，添加log输出方便定位，支持新版网址，支持配置积分兑换策略。
- **2026-04**: 优化代码逻辑，优化日志输出，支持[新版域名](https://railgun.info) ，在 GLADOS_COOKIES 中添加新版域名下的 cookies 即可使用。


## 问题排查与定位
- 定时签到按 UTC `04:00`、`10:00` 执行，对应北京时间 `12:00`、`18:00`；GitHub 调度可能延迟。也可在 Actions → `auto check` 中手动运行。
- 提交到 `master` 和 Pull Request 仅运行 `Offline tests`，不会触发真实签到或读取账号 Cookie。
- 每个 Cookie 只要在一个支持域名签到成功或已签到，就视为该账号成功。如果任一 Cookie 在所有域名都失败，或 Cookie 未设置，脚本会以非零退出码让 Actions 正确标红。
- 日志出现 `没有权限` / `No permission` 时，请重新登录实际使用的网站，并在浏览器 Network → Request Headers 中复制新的 Cookie 值，更新仓库 Secret `GLADOS_COOKIES`。不要在 Issue、日志或聊天中公开 Cookie。
- 如需手机推送，仍需自行配置 `PUSHDEER_SENDKEY`；未配置时不会发送推送。
- 大家可以通过查询 actions 中的 running checkin 日志快速定位问题，有其他问题提交issue。

  <img width="1684" height="844" alt="image" src="https://github.com/user-attachments/assets/45348a5f-43e4-45f5-8fdf-ce84d343b30d" />

## 离线测试

```shell
python -m pip install requests pypushdeer PyYAML
python -m unittest discover -s tests -v
```

测试使用模拟 HTTP 响应和虚构 Cookie，不需要 Secrets，也不会访问签到服务。

## 声明

本项目不保证稳定运行与更新, 因GitHub相关规定可能会删库, 请注意备份








