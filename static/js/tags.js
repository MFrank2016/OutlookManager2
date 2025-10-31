// tags.js - 标签管理模块

// 打开标签管理模态框
function editAccountTags(emailId, tags) {
    currentEditAccount = emailId;
    currentEditTags = Array.isArray(tags) ? [...tags] : [];
    
    // 更新模态框标题
    const modalHeader = document.querySelector('#tagsModal .modal-header h3');
    if (modalHeader) {
        modalHeader.textContent = `管理 ${emailId} 的标签`;
    }
    
    // 显示当前标签
    renderCurrentTags();
    
    // 显示模态框
    const modal = document.getElementById('tagsModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

// 渲染当前标签列表
function renderCurrentTags() {
    const tagsList = document.getElementById('currentTagsList');
    if (!tagsList) return;
    
    if (currentEditTags.length === 0) {
        tagsList.innerHTML = '<p class="text-muted">暂无标签</p>';
        return;
    }
    
    tagsList.innerHTML = currentEditTags.map(tag => `
        <div class="tag-item">
            <span class="tag-name">${tag}</span>
            <button class="tag-delete" onclick="removeTag('${tag}')">×</button>
        </div>
    `).join('');
}

// 添加新标签
function addTag() {
    const newTagInput = document.getElementById('newTag');
    if (!newTagInput) return;
    
    const newTag = newTagInput.value.trim();
    
    if (!newTag) {
        showNotification('标签名称不能为空', 'warning');
        return;
    }
    
    // 检查标签是否已存在
    if (currentEditTags.includes(newTag)) {
        showNotification('标签已存在', 'warning');
        return;
    }
    
    // 添加新标签
    currentEditTags.push(newTag);
    
    // 清空输入框
    newTagInput.value = '';
    
    // 重新渲染标签列表
    renderCurrentTags();
}

// 删除标签
function removeTag(tag) {
    currentEditTags = currentEditTags.filter(t => t !== tag);
    renderCurrentTags();
}

// 关闭标签管理模态框
function closeTagsModal() {
    const modal = document.getElementById('tagsModal');
    if (modal) {
        modal.style.display = 'none';
    }
    currentEditAccount = null;
    currentEditTags = [];
}

// 保存账户标签
async function saveAccountTags() {
    if (!currentEditAccount) {
        closeTagsModal();
        return;
    }
    
    try {
        const response = await apiRequest(`/accounts/${currentEditAccount}/tags`, {
            method: 'PUT',
            body: JSON.stringify({ tags: currentEditTags })
        });
        
        showSuccess('标签更新成功');
        closeTagsModal();
        
        // 重新加载账户列表
        if (typeof loadAccounts === 'function') {
            loadAccounts();
        }
    } catch (error) {
        showError('更新标签失败: ' + error.message);
    }
}

console.log('✅ [Tags] 标签管理模块加载完成');
