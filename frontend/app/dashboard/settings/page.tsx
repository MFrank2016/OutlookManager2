"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api-client";

export default function SettingsPage() {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    // 验证
    if (newPassword !== confirmPassword) {
      setError("两次输入的新密码不一致");
      return;
    }

    if (newPassword.length < 6) {
      setError("新密码长度至少为6位");
      return;
    }

    setLoading(true);

    try {
      await apiClient.changePassword(oldPassword, newPassword);
      setSuccess("密码修改成功！");
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "密码修改失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold text-gray-900">系统设置</h1>

      <div className="grid gap-6">
        {/* 密码修改 */}
        <div className="rounded-lg bg-white p-6 shadow-md">
          <h2 className="mb-4 text-xl font-semibold">修改密码</h2>

          <form onSubmit={handleChangePassword} className="max-w-md space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                当前密码
              </label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                required
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none"
                placeholder="请输入当前密码"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                新密码
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none"
                placeholder="请输入新密码（至少6位）"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                确认新密码
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none"
                placeholder="请再次输入新密码"
              />
            </div>

            {error && (
              <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}

            {success && (
              <div className="rounded-md bg-green-50 p-3 text-sm text-green-600">
                {success}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "修改中..." : "修改密码"}
            </button>
          </form>
        </div>

        {/* 系统信息 */}
        <div className="rounded-lg bg-white p-6 shadow-md">
          <h2 className="mb-4 text-xl font-semibold">系统信息</h2>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">系统版本</span>
              <span className="font-medium">v3.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">后端框架</span>
              <span className="font-medium">FastAPI</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">前端框架</span>
              <span className="font-medium">Next.js 14</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">数据库</span>
              <span className="font-medium">SQLite / PostgreSQL</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">架构模式</span>
              <span className="font-medium">洋葱架构 + DDD</span>
            </div>
          </div>
        </div>

        {/* API端点信息 */}
        <div className="rounded-lg bg-white p-6 shadow-md">
          <h2 className="mb-4 text-xl font-semibold">API端点</h2>

          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">后端API</span>
              <a
                href="http://localhost:8000/api/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                http://localhost:8000 📖
              </a>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">API文档 (Swagger)</span>
              <a
                href="http://localhost:8000/api/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                /api/docs
              </a>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">API文档 (ReDoc)</span>
              <a
                href="http://localhost:8000/api/redoc"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                /api/redoc
              </a>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">健康检查</span>
              <a
                href="http://localhost:8000/health"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                /health
              </a>
            </div>
          </div>
        </div>

        {/* 快速链接 */}
        <div className="rounded-lg bg-white p-6 shadow-md">
          <h2 className="mb-4 text-xl font-semibold">快速链接</h2>

          <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center rounded-md border border-gray-200 p-3 text-sm hover:bg-gray-50"
            >
              📚 项目文档
            </a>
            <a
              href="http://localhost:8000/api/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center rounded-md border border-gray-200 p-3 text-sm hover:bg-gray-50"
            >
              🔌 API文档
            </a>
            <a
              href="/"
              className="flex items-center justify-center rounded-md border border-gray-200 p-3 text-sm hover:bg-gray-50"
            >
              🏠 返回首页
            </a>
          </div>
        </div>

        {/* 帮助信息 */}
        <div className="rounded-lg bg-blue-50 p-6">
          <h3 className="mb-2 font-semibold text-blue-900">💡 使用提示</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li>• 定期修改密码以保证账户安全</li>
            <li>• 在"账户管理"中添加Outlook账户来管理邮件</li>
            <li>• 访问API文档了解所有可用接口</li>
            <li>• 遇到问题请查看后端日志或控制台输出</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

