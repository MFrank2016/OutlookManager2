// 发送邮件模块
let currentSendEmailId = null;
let quillEditor = null;

/**
 * 打开发送邮件模态框
 * @param {string} emailId - 发件人邮箱地址
 */
function openSendEmailModal(emailId) {
  currentSendEmailId = emailId;
  
  // 设置发件人地址
  const fromAddress = document.getElementById('sendEmailFromAddress');
  if (fromAddress) {
    fromAddress.textContent = emailId;
  }
  
  // 清空表单
  document.getElementById('sendEmailTo').value = '';
  document.getElementById('sendEmailSubject').value = '';
  
  // 初始化或清空编辑器
  if (!quillEditor) {
    initQuillEditor();
  } else {
    quillEditor.setContents([]);
  }
  
  // 显示模态框（使用 flex 确保居中）
  const modal = document.getElementById('sendEmailModal');
  if (modal) {
    modal.style.display = 'flex';
  }
}

/**
 * 关闭发送邮件模态框
 */
function closeSendEmailModal() {
  const modal = document.getElementById('sendEmailModal');
  if (modal) {
    modal.style.display = 'none';
  }
  
  // 清空数据
  currentSendEmailId = null;
  document.getElementById('sendEmailTo').value = '';
  document.getElementById('sendEmailSubject').value = '';
  if (quillEditor) {
    quillEditor.setContents([]);
  }
}

/**
 * 初始化Quill富文本编辑器
 */
function initQuillEditor() {
  const editorElement = document.getElementById('sendEmailEditor');
  if (!editorElement || quillEditor) {
    return;
  }
  
  quillEditor = new Quill('#sendEmailEditor', {
    theme: 'snow',
    modules: {
      toolbar: [
        [{ 'header': [1, 2, 3, false] }],
        ['bold', 'italic', 'underline', 'strike'],
        [{ 'color': [] }, { 'background': [] }],
        [{ 'list': 'ordered'}, { 'list': 'bullet' }],
        [{ 'indent': '-1'}, { 'indent': '+1' }],
        [{ 'align': [] }],
        ['link'],
        ['clean']
      ]
    },
    placeholder: '请输入邮件内容...'
  });
}

/**
 * 从模态框发送邮件
 */
async function sendEmailFromModal() {
  if (!currentSendEmailId) {
    showNotification('未指定发件人邮箱', 'error');
    return;
  }
  
  // 获取表单数据
  const to = document.getElementById('sendEmailTo').value.trim();
  const subject = document.getElementById('sendEmailSubject').value.trim();
  
  // 验证必填字段
  if (!to) {
    showNotification('请输入收件人邮箱地址', 'warning');
    document.getElementById('sendEmailTo').focus();
    return;
  }
  
  // 验证邮箱格式
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(to)) {
    showNotification('请输入有效的邮箱地址', 'warning');
    document.getElementById('sendEmailTo').focus();
    return;
  }
  
  if (!subject) {
    showNotification('请输入邮件主题', 'warning');
    document.getElementById('sendEmailSubject').focus();
    return;
  }
  
  // 获取编辑器内容
  if (!quillEditor) {
    showNotification('编辑器未初始化', 'error');
    return;
  }
  
  const htmlContent = quillEditor.root.innerHTML;
  const textContent = quillEditor.getText().trim();
  
  if (!textContent) {
    showNotification('请输入邮件内容', 'warning');
    quillEditor.focus();
    return;
  }
  
  // 禁用发送按钮
  const sendBtn = document.getElementById('sendEmailBtn');
  const originalBtnContent = sendBtn.innerHTML;
  sendBtn.disabled = true;
  sendBtn.innerHTML = '<span>⏳</span> 发送中...';
  
  try {
    showNotification('正在发送邮件，请稍候...', 'info');
    
    // 调用后端API
    const response = await apiRequest(`/emails/${currentSendEmailId}/send`, {
      method: 'POST',
      body: JSON.stringify({
        to: to,
        subject: subject,
        body_text: textContent,
        body_html: htmlContent
      })
    });
    
    if (response.success) {
      showSuccess('邮件发送成功！');
      closeSendEmailModal();
    } else {
      showNotification(`发送失败: ${response.message}`, 'error');
    }
  } catch (error) {
    // 检查是否是 Graph API 权限问题
    if (error.message && error.message.includes('Graph API')) {
      showNotification(
        `发送失败：该账户需要 Graph API 支持。<br><br>` +
        `请在账户列表中点击该账户的发送按钮，系统将引导您启用 Graph API。`,
        'error',
        8000
      );
    } else {
      showError('邮件发送失败: ' + error.message);
    }
  } finally {
    // 恢复发送按钮
    sendBtn.disabled = false;
    sendBtn.innerHTML = originalBtnContent;
  }
}

/**
 * 点击模态框外部关闭
 */
window.addEventListener('click', function(event) {
  const modal = document.getElementById('sendEmailModal');
  if (event.target === modal) {
    closeSendEmailModal();
  }
});

/**
 * ESC键关闭模态框
 */
document.addEventListener('keydown', function(event) {
  if (event.key === 'Escape') {
    const modal = document.getElementById('sendEmailModal');
    if (modal && (modal.style.display === 'flex' || modal.style.display === 'block')) {
      closeSendEmailModal();
    }
  }
});

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
  // 只检查 Quill 是否加载成功，不初始化编辑器
  // 编辑器会在打开模态框时才初始化
  setTimeout(() => {
    if (typeof Quill !== 'undefined') {
      console.log('✅ Quill富文本编辑器已就绪');
    } else {
      console.error('❌ Quill富文本编辑器加载失败');
    }
  }, 500);
});

