# MJ Video API 接口文档

## 📹 概述

MJ Video 接口用于图片生成视频内容，支持两种输入方式：通过 Base64 图片数组或在提示词中包含图片地址。该接口采用异步处理方式，需要轮询查询任务状态或使用回调通知获取结果。

**注意：当前仅支持快速模式（fast mode）**

## 🔗 接口信息

- **基础路径**: `/mj/submit/video`
- **HTTP 方法**: `POST`
- **认证方式**: Bearer Token
- **内容类型**: `application/json`

## 📋 请求参数

### 基础请求结构

```json
{
  "prompt": "string",           // 描述文本（必需）
  "base64Array": ["string"],   // Base64图片数组（方式1）
  "taskId": "string",          // 已有任务ID（方式2）
  "customId": "string",        // 自定义ID（可选）
  "botType": "string",         // 机器人类型（可选）
  "notifyHook": "string",      // 回调通知地址（可选）
  "index": 0,                  // 索引（可选）
  "state": "string",           // 状态（可选）
  "content": "string",         // 内容（可选）
  "maskBase64": "string"       // 遮罩Base64（可选）
}
```

### 参数说明

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| `prompt` | string | 必需 | 描述文本，可包含图片URL或纯文本描述 |
| `base64Array` | array | 方式1需要 | Base64编码的图片数组（与prompt中图片地址二选一） |
| `taskId` | string | 方式2需要 | 已有任务的ID，基于该任务生成视频 |
| `customId` | string | 可选 | 自定义标识符 |
| `botType` | string | 可选 | 机器人类型 |
| `notifyHook` | string | 可选 | 任务完成后的回调通知地址 |
| `index` | integer | 可选 | 索引值，默认为0 |
| `state` | string | 可选 | 任务状态 |
| `content` | string | 可选 | 附加内容 |
| `maskBase64` | string | 可选 | Base64编码的遮罩图片 |

### 输入方式

#### 方式1：Base64 图片数组 + 描述

```json
{
  "prompt": "一只可爱的小猫在花园里缓慢走动",
  "base64Array": [
    "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ...",
    "data:image/jpeg;base64,iVBORw0KGgoAAAANSUhEUgAA..."
  ],
  "notifyHook": "https://your-domain.com/mj/notify"
}
```

#### 方式2：Prompt 中包含图片地址

```json
{
  "prompt": "https://example.com/image.jpg 一只可爱的小猫在花园里缓慢走动",
  "notifyHook": "https://your-domain.com/mj/notify"
}
```

#### 方式3：基于已有任务生成视频

```json
{
  "taskId": "existing-task-id-12345",
  "prompt": "基于这张图片生成视频，小猫在花园里走动",
  "notifyHook": "https://your-domain.com/mj/notify"
}
```

## 📤 返回参数

### 提交响应

```json
{
  "code": 1,
  "description": "提交成功",
  "properties": null,
  "result": "task-id-12345"
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `code` | integer | 状态码（详见状态码说明） |
| `description` | string | 描述信息 |
| `properties` | object | 附加属性信息 |
| `result` | string | 任务ID，用于后续查询 |

### 状态码说明

| 状态码 | 说明 |
|--------|------|
| 1 | 提交成功 |
| 21 | 任务已存在（处理中或已完成） |
| 22 | 排队中 |
| 23 | 队列已满，请稍后重试 |
| 24 | 提示词包含敏感词 |
| 3 | 无可用实例账号 |
| 4 | 请求错误 |
| 5 | 未知错误 |

## 🔍 任务查询

### 查询任务状态

**接口路径**: `GET /mj/task/{task-id}/fetch`

**响应示例**:

```json
{
  "id": "task-id-12345",
  "action": "VIDEO",
  "prompt": "一只可爱的小猫在花园里玩耍",
  "promptEn": "A cute cat playing in the garden",
  "status": "SUCCESS",
  "progress": "100%",
  "submitTime": 1703123456789,
  "startTime": 1703123456800,
  "finishTime": 1703123466789,
  "imageUrl": "https://example.com/preview.jpg",
  "videoUrl": "https://example.com/video.mp4",
  "videoUrls": [
    {
      "url": "https://example.com/video1.mp4"
    },
    {
      "url": "https://example.com/video2.mp4"
    }
  ],
  "failReason": "",
  "description": "视频生成完成",
  "buttons": [],
  "properties": {
    "finalPrompt": "A cute cat playing in the garden",
    "finalZhPrompt": "一只可爱的小猫在花园里玩耍"
  }
}
```

## 🎯 使用示例

### 示例1：使用 Base64 图片生成视频

```bash
curl -X POST "https://api.example.com/mj/submit/video" \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一只优雅的天鹅在湖面上游泳，镜头缓慢移动",
    "base64Array": [
      "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..."
    ],
    "notifyHook": "https://your-domain.com/webhook/mj-notify"
  }'
```

### 示例2：使用图片URL生成视频

```bash
curl -X POST "https://api.example.com/mj/submit/video" \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "https://example.com/swan.jpg 天鹅在湖面上优雅游泳，波光粼粼",
    "notifyHook": "https://your-domain.com/webhook/mj-notify"
  }'
```

### 示例3：基于已有任务生成视频

```bash
curl -X POST "https://api.example.com/mj/submit/video" \
  -H "Authorization: Bearer your-api-token" \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "image-task-456",
    "prompt": "让这张图片动起来，添加自然的动态效果",
    "notifyHook": "https://your-domain.com/webhook/mj-notify"
  }'
```

### 示例4：查询任务状态

```bash
curl -X GET "https://api.example.com/mj/task/video-task-789/fetch" \
  -H "Authorization: Bearer your-api-token"
