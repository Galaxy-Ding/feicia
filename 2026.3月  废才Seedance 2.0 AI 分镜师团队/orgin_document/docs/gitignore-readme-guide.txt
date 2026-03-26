Gitignore 说明

当前仓库已经改成以下策略：

- 默认忽略所有 .md 文档
- 仅保留文件名为 README.md 或 readme.md 的文档可被 Git 关注

对应规则已经写入根目录 .gitignore。

当前规则

*.md
**/*.md
!README.md
!readme.md
!**/README.md
!**/readme.md

含义：

- 所有目录下的 Markdown 文档默认忽略
- 只有文件名刚好是 README.md 或 readme.md 的文件不会被忽略

后续如何添加

如果你后面只想继续保留 README.md 这类文件，不需要再改规则，直接正常创建文件即可：

git add README.md

如果你想额外放开某一个 Markdown 文件，比如 docs/keep.md，就在 .gitignore 里追加一行：

!docs/keep.md

然后执行：

git add .gitignore docs/keep.md

如何输入命令

1. 检查某个文件是否被忽略

git check-ignore -v docs/action/01-requirements-report.md
git check-ignore -v README.md

2. 添加 README 文档

git add README.md
git add zeomeng/README.md

3. 添加 .gitignore 规则修改

git add .gitignore

已经被 Git 跟踪的旧文档怎么处理

注意：.gitignore 只对“还没有被 Git 跟踪”的文件生效。

如果某些 .md 文件以前已经提交过，即使现在写进 .gitignore，Git 还是会继续关注它们。

这时需要把这些旧文档从索引里移除，但保留本地文件：

git rm --cached -r -- ':(glob)**/*.md' ':(exclude,glob)**/README.md' ':(exclude,glob)**/readme.md'
git add .gitignore ':(glob)**/README.md' ':(glob)**/readme.md'

说明：

- git rm --cached 只取消 Git 跟踪，不会删除你本地文件
- 第二条命令会把 README 文档重新加入版本管理

推荐提交流程

git add .gitignore
git status
git commit -m "chore: ignore markdown files except readme"

如果你同时要处理“已经被跟踪的旧文档”，建议使用下面这一组：

git rm --cached -r -- ':(glob)**/*.md' ':(exclude,glob)**/README.md' ':(exclude,glob)**/readme.md'
git add .gitignore ':(glob)**/README.md' ':(glob)**/readme.md'
git status
git commit -m "chore: track readme files only"
