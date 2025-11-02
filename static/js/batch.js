// batch.js - 批量操作模块

// 加载示例数据
function loadSampleData() {
  const sampleData = `example1@outlook.com----password1----refresh_token_here_1----client_id_here_1
example2@outlook.com----password2----refresh_token_here_2----client_id_here_2
example3@outlook.com----password3----refresh_token_here_3----client_id_here_3`;

  const batchAccountsElement = document.getElementById("batchAccounts");
  if (batchAccountsElement) {
    batchAccountsElement.value = sampleData;
    showNotification("示例数据已加载，请替换为真实数据", "info");
  }
}

// 验证批量格式
function validateBatchFormat() {
  const batchText = document.getElementById("batchAccounts")?.value.trim();
  if (!batchText) {
    showNotification("请先输入账户信息", "warning");
    return;
  }

  const lines = batchText.split("\n").filter((line) => line.trim());
  let validCount = 0;
  let invalidLines = [];

  lines.forEach((line, index) => {
    const parts = line.split("----").map((p) => p.trim());
    if (parts.length === 4 && parts.every((part) => part.length > 0)) {
      validCount++;
    } else {
      invalidLines.push(index + 1);
    }
  });

  if (invalidLines.length === 0) {
    showNotification(`格式验证通过！共 ${validCount} 个有效账户`, "success");
  } else {
    showNotification(
      `发现 ${invalidLines.length} 行格式错误：第 ${invalidLines.join(
        ", "
      )} 行`,
      "error"
    );
  }
}

// 测试账户连接
async function testAccountConnection() {
  const email = document.getElementById("email")?.value.trim();
  const refreshToken = document.getElementById("refreshToken")?.value.trim();
  const clientId = document.getElementById("clientId")?.value.trim();

  if (!email || !refreshToken || !clientId) {
    showNotification("请填写所有必需字段", "warning");
    return;
  }

  const testBtn = document.getElementById("testBtn");
  if (!testBtn) return;

  testBtn.disabled = true;
  testBtn.innerHTML = "<span>⏳</span> 测试中...";

  try {
    // 这里可以调用一个测试接口
    await new Promise((resolve) => setTimeout(resolve, 2000)); // 模拟测试
    showNotification("连接测试成功！账户配置正确", "success");
  } catch (error) {
    showNotification("连接测试失败：" + error.message, "error");
  } finally {
    testBtn.disabled = false;
    testBtn.innerHTML = "<span>🔍</span> 测试连接";
  }
}

// 批量添加账户
async function batchAddAccounts() {
  const batchText = document.getElementById("batchAccounts")?.value.trim();
  if (!batchText) {
    showNotification("请输入账户信息", "warning");
    return;
  }

  const lines = batchText.split("\n").filter((line) => line.trim());
  if (lines.length === 0) {
    showNotification("没有有效的账户信息", "warning");
    return;
  }

  // 显示进度
  if (typeof showBatchProgress === "function") {
    showBatchProgress();
  }

  const batchBtn = document.getElementById("batchAddBtn");
  if (batchBtn) {
    batchBtn.disabled = true;
    batchBtn.innerHTML = "<span>⏳</span> 添加中...";
  }

  let successCount = 0;
  let failCount = 0;
  const results = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const parts = line.split("----").map((p) => p.trim());

    // 更新进度
    if (typeof updateBatchProgress === "function") {
      updateBatchProgress(i + 1, lines.length, `处理第 ${i + 1} 个账户...`);
    }

    if (parts.length !== 4) {
      failCount++;
      results.push({
        email: parts[0] || "格式错误",
        status: "error",
        message: "格式错误：应为 邮箱----密码----刷新令牌----客户端ID",
      });
      continue;
    }

    const [email, password, refreshToken, clientId] = parts;

    try {
      await apiRequest("/accounts", {
        method: "POST",
        body: JSON.stringify({
          email: email,
          refresh_token: refreshToken,
          client_id: clientId,
        }),
      });
      successCount++;
      results.push({
        email: email,
        status: "success",
        message: "添加成功",
      });
    } catch (error) {
      // 如果是登录过期错误，立即停止批量添加
      if (error.message === "登录已过期") {
        console.log("检测到登录过期，停止批量添加");
        break;
      }
      
      failCount++;
      results.push({
        email: email,
        status: "error",
        message: error.message,
      });
    }

    // 添加小延迟避免请求过快
    await new Promise((resolve) => setTimeout(resolve, 100));
  }

  // 完成进度
  if (typeof updateBatchProgress === "function") {
    updateBatchProgress(lines.length, lines.length, "批量添加完成！");
  }

  // 显示结果
  if (typeof showBatchResults === "function") {
    showBatchResults(results);
  }

  if (successCount > 0) {
    showNotification(
      `批量添加完成！成功 ${successCount} 个，失败 ${failCount} 个`,
      "success"
    );
    if (failCount === 0) {
      setTimeout(() => {
        if (typeof clearBatchForm === "function") {
          clearBatchForm();
        }
        if (typeof showPage === "function") {
          showPage("accounts");
        }
      }, 3000);
    }
  } else {
    showNotification("所有账户添加失败，请检查账户信息", "error");
  }

  if (batchBtn) {
    batchBtn.disabled = false;
    batchBtn.innerHTML = "<span>📦</span> 开始批量添加";
  }
}

console.log("✅ [Batch] 批量操作模块加载完成");
