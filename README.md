# scoop-bucket

[Scoop](https://scoop.sh/) 包源，托管 harrisonwang 名下工具的 Windows manifest。

## 使用

```powershell
scoop bucket add harrisonwang https://github.com/harrisonwang/scoop-bucket
scoop install pith
```

后续升级：

```powershell
scoop update pith
```

## 已收录

| 工具 | 上游 |
| --- | --- |
| pith | [harrisonwang/pith](https://github.com/harrisonwang/pith) |

## 更新机制

源仓库打 tag 后通过 `repository_dispatch: tool-released` 通知本仓库，工作流从源仓库 checkout `.github/scoop/<tool>.json.tmpl` 模板，结合 `SHA256SUMS.txt` 渲染成 `bucket/<tool>.json` 并自动提交。

也可在 Actions 页手动触发 `update-manifest`，传 `tool` / `tag` / `repo` 三个参数复跑。
