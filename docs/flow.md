# MusicPilot 研发流程规范

## 🎯 开发流程

### 1. 需求分析
- 新功能或问题 → 创建 GitHub Issue
- 明确功能描述、验收标准、依赖关系
- 指定优先级和里程碑

### 2. 分支策略
- **main**: 生产稳定分支
- **develop**: 开发集成分支
- **feature/xxx**: 新功能分支 (从 develop 创建)
- **fix/xxx**: 问题修复分支 (从 develop 创建)
- **release/x.y.z**: 发布准备分支

### 3. 开发流程
```
1. 从 develop 创建功能分支
   git checkout -b feature/your-feature develop

2. 开发并提交代码
   git commit -m "feat: 添加音乐文件扫描功能"

3. 推送到远程
   git push origin feature/your-feature

4. 创建 Pull Request (PR)
   - 填写 PR 模板
   - 关联相关 Issue
   - 等待代码审查

5. CI/CD 自动运行测试
   - Lint 检查
   - 单元测试
   - 构建验证

6. 审查通过后合并到 develop
```

### 4. 发布流程
```
1. 从 develop 创建 release 分支
   git checkout -b release/v1.0.0 develop

2. 版本号更新 (version bump)
   - 更新 package.json
   - 更新 requirements.txt 版本

3. 合并到 main 并打标签
   git checkout main
   git merge release/v1.0.0
   git tag v1.0.0

4. 部署到生产环境

5. 回合并到 develop
   git checkout develop
   git merge release/v1.0.0
```

---

## 📝 代码提交规范 (Conventional Commits)

### 格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整（不影响逻辑）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具链相关

### 示例
```
feat(backend): 添加 MusicBrainz API 集成

- 实现艺术家信息查询
- 实现专辑信息查询
- 添加缓存机制优化性能

Closes #42
```

---

## ✅ 代码审查要求

### 审查清单
- [ ] 代码符合项目规范
- [ ] 功能完整且符合需求
- [ ] 单元测试覆盖率达标 (≥80%)
- [ ] 没有引入新的警告或错误
- [ ] 文档已更新
- [ ] 没有敏感信息泄露

### 审查流程
1. 开发者提交 PR
2. 至少一人审查
3. 提出修改意见或批准
4. 修改后重新审查（如需要）
5. 合并到目标分支

---

## 🧪 测试要求

### 单元测试
- 后端核心业务逻辑 ≥ 80% 覆盖率
- 前端关键组件和工具函数

### 集成测试
- API 接口测试
- 数据库操作测试
- 外部服务集成测试

### E2E 测试
- 关键用户路径覆盖
- 登录/注销
- 音乐库操作
- 播放器功能

---

## 🚀 CI/CD 流水线

### 触发条件
- 推送代码到任意分支 → 运行 lint 和单元测试
- 创建/更新 PR → 运行完整测试套件
- 合并到 main → 构建并部署

### 流水线步骤
1. **Backend Lint**: Ruff + Black 检查
2. **Backend Test**: pytest + 覆盖率报告
3. **Frontend Lint**: ESLint + Prettier
4. **Frontend Test**: Vitest 单元测试
5. **Build**: 构建 Docker 镜像
6. **Deploy**: 部署到目标环境（仅 main 分支）

---

## 📚 文档要求

### 必需文档
- **README.md**: 项目介绍和快速开始
- **EVOLUTION.md**: 项目进化追踪
- **docs/tasks.md**: 任务清单
- **docs/development.md**: 开发环境搭建
- **docs/api.md**: API 文档（自动生成）

### 代码注释
- 公共函数和类必须有文档字符串
- 复杂逻辑必须添加注释说明
- TODO/FIXME/HACK 标签需要说明原因

---

## 🔄 迭代节奏

### Sprint 周期
- 2 周为一个 Sprint
- 每次迭代包含：开发 + 测试 + 部署

### 每日站会 (异步)
- 在 EVOLUTION.md 更新当日进展
- 遇到阻塞立即标注

---

## 🎨 代码风格

### Python (Backend)
- 使用 Black 格式化
- 使用 Ruff 进行 Lint
- 遵循 PEP 8 规范

### JavaScript/TypeScript (Frontend)
- 使用 Prettier 格式化
- 使用 ESLint 进行 Lint
- 使用 Vue 3 Composition API

---

## 🐛 问题处理

### Bug 严重级别
- **P0**: 阻塞性问题，立即修复
- **P1**: 高优先级，24小时内修复
- **P2**: 中优先级，当前 Sprint 修复
- **P3**: 低优先级，排期修复

### Bug 处理流程
1. 创建 GitHub Issue (label: bug)
2. 指定优先级和负责人
3. 创建 fix/* 分支修复
4. 提交 PR 并关联 Issue
5. 合并后关闭 Issue

---

## 🔒 安全规范

### 敏感信息
- 绝不提交 API Key、数据库密码等
- 使用环境变量管理配置
- `.env` 文件加入 .gitignore

### 代码安全
- 用户输入必须验证和过滤
- SQL 查询使用参数化
- API 接口实现认证和授权

---

## 📦 依赖管理

### Python 依赖
- 在 `backend/requirements.txt` 中声明
- 定期更新依赖版本
- 使用 pip-tools 锁定版本（推荐）

### Node 依赖
- 在 `frontend/package.json` 中声明
- 使用 npm ci 安装（CI 环境）
- 定期运行 `npm audit` 检查安全漏洞