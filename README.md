# Support Conversation Datahub

把工单、聊天和邮件消息整理为可治理的会话数据产品。流水线对消息做统一字段处理、重复导入保护、PII 脱敏和会话级聚合，同时保留消息级事实表，便于以后接入知识库、检索和训练数据流程。

## 运行

```bash
PYTHONPATH=src python3 -m support_conversation.cli \
  --fixture fixtures/sample.json \
  --database /tmp/support-conversation-datahub.sqlite3
```

## 外部依赖类型与版本

- Python 3.11+
- SQLite 3.x
- pytest 8.3.x（测试）

脱敏规则只在本地处理示例数据，不使用真实账号、token、连接串或密钥。

## 验证

```bash
PYTHONPATH=src python3 -m pytest --import-mode=importlib tests
PYTHONPATH=src python3 -m compileall -q src
```
