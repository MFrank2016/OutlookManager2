// apidocs.js - API文档模块

// 加载 API 文档页面时初始化
async function initApiDocs() {
  // 这里可以添加 API 文档的初始化逻辑
  console.log("API 文档页面已初始化");
}

// 复制代码示例到剪贴板
function copyCodeExample(button) {
  const codeBlock = button.parentElement.querySelector("code, pre");
  if (!codeBlock) return;

  const code = codeBlock.textContent;

  if (navigator.clipboard) {
    navigator.clipboard
      .writeText(code)
      .then(() => {
        showNotification("代码已复制到剪贴板", "success");
        // 临时改变按钮文本
        const originalText = button.textContent;
        button.textContent = "✓ 已复制";
        setTimeout(() => {
          button.textContent = originalText;
        }, 2000);
      })
      .catch(() => {
        fallbackCopyCode(code, button);
      });
  } else {
    fallbackCopyCode(code, button);
  }
}

// 后备复制方法
function fallbackCopyCode(text, button) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.left = "-999999px";
  document.body.appendChild(textArea);
  textArea.select();
  try {
    document.execCommand("copy");
    showNotification("代码已复制到剪贴板", "success");
    // 临时改变按钮文本
    const originalText = button.textContent;
    button.textContent = "✓ 已复制";
    setTimeout(() => {
      button.textContent = originalText;
    }, 2000);
  } catch (err) {
    showNotification("复制失败，请手动复制", "error");
  }
  document.body.removeChild(textArea);
}

// 展开/折叠 API 接口详情
function toggleApiSection(element) {
  const section = element.closest(".api-section");
  if (!section) return;

  const content = section.querySelector(".api-section-content");
  if (!content) return;

  const isExpanded = content.style.display !== "none";
  content.style.display = isExpanded ? "none" : "block";

  // 切换展开图标
  const icon = element.querySelector(".toggle-icon");
  if (icon) {
    icon.textContent = isExpanded ? "▶" : "▼";
  }
}

// 搜索 API 文档
function searchApiDocs() {
  const searchInput = document.getElementById("apiDocsSearch");
  if (!searchInput) return;

  const searchTerm = searchInput.value.toLowerCase();
  const apiSections = document.querySelectorAll(".api-section");

  apiSections.forEach((section) => {
    const title =
      section.querySelector(".api-section-title")?.textContent.toLowerCase() ||
      "";
    const content =
      section
        .querySelector(".api-section-content")
        ?.textContent.toLowerCase() || "";

    if (title.includes(searchTerm) || content.includes(searchTerm)) {
      section.style.display = "block";
    } else {
      section.style.display = "none";
    }
  });
}

// 跳转到指定的 API 部分（用于目录导航）
function scrollToApiSection(sectionId) {
  const section = document.getElementById(sectionId);
  if (section) {
    section.scrollIntoView({ behavior: "smooth", block: "start" });

    // 高亮显示该部分
    section.style.backgroundColor = "#fff3cd";
    setTimeout(() => {
      section.style.backgroundColor = "";
    }, 2000);
  }
}

// 生成 API 文档目录
function generateApiDocsToc() {
  const tocContainer = document.getElementById("apiDocsToc");
  if (!tocContainer) return;

  const sections = document.querySelectorAll(".api-section");
  let tocHtml = '<ul class="api-docs-toc">';

  sections.forEach((section, index) => {
    const title =
      section.querySelector(".api-section-title")?.textContent ||
      `Section ${index + 1}`;
    const sectionId = section.id || `section-${index}`;
    section.id = sectionId; // 确保每个section都有ID

    tocHtml += `<li><a href="#${sectionId}" onclick="scrollToApiSection('${sectionId}'); return false;">${title}</a></li>`;
  });

  tocHtml += "</ul>";
  tocContainer.innerHTML = tocHtml;
}

console.log("✅ [API Docs] API文档模块加载完成");
