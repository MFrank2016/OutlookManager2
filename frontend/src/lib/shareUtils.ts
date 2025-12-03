/**
 * 分享相关工具函数
 */

/**
 * 获取分享页域名
 * 如果系统配置中设置了 share_domain，则使用该域名
 * 否则使用当前窗口的 origin
 */
export function getShareDomain(): string {
  // 在客户端运行时，尝试从 localStorage 或全局变量获取配置
  // 由于配置可能动态变化，这里先使用 window.location.origin
  // 实际使用时，可以通过 useConfigs hook 获取配置
  if (typeof window !== 'undefined') {
    // 尝试从 sessionStorage 获取（如果之前缓存过）
    const cachedDomain = sessionStorage.getItem('share_domain');
    if (cachedDomain) {
      return cachedDomain;
    }
  }
  return typeof window !== 'undefined' ? window.location.origin : '';
}

/**
 * 生成分享链接
 * @param token 分享token
 * @param customDomain 自定义域名（可选，如果提供则使用该域名）
 */
export function generateShareLink(token: string, customDomain?: string): string {
  const domain = customDomain || getShareDomain();
  // 确保域名以 http:// 或 https:// 开头
  const protocol = domain.startsWith('http://') || domain.startsWith('https://') 
    ? '' 
    : 'https://';
  return `${protocol}${domain}/shared/${token}`;
}

/**
 * 从系统配置中获取分享页域名
 * 这个函数需要在组件中使用 useConfigs hook 来获取配置
 * @param configs 系统配置列表
 */
export function getShareDomainFromConfigs(configs?: Array<{ key: string; value: string }>): string | null {
  if (!configs) return null;
  const shareDomainConfig = configs.find(config => config.key === 'share_domain');
  if (shareDomainConfig && shareDomainConfig.value) {
    return shareDomainConfig.value.trim();
  }
  return null;
}