```

### 示例5：JavaScript 实现

```javascript
// 提交图片生成视频任务
async function submitImageToVideo(imageBase64, description) {
  const response = await fetch('/mj/submit/video', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt: description,
      base64Array: [imageBase64],
      notifyHook: 'https://your-domain.com/webhook'
    })
  });
  
  const result = await response.json();
  if (result.code === 1) {
    return result.result; // 返回任务ID
  } else {
    throw new Error(result.description);
  }
}

// 使用图片URL提交任务
async function submitUrlToVideo(imageUrl, description) {
  const response = await fetch('/mj/submit/video', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + token,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      prompt: `${imageUrl} ${description}`,
      notifyHook: 'https://your-domain.com/webhook'
    })
  });
  
  const result = await response.json();
  if (result.code === 1) {
    return result.result;
  } else {
    throw new Error(result.description);
  }
}

// 查询任务状态
async function getTaskStatus(taskId) {
  const response = await fetch(`/mj/task/${taskId}/fetch`, {
    headers: {
      'Authorization': 'Bearer ' + token
    }
  });
  
  return await response.json();
}

// 轮询等待任务完成
async function waitForVideoCompletion(taskId, maxWaitTime = 600000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < maxWaitTime) {
    const task = await getTaskStatus(taskId);
    
    if (task.status === 'SUCCESS') {
      return task.videoUrls || [{ url: task.videoUrl }];
    } else if (task.status === 'FAILURE') {
      throw new Error(task.failReason || '视频生成失败');
    }
    
    console.log(`任务进度: ${task.progress}, 状态: ${task.status}`);
    
    // 等待10秒后重试
    await new Promise(resolve => setTimeout(resolve, 10000));
  }
  
  throw new Error('任务超时');
}
```

## 💰 计费说明

### 模型计费

- **模型名称**: `mj_video_fast`
- **计费模式**: 快速模式（固定）
- **计费方式**: 按任务计费

### 计费规则

1. **所有视频生成任务**: 统一使用快速模式计费
2. **基于已有任务的视频生成**: 使用原始任务的模式进行计费
3. **失败任务**: 通常会退还配额（根据系统配置）

## 🔔 回调通知

### 回调地址配置

在请求中设置 `notifyHook` 参数，任务状态变更时会向该地址发送 POST 请求。

### 回调数据格式

```json
{
  "id": "task-id",
  "action": "VIDEO",
  "status": "SUCCESS",
  "progress": "100%",
  "videoUrl": "https://example.com/video.mp4",
  "videoUrls": [
    {
      "url": "https://example.com/video1.mp4"
    }
  ],
  "submitTime": 1703123456789,
  "startTime": 1703123456800,
  "finishTime": 1703123466789,
  "failReason": ""
}
```

## ⚠️ 注意事项

### 使用限制

1. **图片要求**: 必须提供图片输入（Base64数组或URL）
2. **描述必需**: prompt 参数必须包含对视频动作的描述
3. **异步处理**: 视频生成是异步任务，需要轮询查询或使用回调
4. **超时限制**: 任务超过1小时未完成会被标记为失败
5. **队列限制**: 系统有队列长度限制，高峰期可能需要等待

### 最佳实践

1. **图片质量**: 使用高质量、清晰的输入图片效果更好
2. **描述详细**: 提供具体的动作描述，如"缓慢移动"、"微风吹动"等
3. **设置回调**: 推荐使用 `notifyHook` 而非频繁轮询查询
4. **错误处理**: 根据状态码进行相应的错误处理
5. **重试机制**: 对于队列满（code 23）的情况，建议指数退避重试

### 常见错误

| 错误情况 | 解决方案 |
|----------|----------|
| 缺少图片输入 | 确保提供 base64Array 或 prompt 中包含图片URL |
| 图片格式不支持 | 使用 JPEG、PNG 等常见格式 |
| Base64 格式错误 | 确保包含正确的 data URI 前缀 |
| 队列已满 | 稍后重试或降低请求频率 |
| 敏感词检测 | 修改描述内容 |
| 任务超时 | 检查图片复杂度，考虑简化 |
| 无可用账号 | 联系管理员检查渠道状态 |

## 📊 任务状态流转

```
提交任务 → 队列等待 → 开始处理 → 生成中 → 完成/失败
   ↓         ↓         ↓        ↓        ↓
 code:1   code:22   progress   progress  SUCCESS/FAILURE
          排队中    0%-99%     100%      最终状态
```

## 🔧 开发工具

### Postman 集合

可以导入以下 Postman 集合进行接口测试：

```json
{
  "info": {
    "name": "MJ Video API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Submit Video Task (Base64)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{token}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"prompt\": \"一只可爱的小猫在花园里缓慢走动\",\n  \"base64Array\": [\"data:image/jpeg;base64,{{base64Image}}\"],\n  \"notifyHook\": \"https://your-domain.com/webhook\"\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/mj/submit/video",
          "host": ["{{baseUrl}}"],
          "path": ["mj", "submit", "video"]
        }
      }
    },
    {
      "name": "Submit Video Task (URL)",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{token}}"
          },
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"prompt\": \"{{imageUrl}} 一只可爱的小猫在花园里缓慢走动\",\n  \"notifyHook\": \"https://your-domain.com/webhook\"\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/mj/submit/video",
          "host": ["{{baseUrl}}"],
          "path": ["mj", "submit", "video"]
        }
      }
    },
    {
      "name": "Get Task Status",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{token}}"
          }
        ],
        "url": {
          "raw": "{{baseUrl}}/mj/task/{{taskId}}/fetch",
          "host": ["{{baseUrl}}"],
          "path": ["mj", "task", "{{taskId}}", "fetch"]
        }
      }
    }
  ]
}
```

---

**更新时间**: 2024年12月
**API 版本**: v1.0
**文档版本**: 1.1.0
